"""
Comprehensive Audit Logging System for DT-RAG v1.8.1
Implements immutable audit trails with integrity verification
Compliant with GDPR Article 30, CCPA, and PIPA logging requirements
"""

import json
import hashlib
import hmac
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid
import gzip
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import sqlite3
import aiosqlite
import asyncpg

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Audit event types"""
    # Authentication events
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILED = "auth_failed"
    AUTHENTICATION_ERROR = "auth_error"
    SESSION_CREATED = "session_created"
    SESSION_INVALIDATED = "session_invalidated"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"

    # Authorization events
    AUTHORIZATION_SUCCESS = "authz_success"
    AUTHORIZATION_FAILED = "authz_failed"
    AUTHORIZATION_ERROR = "authz_error"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # Data access events
    DOCUMENT_ACCESSED = "document_accessed"
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    SEARCH_PERFORMED = "search_performed"
    CLASSIFICATION_PERFORMED = "classification_performed"

    # PII and privacy events
    PII_DETECTED = "pii_detected"
    PII_ACCESSED = "pii_accessed"
    PII_MASKED = "pii_masked"
    PII_EXPORTED = "pii_exported"
    DATA_SUBJECT_REQUEST = "data_subject_request"
    DATA_RETENTION_ACTION = "data_retention_action"

    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGED = "config_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

    # Security events
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_SANITIZED = "data_sanitized"
    DATA_SANITIZATION_ERROR = "data_sanitization_error"
    HIGH_RISK_OPERATION_BLOCKED = "high_risk_operation_blocked"
    VULNERABILITY_DETECTED = "vulnerability_detected"

    # Compliance events
    COMPLIANCE_CHECK = "compliance_check"
    GDPR_REQUEST = "gdpr_request"
    CCPA_REQUEST = "ccpa_request"
    PIPA_REQUEST = "pipa_request"
    AUDIT_LOG_ACCESSED = "audit_log_accessed"

class SeverityLevel(Enum):
    """Event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: EventType
    severity: SeverityLevel
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    source_system: str = "dt-rag"
    compliance_flags: List[str] = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.compliance_flags:
            self.compliance_flags = []

@dataclass
class AuditEntry:
    """Complete audit entry with integrity protection"""
    event: SecurityEvent
    hash_value: str
    previous_hash: str
    sequence_number: int
    signature: Optional[str] = None

class AuditLogger:
    """
    Enterprise-grade audit logging system with tamper-proof logs
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Storage configuration
        self.storage_type = self.config.get('storage_type', 'sqlite')  # sqlite, postgresql, file
        self.log_directory = Path(self.config.get('log_directory', './audit_logs'))
        self.max_log_file_size = self.config.get('max_log_file_size', 100 * 1024 * 1024)  # 100MB
        self.retention_days = self.config.get('retention_days', 2555)  # 7 years for compliance

        # Security configuration
        self.enable_encryption = self.config.get('enable_encryption', True)
        self.enable_signing = self.config.get('enable_signing', True)
        self.compression_enabled = self.config.get('compression_enabled', True)

        # Initialize storage
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Integrity protection
        self._last_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self._sequence_number = 0
        self._hmac_key = self._generate_hmac_key()

        # Digital signing (for non-repudiation)
        if self.enable_signing:
            self._private_key, self._public_key = self._generate_signing_keys()

        # In-memory cache for performance
        self._cache: List[AuditEntry] = []
        self._cache_size = self.config.get('cache_size', 1000)

        # Background tasks
        self._flush_task = None
        self._compression_task = None

        # Metrics
        self._metrics = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "failed_writes": 0,
            "integrity_violations": 0
        }

        logger.info("AuditLogger initialized with enterprise security features")

    async def log_event(self, event: SecurityEvent):
        """Log a security event with integrity protection"""
        try:
            # 1. Validate event
            if not self._validate_event(event):
                raise AuditError("Invalid event data")

            # 2. Add compliance flags
            self._add_compliance_flags(event)

            # 3. Calculate hash for integrity
            event_hash = self._calculate_event_hash(event)

            # 4. Create audit entry
            self._sequence_number += 1
            audit_entry = AuditEntry(
                event=event,
                hash_value=event_hash,
                previous_hash=self._last_hash,
                sequence_number=self._sequence_number
            )

            # 5. Sign entry for non-repudiation
            if self.enable_signing:
                audit_entry.signature = self._sign_entry(audit_entry)

            # 6. Update hash chain
            self._last_hash = self._calculate_entry_hash(audit_entry)

            # 7. Add to cache
            self._cache.append(audit_entry)

            # 8. Update metrics
            self._update_metrics(event)

            # 9. Flush if cache is full
            if len(self._cache) >= self._cache_size:
                await self._flush_cache()

            logger.debug(f"Event logged: {event.event_type.value}")

        except Exception as e:
            self._metrics["failed_writes"] += 1
            logger.error(f"Failed to log event: {e}")
            raise AuditError(f"Event logging failed: {str(e)}")

    async def query_events(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: List[EventType] = None,
        user_id: str = None,
        severity: SeverityLevel = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Query audit events with filters"""
        try:
            # Ensure cache is flushed
            await self._flush_cache()

            if self.storage_type == 'sqlite':
                return await self._query_sqlite(
                    start_time, end_time, event_types, user_id, severity, limit
                )
            elif self.storage_type == 'postgresql':
                return await self._query_postgresql(
                    start_time, end_time, event_types, user_id, severity, limit
                )
            else:
                return await self._query_files(
                    start_time, end_time, event_types, user_id, severity, limit
                )

        except Exception as e:
            logger.error(f"Failed to query events: {e}")
            raise AuditError(f"Event query failed: {str(e)}")

    async def verify_integrity(
        self,
        start_sequence: int = None,
        end_sequence: int = None
    ) -> Dict[str, Any]:
        """Verify audit log integrity"""
        try:
            violations = []
            verified_entries = 0
            total_entries = 0

            if self.storage_type == 'sqlite':
                entries = await self._get_entries_sqlite(start_sequence, end_sequence)
            else:
                entries = await self._get_entries_files(start_sequence, end_sequence)

            previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"

            for entry in entries:
                total_entries += 1

                # Verify hash chain
                if entry.previous_hash != previous_hash:
                    violations.append({
                        "sequence": entry.sequence_number,
                        "type": "hash_chain_violation",
                        "expected": previous_hash,
                        "actual": entry.previous_hash
                    })

                # Verify entry hash
                calculated_hash = self._calculate_event_hash(entry.event)
                if calculated_hash != entry.hash_value:
                    violations.append({
                        "sequence": entry.sequence_number,
                        "type": "entry_hash_violation",
                        "expected": calculated_hash,
                        "actual": entry.hash_value
                    })

                # Verify signature
                if self.enable_signing and entry.signature:
                    if not self._verify_signature(entry):
                        violations.append({
                            "sequence": entry.sequence_number,
                            "type": "signature_violation"
                        })

                if not violations:
                    verified_entries += 1

                previous_hash = self._calculate_entry_hash(entry)

            self._metrics["integrity_violations"] += len(violations)

            return {
                "verified": len(violations) == 0,
                "total_entries": total_entries,
                "verified_entries": verified_entries,
                "violations": violations,
                "verification_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            raise AuditError(f"Integrity verification failed: {str(e)}")

    async def export_compliance_report(
        self,
        regulation: str,  # 'gdpr', 'ccpa', 'pipa'
        start_time: datetime,
        end_time: datetime,
        subject_id: str = None
    ) -> Dict[str, Any]:
        """Export compliance report for regulatory requirements"""
        try:
            # Get relevant events
            events = await self.query_events(
                start_time=start_time,
                end_time=end_time,
                user_id=subject_id
            )

            # Filter events by compliance flags
            compliance_events = [
                event for event in events
                if regulation.upper() in event.compliance_flags
            ]

            # Categorize events by regulation requirements
            if regulation.lower() == 'gdpr':
                return self._generate_gdpr_report(compliance_events, start_time, end_time)
            elif regulation.lower() == 'ccpa':
                return self._generate_ccpa_report(compliance_events, start_time, end_time)
            elif regulation.lower() == 'pipa':
                return self._generate_pipa_report(compliance_events, start_time, end_time)
            else:
                raise AuditError(f"Unsupported regulation: {regulation}")

        except Exception as e:
            logger.error(f"Compliance report generation failed: {e}")
            raise AuditError(f"Compliance report failed: {str(e)}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get audit logging metrics"""
        return {
            **self._metrics,
            "cache_size": len(self._cache),
            "last_sequence": self._sequence_number,
            "storage_type": self.storage_type,
            "encryption_enabled": self.enable_encryption,
            "signing_enabled": self.enable_signing
        }

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        self._compression_task = asyncio.create_task(self._periodic_compression())

    async def stop_background_tasks(self):
        """Stop background tasks and flush remaining data"""
        if self._flush_task:
            self._flush_task.cancel()
        if self._compression_task:
            self._compression_task.cancel()

        await self._flush_cache()

    # Private methods

    def _validate_event(self, event: SecurityEvent) -> bool:
        """Validate event data"""
        if not event.event_type or not event.severity:
            return False

        if not event.timestamp:
            event.timestamp = datetime.utcnow()

        if not event.event_id:
            event.event_id = str(uuid.uuid4())

        return True

    def _add_compliance_flags(self, event: SecurityEvent):
        """Add compliance flags based on event type"""
        # GDPR flags
        if event.event_type in [
            EventType.PII_ACCESSED,
            EventType.PII_DETECTED,
            EventType.PII_EXPORTED,
            EventType.DATA_SUBJECT_REQUEST
        ]:
            event.compliance_flags.append("GDPR")

        # CCPA flags
        if event.event_type in [
            EventType.PII_ACCESSED,
            EventType.PII_EXPORTED,
            EventType.DATA_SUBJECT_REQUEST
        ]:
            event.compliance_flags.append("CCPA")

        # PIPA flags (Korean)
        if event.event_type in [
            EventType.PII_ACCESSED,
            EventType.PII_DETECTED,
            EventType.PII_EXPORTED
        ]:
            event.compliance_flags.append("PIPA")

        # SOX compliance for financial data
        if "financial" in str(event.details).lower():
            event.compliance_flags.append("SOX")

    def _calculate_event_hash(self, event: SecurityEvent) -> str:
        """Calculate SHA-256 hash of event data"""
        event_dict = asdict(event)
        event_json = json.dumps(event_dict, sort_keys=True, default=str)
        return hashlib.sha256(event_json.encode()).hexdigest()

    def _calculate_entry_hash(self, entry: AuditEntry) -> str:
        """Calculate hash of complete audit entry"""
        entry_data = f"{entry.hash_value}{entry.previous_hash}{entry.sequence_number}"
        return hashlib.sha256(entry_data.encode()).hexdigest()

    def _generate_hmac_key(self) -> bytes:
        """Generate HMAC key for integrity protection"""
        key_file = self.log_directory / "hmac.key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = os.urandom(32)
            key_file.write_bytes(key)
            return key

    def _generate_signing_keys(self) -> tuple:
        """Generate RSA key pair for digital signing"""
        private_key_file = self.log_directory / "private.pem"
        public_key_file = self.log_directory / "public.pem"

        if private_key_file.exists() and public_key_file.exists():
            private_key = load_pem_private_key(
                private_key_file.read_bytes(),
                password=None
            )
            public_key = serialization.load_pem_public_key(
                public_key_file.read_bytes()
            )
            return private_key, public_key

        # Generate new key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # Save keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        private_key_file.write_bytes(private_pem)
        public_key_file.write_bytes(public_pem)

        return private_key, public_key

    def _sign_entry(self, entry: AuditEntry) -> str:
        """Sign audit entry for non-repudiation"""
        if not self._private_key:
            return ""

        entry_data = f"{entry.hash_value}{entry.previous_hash}{entry.sequence_number}"
        signature = self._private_key.sign(
            entry_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature.hex()

    def _verify_signature(self, entry: AuditEntry) -> bool:
        """Verify entry signature"""
        if not self._public_key or not entry.signature:
            return False

        try:
            entry_data = f"{entry.hash_value}{entry.previous_hash}{entry.sequence_number}"
            signature = bytes.fromhex(entry.signature)

            self._public_key.verify(
                signature,
                entry_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True

        except Exception:
            return False

    def _update_metrics(self, event: SecurityEvent):
        """Update logging metrics"""
        self._metrics["total_events"] += 1

        event_type = event.event_type.value
        if event_type not in self._metrics["events_by_type"]:
            self._metrics["events_by_type"][event_type] = 0
        self._metrics["events_by_type"][event_type] += 1

        severity = event.severity.value
        if severity not in self._metrics["events_by_severity"]:
            self._metrics["events_by_severity"][severity] = 0
        self._metrics["events_by_severity"][severity] += 1

    async def _flush_cache(self):
        """Flush cache to persistent storage"""
        if not self._cache:
            return

        try:
            if self.storage_type == 'sqlite':
                await self._write_sqlite(self._cache)
            elif self.storage_type == 'postgresql':
                await self._write_postgresql(self._cache)
            else:
                await self._write_files(self._cache)

            self._cache.clear()
            logger.debug(f"Cache flushed to {self.storage_type}")

        except Exception as e:
            logger.error(f"Cache flush failed: {e}")
            raise

    async def _write_sqlite(self, entries: List[AuditEntry]):
        """Write entries to SQLite database"""
        db_path = self.log_directory / "audit.db"

        async with aiosqlite.connect(str(db_path)) as db:
            # Create table if not exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    sequence_number INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_id TEXT,
                    resource TEXT,
                    action TEXT,
                    details TEXT,
                    metadata TEXT,
                    compliance_flags TEXT,
                    hash_value TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    signature TEXT
                )
            """)

            # Insert entries
            for entry in entries:
                await db.execute("""
                    INSERT INTO audit_entries VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    entry.sequence_number,
                    entry.event.event_id,
                    entry.event.event_type.value,
                    entry.event.severity.value,
                    entry.event.timestamp.isoformat(),
                    entry.event.user_id,
                    entry.event.session_id,
                    entry.event.ip_address,
                    entry.event.user_agent,
                    entry.event.request_id,
                    entry.event.resource,
                    entry.event.action,
                    json.dumps(entry.event.details),
                    json.dumps(entry.event.metadata),
                    json.dumps(entry.event.compliance_flags),
                    entry.hash_value,
                    entry.previous_hash,
                    entry.signature
                ))

            await db.commit()

    async def _write_files(self, entries: List[AuditEntry]):
        """Write entries to files"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H")
        file_path = self.log_directory / f"audit_{timestamp}.jsonl"

        with open(file_path, 'a') as f:
            for entry in entries:
                entry_dict = {
                    "sequence_number": entry.sequence_number,
                    "event": asdict(entry.event),
                    "hash_value": entry.hash_value,
                    "previous_hash": entry.previous_hash,
                    "signature": entry.signature
                }

                line = json.dumps(entry_dict, default=str) + "\n"

                if self.enable_encryption:
                    line = self._encrypt_line(line)

                f.write(line)

    def _encrypt_line(self, line: str) -> str:
        """Encrypt log line (placeholder - implement with proper encryption)"""
        # In production, use AES-GCM or similar
        return line

    async def _periodic_flush(self):
        """Periodic cache flush task"""
        while True:
            try:
                await asyncio.sleep(60)  # Flush every minute
                if self._cache:
                    await self._flush_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic flush error: {e}")

    async def _periodic_compression(self):
        """Periodic log compression task"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                await self._compress_old_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic compression error: {e}")

    async def _compress_old_logs(self):
        """Compress old log files"""
        cutoff_time = datetime.utcnow() - timedelta(days=1)

        for file_path in self.log_directory.glob("audit_*.jsonl"):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                compressed_path = file_path.with_suffix('.jsonl.gz')

                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)

                file_path.unlink()
                logger.info(f"Compressed log file: {file_path}")

    def _generate_gdpr_report(self, events: List[SecurityEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        pii_access_events = [e for e in events if e.event_type == EventType.PII_ACCESSED]
        data_subject_requests = [e for e in events if e.event_type == EventType.DATA_SUBJECT_REQUEST]

        return {
            "regulation": "GDPR",
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {
                "total_events": len(events),
                "pii_access_events": len(pii_access_events),
                "data_subject_requests": len(data_subject_requests)
            },
            "detailed_events": [asdict(event) for event in events],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_ccpa_report(self, events: List[SecurityEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate CCPA compliance report"""
        # Similar to GDPR but with CCPA-specific requirements
        return {
            "regulation": "CCPA",
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {
                "total_events": len(events)
            },
            "detailed_events": [asdict(event) for event in events],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_pipa_report(self, events: List[SecurityEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate PIPA (Korean) compliance report"""
        return {
            "regulation": "PIPA",
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {
                "total_events": len(events)
            },
            "detailed_events": [asdict(event) for event in events],
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _query_sqlite(self, start_time, end_time, event_types, user_id, severity, limit) -> List[SecurityEvent]:
        """Query events from SQLite database"""
        db_path = self.log_directory / "audit.db"

        if not db_path.exists():
            return []

        conditions = []
        params = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        if event_types:
            placeholders = ",".join("?" * len(event_types))
            conditions.append(f"event_type IN ({placeholders})")
            params.extend([et.value for et in event_types])

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if severity:
            conditions.append("severity = ?")
            params.append(severity.value)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT * FROM audit_entries
            {where_clause}
            ORDER BY sequence_number DESC
            LIMIT ?
        """
        params.append(limit)

        async with aiosqlite.connect(str(db_path)) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                events = []
                for row in rows:
                    event = SecurityEvent(
                        event_id=row[1],
                        event_type=EventType(row[2]),
                        severity=SeverityLevel(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        user_id=row[5],
                        session_id=row[6],
                        ip_address=row[7],
                        user_agent=row[8],
                        request_id=row[9],
                        resource=row[10],
                        action=row[11],
                        details=json.loads(row[12]) if row[12] else {},
                        metadata=json.loads(row[13]) if row[13] else {},
                        compliance_flags=json.loads(row[14]) if row[14] else []
                    )
                    events.append(event)

                return events

class AuditError(Exception):
    """Audit logging exception"""
    pass