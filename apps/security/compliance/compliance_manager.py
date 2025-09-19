"""
Compliance Manager for DT-RAG v1.8.1
Manages GDPR, CCPA, PIPA and other regulatory compliance requirements
Implements data subject rights, consent management, and compliance reporting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid
from .pii_detector import PIIDetector, PIIType, PIIFinding

logger = logging.getLogger(__name__)

class DataSubjectRightType(Enum):
    """Types of data subject rights"""
    # GDPR Rights
    ACCESS = "access"  # Right to access personal data
    RECTIFICATION = "rectification"  # Right to rectify inaccurate data
    ERASURE = "erasure"  # Right to be forgotten
    RESTRICT_PROCESSING = "restrict_processing"  # Right to restrict processing
    DATA_PORTABILITY = "data_portability"  # Right to data portability
    OBJECT = "object"  # Right to object to processing

    # CCPA Rights
    KNOW = "know"  # Right to know about personal information
    DELETE = "delete"  # Right to delete personal information
    OPT_OUT = "opt_out"  # Right to opt-out of sale

    # PIPA Rights (Korean)
    PROCESSING_STATUS = "processing_status"  # Right to know processing status
    STOP_PROCESSING = "stop_processing"  # Right to stop processing
    DESTROY = "destroy"  # Right to destroy personal information

class ConsentType(Enum):
    """Types of consent"""
    EXPLICIT = "explicit"  # GDPR explicit consent
    IMPLIED = "implied"  # Implied consent
    OPT_IN = "opt_in"  # Active opt-in
    OPT_OUT = "opt_out"  # Opt-out model

class LegalBasis(Enum):
    """GDPR legal basis for processing"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class ProcessingPurpose(Enum):
    """Purposes for data processing"""
    SERVICE_DELIVERY = "service_delivery"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RESEARCH = "research"
    SYSTEM_ADMINISTRATION = "system_administration"

@dataclass
class DataSubjectRequest:
    """Data subject request"""
    request_id: str
    request_type: DataSubjectRightType
    data_subject_id: str
    email: str
    requested_at: datetime
    status: str  # pending, in_progress, completed, rejected
    legal_basis: Optional[str] = None
    verification_status: str = "pending"  # pending, verified, failed
    response_due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request_details: Dict[str, Any] = None
    response_data: Optional[Dict[str, Any]] = None
    compliance_notes: Optional[str] = None

@dataclass
class ConsentRecord:
    """Consent record"""
    consent_id: str
    data_subject_id: str
    purpose: ProcessingPurpose
    consent_type: ConsentType
    legal_basis: LegalBasis
    granted_at: datetime
    is_active: bool = True
    withdrawn_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    consent_text: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = None

@dataclass
class ProcessingActivity:
    """Processing activity record (GDPR Article 30)"""
    activity_id: str
    name: str
    description: str
    controller: str
    purposes: List[ProcessingPurpose]
    legal_basis: List[LegalBasis]
    data_categories: List[str]
    data_subjects: List[str]
    recipients: List[str]
    retention_period: str
    security_measures: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

@dataclass
class DataBreachRecord:
    """Data breach record"""
    breach_id: str
    detected_at: datetime
    breach_type: str
    severity: str  # low, medium, high, critical
    affected_data_types: List[str]
    affected_subjects_count: int
    description: str
    cause: str
    containment_measures: List[str]
    reported_to_authority: bool = False
    reported_at: Optional[datetime] = None
    authority_reference: Optional[str] = None
    subjects_notified: bool = False
    notification_date: Optional[datetime] = None
    status: str = "open"  # open, investigating, contained, closed

class ComplianceManager:
    """
    Comprehensive compliance management system
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Compliance settings
        self.supported_regulations = self.config.get(
            'supported_regulations',
            ['GDPR', 'CCPA', 'PIPA', 'SOX', 'HIPAA']
        )

        # Response timeframes (in days)
        self.response_timeframes = {
            'GDPR': {
                DataSubjectRightType.ACCESS: 30,
                DataSubjectRightType.RECTIFICATION: 30,
                DataSubjectRightType.ERASURE: 30,
                DataSubjectRightType.RESTRICT_PROCESSING: 30,
                DataSubjectRightType.DATA_PORTABILITY: 30,
                DataSubjectRightType.OBJECT: 30
            },
            'CCPA': {
                DataSubjectRightType.KNOW: 45,
                DataSubjectRightType.DELETE: 45,
                DataSubjectRightType.OPT_OUT: 15
            },
            'PIPA': {
                DataSubjectRightType.PROCESSING_STATUS: 10,
                DataSubjectRightType.STOP_PROCESSING: 10,
                DataSubjectRightType.DESTROY: 10
            }
        }

        # Data storage
        self.storage_path = Path(self.config.get('storage_path', './compliance_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory stores (use database in production)
        self._consent_records: Dict[str, ConsentRecord] = {}
        self._data_subject_requests: Dict[str, DataSubjectRequest] = {}
        self._processing_activities: Dict[str, ProcessingActivity] = {}
        self._data_breaches: Dict[str, DataBreachRecord] = {}

        # Initialize PII detector
        self.pii_detector = PIIDetector(self.config.get('pii_detector', {}))

        # Metrics
        self._metrics = {
            "total_requests": 0,
            "requests_by_type": {},
            "requests_by_regulation": {},
            "consent_records": 0,
            "active_consents": 0,
            "withdrawn_consents": 0,
            "data_breaches": 0,
            "compliance_violations": 0
        }

        logger.info("ComplianceManager initialized with multi-regulation support")

    # Data Subject Rights Management

    async def submit_data_subject_request(
        self,
        request_type: DataSubjectRightType,
        data_subject_id: str,
        email: str,
        request_details: Dict[str, Any] = None,
        regulation: str = "GDPR"
    ) -> DataSubjectRequest:
        """Submit a data subject request"""

        request_id = str(uuid.uuid4())
        request = DataSubjectRequest(
            request_id=request_id,
            request_type=request_type,
            data_subject_id=data_subject_id,
            email=email,
            requested_at=datetime.utcnow(),
            status="pending",
            request_details=request_details or {}
        )

        # Set response due date based on regulation
        if regulation in self.response_timeframes:
            timeframe = self.response_timeframes[regulation].get(request_type, 30)
            request.response_due_date = datetime.utcnow() + timedelta(days=timeframe)

        self._data_subject_requests[request_id] = request

        # Update metrics
        self._metrics["total_requests"] += 1
        req_type = request_type.value
        if req_type not in self._metrics["requests_by_type"]:
            self._metrics["requests_by_type"][req_type] = 0
        self._metrics["requests_by_type"][req_type] += 1

        if regulation not in self._metrics["requests_by_regulation"]:
            self._metrics["requests_by_regulation"][regulation] = 0
        self._metrics["requests_by_regulation"][regulation] += 1

        logger.info(f"Data subject request submitted: {request_id} ({request_type.value})")

        # Start processing automatically
        asyncio.create_task(self._process_data_subject_request(request))

        return request

    async def verify_data_subject_identity(
        self,
        request_id: str,
        verification_data: Dict[str, Any]
    ) -> bool:
        """Verify data subject identity for request processing"""

        request = self._data_subject_requests.get(request_id)
        if not request:
            return False

        # Simple verification logic (enhance based on requirements)
        if verification_data.get('email') == request.email:
            request.verification_status = "verified"
            request.status = "in_progress"

            logger.info(f"Data subject identity verified: {request_id}")
            return True

        request.verification_status = "failed"
        logger.warning(f"Data subject identity verification failed: {request_id}")
        return False

    async def get_data_subject_data(self, data_subject_id: str) -> Dict[str, Any]:
        """Get all data for a data subject (for access requests)"""

        data = {
            "data_subject_id": data_subject_id,
            "extracted_at": datetime.utcnow().isoformat(),
            "data_categories": {
                "consent_records": [],
                "processing_activities": [],
                "audit_logs": [],
                "documents": [],
                "search_history": []
            }
        }

        # Get consent records
        consents = [
            asdict(consent) for consent in self._consent_records.values()
            if consent.data_subject_id == data_subject_id
        ]
        data["data_categories"]["consent_records"] = consents

        # Get processing activities where this subject is mentioned
        activities = [
            asdict(activity) for activity in self._processing_activities.values()
            if data_subject_id in activity.data_subjects
        ]
        data["data_categories"]["processing_activities"] = activities

        # This would integrate with other system components to gather data
        # For example: documents, search history, classification results, etc.

        return data

    async def delete_data_subject_data(
        self,
        data_subject_id: str,
        categories: List[str] = None
    ) -> Dict[str, Any]:
        """Delete data subject data (for erasure/delete requests)"""

        deletion_report = {
            "data_subject_id": data_subject_id,
            "deleted_at": datetime.utcnow().isoformat(),
            "categories_deleted": [],
            "retention_exceptions": [],
            "failed_deletions": []
        }

        try:
            # Delete consent records
            deleted_consents = []
            for consent_id, consent in list(self._consent_records.items()):
                if consent.data_subject_id == data_subject_id:
                    del self._consent_records[consent_id]
                    deleted_consents.append(consent_id)

            if deleted_consents:
                deletion_report["categories_deleted"].append({
                    "category": "consent_records",
                    "count": len(deleted_consents),
                    "items": deleted_consents
                })

            # Mark for deletion in other systems
            # This would cascade to document database, search indices, etc.

            logger.info(f"Data deletion completed for subject: {data_subject_id}")

        except Exception as e:
            logger.error(f"Data deletion failed for subject {data_subject_id}: {e}")
            deletion_report["failed_deletions"].append({
                "category": "all",
                "error": str(e)
            })

        return deletion_report

    # Consent Management

    async def record_consent(
        self,
        data_subject_id: str,
        purpose: ProcessingPurpose,
        consent_type: ConsentType,
        legal_basis: LegalBasis,
        consent_text: str = None,
        expires_at: datetime = None
    ) -> ConsentRecord:
        """Record consent from data subject"""

        consent_id = str(uuid.uuid4())
        consent = ConsentRecord(
            consent_id=consent_id,
            data_subject_id=data_subject_id,
            purpose=purpose,
            consent_type=consent_type,
            legal_basis=legal_basis,
            granted_at=datetime.utcnow(),
            consent_text=consent_text,
            expires_at=expires_at,
            metadata={}
        )

        self._consent_records[consent_id] = consent

        # Update metrics
        self._metrics["consent_records"] += 1
        self._metrics["active_consents"] += 1

        logger.info(f"Consent recorded: {consent_id} for subject {data_subject_id}")
        return consent

    async def withdraw_consent(
        self,
        data_subject_id: str,
        purpose: ProcessingPurpose = None,
        consent_id: str = None
    ) -> List[str]:
        """Withdraw consent"""

        withdrawn_consents = []

        for cid, consent in self._consent_records.items():
            if consent.data_subject_id == data_subject_id and consent.is_active:
                # Withdraw specific consent or all for purpose
                if consent_id and cid == consent_id:
                    consent.is_active = False
                    consent.withdrawn_at = datetime.utcnow()
                    withdrawn_consents.append(cid)
                elif purpose and consent.purpose == purpose:
                    consent.is_active = False
                    consent.withdrawn_at = datetime.utcnow()
                    withdrawn_consents.append(cid)
                elif not consent_id and not purpose:
                    # Withdraw all consents
                    consent.is_active = False
                    consent.withdrawn_at = datetime.utcnow()
                    withdrawn_consents.append(cid)

        # Update metrics
        self._metrics["withdrawn_consents"] += len(withdrawn_consents)
        self._metrics["active_consents"] -= len(withdrawn_consents)

        logger.info(f"Consent withdrawn: {withdrawn_consents} for subject {data_subject_id}")
        return withdrawn_consents

    async def check_consent_validity(
        self,
        data_subject_id: str,
        purpose: ProcessingPurpose
    ) -> bool:
        """Check if valid consent exists for processing purpose"""

        for consent in self._consent_records.values():
            if (consent.data_subject_id == data_subject_id and
                consent.purpose == purpose and
                consent.is_active):

                # Check expiration
                if consent.expires_at and consent.expires_at < datetime.utcnow():
                    consent.is_active = False
                    consent.withdrawn_at = datetime.utcnow()
                    self._metrics["active_consents"] -= 1
                    return False

                return True

        return False

    # Processing Activities (GDPR Article 30)

    async def register_processing_activity(
        self,
        name: str,
        description: str,
        controller: str,
        purposes: List[ProcessingPurpose],
        legal_basis: List[LegalBasis],
        data_categories: List[str],
        data_subjects: List[str],
        recipients: List[str],
        retention_period: str,
        security_measures: List[str]
    ) -> ProcessingActivity:
        """Register a processing activity"""

        activity_id = str(uuid.uuid4())
        activity = ProcessingActivity(
            activity_id=activity_id,
            name=name,
            description=description,
            controller=controller,
            purposes=purposes,
            legal_basis=legal_basis,
            data_categories=data_categories,
            data_subjects=data_subjects,
            recipients=recipients,
            retention_period=retention_period,
            security_measures=security_measures,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self._processing_activities[activity_id] = activity

        logger.info(f"Processing activity registered: {activity_id} - {name}")
        return activity

    async def get_processing_activities_report(self) -> Dict[str, Any]:
        """Generate processing activities report (GDPR Article 30)"""

        activities = [asdict(activity) for activity in self._processing_activities.values()]

        return {
            "report_type": "processing_activities",
            "generated_at": datetime.utcnow().isoformat(),
            "total_activities": len(activities),
            "activities": activities
        }

    # Data Breach Management

    async def report_data_breach(
        self,
        breach_type: str,
        severity: str,
        affected_data_types: List[str],
        affected_subjects_count: int,
        description: str,
        cause: str,
        containment_measures: List[str] = None
    ) -> DataBreachRecord:
        """Report a data breach"""

        breach_id = str(uuid.uuid4())
        breach = DataBreachRecord(
            breach_id=breach_id,
            detected_at=datetime.utcnow(),
            breach_type=breach_type,
            severity=severity,
            affected_data_types=affected_data_types,
            affected_subjects_count=affected_subjects_count,
            description=description,
            cause=cause,
            containment_measures=containment_measures or []
        )

        self._data_breaches[breach_id] = breach

        # Update metrics
        self._metrics["data_breaches"] += 1

        # Check if authority notification is required
        await self._check_breach_notification_requirements(breach)

        logger.critical(f"Data breach reported: {breach_id} - {severity} severity")
        return breach

    async def _check_breach_notification_requirements(self, breach: DataBreachRecord):
        """Check if breach requires authority notification"""

        # GDPR: 72 hours to notify if high risk
        if breach.severity in ['high', 'critical']:
            if 'personal_data' in breach.affected_data_types:
                # Should notify supervisory authority within 72 hours
                logger.warning(f"Breach {breach.breach_id} requires GDPR authority notification")

        # Additional regulation checks would go here

    # Privacy Impact Assessment

    async def conduct_privacy_impact_assessment(
        self,
        processing_description: str,
        data_types: List[str],
        purposes: List[ProcessingPurpose],
        legal_basis: List[LegalBasis]
    ) -> Dict[str, Any]:
        """Conduct Privacy Impact Assessment (PIA/DPIA)"""

        pia_id = str(uuid.uuid4())

        # Risk assessment
        risk_score = await self._calculate_privacy_risk(
            data_types, purposes, legal_basis
        )

        # Mitigation recommendations
        mitigations = await self._recommend_mitigations(risk_score, data_types)

        pia = {
            "pia_id": pia_id,
            "conducted_at": datetime.utcnow().isoformat(),
            "processing_description": processing_description,
            "data_types": data_types,
            "purposes": [p.value for p in purposes],
            "legal_basis": [lb.value for lb in legal_basis],
            "risk_assessment": {
                "overall_risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "high_risk_factors": [],
                "recommendations": mitigations
            },
            "compliance_requirements": await self._get_compliance_requirements(data_types),
            "conclusion": "DPIA required" if risk_score > 0.7 else "Standard measures sufficient"
        }

        logger.info(f"Privacy Impact Assessment conducted: {pia_id}")
        return pia

    # Compliance Monitoring

    async def run_compliance_check(
        self,
        regulation: str = "GDPR"
    ) -> Dict[str, Any]:
        """Run comprehensive compliance check"""

        compliance_report = {
            "regulation": regulation,
            "check_date": datetime.utcnow().isoformat(),
            "overall_compliance": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }

        # Check consent validity
        await self._check_consent_compliance(compliance_report)

        # Check data retention
        await self._check_retention_compliance(compliance_report)

        # Check request response times
        await self._check_request_response_compliance(compliance_report, regulation)

        # Check processing activities
        await self._check_processing_activities_compliance(compliance_report)

        # Calculate overall compliance
        if compliance_report["violations"]:
            compliance_report["overall_compliance"] = False
            self._metrics["compliance_violations"] += len(compliance_report["violations"])

        logger.info(f"Compliance check completed for {regulation}")
        return compliance_report

    async def get_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics"""
        return {
            **self._metrics,
            "active_processing_activities": len(self._processing_activities),
            "open_data_breaches": len([
                b for b in self._data_breaches.values()
                if b.status == "open"
            ]),
            "overdue_requests": len([
                r for r in self._data_subject_requests.values()
                if r.response_due_date and r.response_due_date < datetime.utcnow()
                and r.status not in ["completed", "rejected"]
            ])
        }

    # Private methods

    async def _process_data_subject_request(self, request: DataSubjectRequest):
        """Process data subject request automatically"""
        try:
            # Wait for identity verification
            timeout = 0
            while request.verification_status == "pending" and timeout < 300:  # 5 minutes
                await asyncio.sleep(1)
                timeout += 1

            if request.verification_status != "verified":
                request.status = "rejected"
                request.completed_at = datetime.utcnow()
                request.compliance_notes = "Identity verification failed"
                return

            # Process based on request type
            if request.request_type == DataSubjectRightType.ACCESS:
                data = await self.get_data_subject_data(request.data_subject_id)
                request.response_data = data

            elif request.request_type == DataSubjectRightType.ERASURE:
                deletion_report = await self.delete_data_subject_data(request.data_subject_id)
                request.response_data = deletion_report

            elif request.request_type == DataSubjectRightType.DATA_PORTABILITY:
                data = await self.get_data_subject_data(request.data_subject_id)
                # Format for portability
                request.response_data = {
                    "format": "JSON",
                    "data": data
                }

            # Mark as completed
            request.status = "completed"
            request.completed_at = datetime.utcnow()

        except Exception as e:
            request.status = "failed"
            request.compliance_notes = f"Processing failed: {str(e)}"
            logger.error(f"Request processing failed: {request.request_id} - {e}")

    async def _calculate_privacy_risk(
        self,
        data_types: List[str],
        purposes: List[ProcessingPurpose],
        legal_basis: List[LegalBasis]
    ) -> float:
        """Calculate privacy risk score"""
        risk_score = 0.0

        # Data type risk
        high_risk_data = ['biometric', 'genetic', 'health', 'financial', 'location']
        for data_type in data_types:
            if any(risk_term in data_type.lower() for risk_term in high_risk_data):
                risk_score += 0.3

        # Purpose risk
        high_risk_purposes = [ProcessingPurpose.MARKETING, ProcessingPurpose.ANALYTICS]
        for purpose in purposes:
            if purpose in high_risk_purposes:
                risk_score += 0.2

        # Legal basis risk
        if LegalBasis.LEGITIMATE_INTERESTS in legal_basis:
            risk_score += 0.1

        return min(risk_score, 1.0)

    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.7:
            return "medium"
        else:
            return "high"

    async def _recommend_mitigations(
        self,
        risk_score: float,
        data_types: List[str]
    ) -> List[str]:
        """Recommend risk mitigation measures"""
        mitigations = []

        if risk_score > 0.5:
            mitigations.append("Implement data minimization practices")
            mitigations.append("Enhance encryption and access controls")

        if risk_score > 0.7:
            mitigations.append("Conduct regular security audits")
            mitigations.append("Implement pseudonymization")
            mitigations.append("Consider appointing Data Protection Officer")

        if any('biometric' in dt.lower() for dt in data_types):
            mitigations.append("Implement biometric data specific protections")

        return mitigations

    async def _get_compliance_requirements(self, data_types: List[str]) -> List[str]:
        """Get applicable compliance requirements"""
        requirements = ["GDPR Article 6 (Lawfulness)"]

        if any('health' in dt.lower() for dt in data_types):
            requirements.append("GDPR Article 9 (Special categories)")

        if any('child' in dt.lower() for dt in data_types):
            requirements.append("GDPR Article 8 (Children)")

        return requirements

    async def _check_consent_compliance(self, report: Dict[str, Any]):
        """Check consent compliance"""
        expired_consents = 0

        for consent in self._consent_records.values():
            if (consent.expires_at and
                consent.expires_at < datetime.utcnow() and
                consent.is_active):
                expired_consents += 1

        if expired_consents > 0:
            report["violations"].append({
                "type": "expired_consent",
                "count": expired_consents,
                "description": f"{expired_consents} expired consents still marked as active"
            })

    async def _check_retention_compliance(self, report: Dict[str, Any]):
        """Check data retention compliance"""
        # This would check actual data against retention policies
        # For now, just a placeholder
        pass

    async def _check_request_response_compliance(
        self,
        report: Dict[str, Any],
        regulation: str
    ):
        """Check data subject request response compliance"""
        overdue_requests = []

        for request in self._data_subject_requests.values():
            if (request.response_due_date and
                request.response_due_date < datetime.utcnow() and
                request.status not in ["completed", "rejected"]):
                overdue_requests.append(request.request_id)

        if overdue_requests:
            report["violations"].append({
                "type": "overdue_requests",
                "count": len(overdue_requests),
                "requests": overdue_requests,
                "description": f"{len(overdue_requests)} requests overdue for {regulation}"
            })

    async def _check_processing_activities_compliance(self, report: Dict[str, Any]):
        """Check processing activities compliance"""
        activities_without_legal_basis = []

        for activity in self._processing_activities.values():
            if not activity.legal_basis:
                activities_without_legal_basis.append(activity.activity_id)

        if activities_without_legal_basis:
            report["violations"].append({
                "type": "missing_legal_basis",
                "count": len(activities_without_legal_basis),
                "activities": activities_without_legal_basis,
                "description": "Processing activities without defined legal basis"
            })

class ComplianceError(Exception):
    """Compliance-related exception"""
    pass