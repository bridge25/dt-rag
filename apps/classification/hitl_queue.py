"""
Human-in-the-Loop Queue Management
=================================

Manages classification cases requiring human validation:
- Priority queue management
- Admin review interfaces
- Feedback collection and learning
- Approval/rejection workflows
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class HITLStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

class HITLPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class HITLItem:
    """Item in HITL queue"""
    item_id: str
    text: str
    original_classification: Dict[str, Any]
    confidence_score: float
    priority: HITLPriority
    status: HITLStatus
    created_at: datetime
    assigned_to: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    human_classification: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    review_time_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums and datetime objects
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.reviewed_at:
            data['reviewed_at'] = self.reviewed_at.isoformat()
        return data

@dataclass
class HITLMetrics:
    """HITL system metrics"""
    total_items: int
    pending_items: int
    in_review_items: int
    approved_items: int
    rejected_items: int
    average_review_time: float
    accuracy_improvement: float
    queue_efficiency: float

class HITLQueue:
    """HITL queue management system"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)
        self.items: Dict[str, HITLItem] = {}
        self.reviewers: Dict[str, Dict[str, Any]] = {}

    def _load_config(self, config: Optional[Dict]) -> Dict[str, Any]:
        """Load HITL configuration"""
        default_config = {
            "queue_limits": {
                "max_pending": 1000,
                "max_per_reviewer": 20,
                "auto_escalate_hours": 24
            },
            "priority_rules": {
                "high_confidence_disagreement": HITLPriority.HIGH,
                "business_critical_path": HITLPriority.URGENT,
                "new_domain_detection": HITLPriority.MEDIUM,
                "low_confidence": HITLPriority.LOW
            },
            "auto_approval": {
                "enabled": False,
                "confidence_threshold": 0.95,
                "agreement_threshold": 0.9
            },
            "feedback_learning": {
                "enabled": True,
                "min_feedback_length": 10,
                "update_rules_threshold": 0.8
            }
        }

        if config:
            for key, value in config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

        return default_config

    async def enqueue(self, text: str, classification_result: Dict[str, Any],
                     confidence_score: float, metadata: Optional[Dict] = None) -> str:
        """
        Add item to HITL queue

        Args:
            text: Original text to classify
            classification_result: Automatic classification result
            confidence_score: Confidence score
            metadata: Additional metadata

        Returns:
            Item ID for tracking
        """
        try:
            # Check queue limits
            if len(self.get_pending_items()) >= self.config["queue_limits"]["max_pending"]:
                logger.warning("HITL queue is full, cannot add new item")
                return None

            # Determine priority
            priority = self._calculate_priority(classification_result, confidence_score, metadata)

            # Create HITL item
            item_id = str(uuid.uuid4())
            item = HITLItem(
                item_id=item_id,
                text=text,
                original_classification=classification_result,
                confidence_score=confidence_score,
                priority=priority,
                status=HITLStatus.PENDING,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )

            self.items[item_id] = item

            logger.info(f"Added item {item_id} to HITL queue with priority {priority.name}")
            return item_id

        except Exception as e:
            logger.error(f"Failed to enqueue HITL item: {e}")
            return None

    def _calculate_priority(self, classification: Dict, confidence: float,
                          metadata: Optional[Dict]) -> HITLPriority:
        """Calculate priority for HITL item"""
        priority_rules = self.config["priority_rules"]

        # Check for business critical paths
        path = classification.get("path", [])
        if metadata and metadata.get("business_critical", False):
            return priority_rules["business_critical_path"]

        # Check for high confidence but classifier disagreement
        if (confidence > 0.8 and
            metadata and
            metadata.get("classifier_disagreement", False)):
            return priority_rules["high_confidence_disagreement"]

        # Check for new domain detection
        if any("unknown" in str(p).lower() for p in path):
            return priority_rules["new_domain_detection"]

        # Default based on confidence
        if confidence < 0.5:
            return priority_rules["low_confidence"]
        elif confidence < 0.7:
            return HITLPriority.MEDIUM
        else:
            return HITLPriority.LOW

    def get_pending_items(self) -> List[HITLItem]:
        """Get all pending items sorted by priority and age"""
        pending = [item for item in self.items.values()
                  if item.status == HITLStatus.PENDING]

        # Sort by priority (high to low) then by age (old to new)
        pending.sort(key=lambda x: (-x.priority.value, x.created_at))
        return pending

    def get_next_item_for_reviewer(self, reviewer_id: str) -> Optional[HITLItem]:
        """Get next item for specific reviewer"""
        # Check reviewer's current workload
        assigned_count = len([item for item in self.items.values()
                            if (item.assigned_to == reviewer_id and
                                item.status == HITLStatus.IN_REVIEW)])

        if assigned_count >= self.config["queue_limits"]["max_per_reviewer"]:
            return None

        # Get highest priority pending item
        pending_items = self.get_pending_items()
        if not pending_items:
            return None

        # Assign item to reviewer
        item = pending_items[0]
        item.assigned_to = reviewer_id
        item.status = HITLStatus.IN_REVIEW

        logger.info(f"Assigned item {item.item_id} to reviewer {reviewer_id}")
        return item

    async def submit_review(self, item_id: str, reviewer_id: str,
                          human_classification: Dict[str, Any],
                          feedback: Optional[str] = None) -> bool:
        """
        Submit human review for HITL item

        Args:
            item_id: Item being reviewed
            reviewer_id: ID of reviewing human
            human_classification: Human-provided classification
            feedback: Optional feedback text

        Returns:
            Success status
        """
        try:
            if item_id not in self.items:
                logger.error(f"HITL item {item_id} not found")
                return False

            item = self.items[item_id]

            if item.assigned_to != reviewer_id:
                logger.error(f"Item {item_id} not assigned to reviewer {reviewer_id}")
                return False

            if item.status != HITLStatus.IN_REVIEW:
                logger.error(f"Item {item_id} is not in review status")
                return False

            # Calculate review time
            review_time = (datetime.utcnow() - item.created_at).total_seconds()

            # Update item
            item.human_classification = human_classification
            item.feedback = feedback
            item.reviewed_at = datetime.utcnow()
            item.review_time_seconds = int(review_time)
            item.status = HITLStatus.APPROVED  # Could be REJECTED based on validation

            # Process feedback for learning
            if self.config["feedback_learning"]["enabled"] and feedback:
                await self._process_feedback_learning(item)

            logger.info(f"Review submitted for item {item_id} by {reviewer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to submit review: {e}")
            return False

    async def _process_feedback_learning(self, item: HITLItem):
        """Process feedback for system learning"""
        try:
            original = item.original_classification
            human = item.human_classification
            feedback = item.feedback

            # Analyze classification differences
            original_path = original.get("path", [])
            human_path = human.get("path", [])

            if original_path != human_path:
                # Classification was corrected
                logger.info(f"Classification correction: {original_path} -> {human_path}")

                # Update internal statistics (would trigger rule/model updates)
                correction_data = {
                    "original_path": original_path,
                    "corrected_path": human_path,
                    "confidence_score": item.confidence_score,
                    "feedback": feedback,
                    "text_sample": item.text[:200],
                    "correction_timestamp": datetime.utcnow().isoformat()
                }

                # In a real system, this would trigger:
                # 1. Rule weight adjustments
                # 2. Training data augmentation
                # 3. Model fine-tuning
                # 4. Pattern analysis

        except Exception as e:
            logger.error(f"Error processing feedback learning: {e}")

    def reject_classification(self, item_id: str, reviewer_id: str,
                            reason: str) -> bool:
        """Reject classification and mark for escalation"""
        try:
            if item_id not in self.items:
                return False

            item = self.items[item_id]
            if item.assigned_to != reviewer_id:
                return False

            item.status = HITLStatus.REJECTED
            item.feedback = reason
            item.reviewed_at = datetime.utcnow()

            # Escalate rejected items
            item.status = HITLStatus.ESCALATED

            logger.info(f"Item {item_id} rejected and escalated: {reason}")
            return True

        except Exception as e:
            logger.error(f"Error rejecting classification: {e}")
            return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        status_counts = {}
        for status in HITLStatus:
            status_counts[status.name] = len([
                item for item in self.items.values()
                if item.status == status
            ])

        priority_counts = {}
        for priority in HITLPriority:
            priority_counts[priority.name] = len([
                item for item in self.items.values()
                if item.priority == priority and item.status == HITLStatus.PENDING
            ])

        return {
            "total_items": len(self.items),
            "status_breakdown": status_counts,
            "pending_by_priority": priority_counts,
            "oldest_pending": self._get_oldest_pending_age(),
            "average_review_time": self._calculate_average_review_time()
        }

    def _get_oldest_pending_age(self) -> Optional[int]:
        """Get age of oldest pending item in hours"""
        pending = self.get_pending_items()
        if not pending:
            return None

        oldest = min(pending, key=lambda x: x.created_at)
        age_hours = (datetime.utcnow() - oldest.created_at).total_seconds() / 3600
        return int(age_hours)

    def _calculate_average_review_time(self) -> float:
        """Calculate average review time in minutes"""
        reviewed_items = [
            item for item in self.items.values()
            if item.review_time_seconds is not None
        ]

        if not reviewed_items:
            return 0.0

        total_time = sum(item.review_time_seconds for item in reviewed_items)
        return total_time / len(reviewed_items) / 60  # Convert to minutes

    async def auto_escalate_stale_items(self):
        """Auto-escalate items that have been pending too long"""
        escalate_threshold = timedelta(
            hours=self.config["queue_limits"]["auto_escalate_hours"]
        )

        stale_items = [
            item for item in self.items.values()
            if (item.status == HITLStatus.PENDING and
                datetime.utcnow() - item.created_at > escalate_threshold)
        ]

        for item in stale_items:
            item.status = HITLStatus.ESCALATED
            logger.warning(f"Auto-escalated stale item {item.item_id}")

    def get_reviewer_performance(self, reviewer_id: str) -> Dict[str, Any]:
        """Get performance metrics for specific reviewer"""
        reviewer_items = [
            item for item in self.items.values()
            if item.assigned_to == reviewer_id and item.reviewed_at
        ]

        if not reviewer_items:
            return {"error": "No reviewed items found for reviewer"}

        total_reviews = len(reviewer_items)
        approved_reviews = len([
            item for item in reviewer_items
            if item.status == HITLStatus.APPROVED
        ])

        avg_review_time = sum(
            item.review_time_seconds for item in reviewer_items
            if item.review_time_seconds
        ) / len(reviewer_items) if reviewer_items else 0

        return {
            "total_reviews": total_reviews,
            "approval_rate": approved_reviews / total_reviews if total_reviews > 0 else 0,
            "average_review_time_minutes": avg_review_time / 60,
            "reviews_today": len([
                item for item in reviewer_items
                if item.reviewed_at and
                item.reviewed_at.date() == datetime.utcnow().date()
            ])
        }

class HITLManager:
    """High-level HITL workflow manager"""

    def __init__(self, queue: HITLQueue):
        self.queue = queue
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def start_review_session(self, reviewer_id: str) -> Optional[Dict[str, Any]]:
        """Start review session for reviewer"""
        item = self.queue.get_next_item_for_reviewer(reviewer_id)
        if not item:
            return None

        session = {
            "session_id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "item_id": item.item_id,
            "started_at": datetime.utcnow(),
            "item": item.to_dict()
        }

        self.active_sessions[session["session_id"]] = session
        return session

    async def complete_review_session(self, session_id: str,
                                    classification: Dict[str, Any],
                                    feedback: Optional[str] = None) -> bool:
        """Complete review session"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        success = await self.queue.submit_review(
            session["item_id"],
            session["reviewer_id"],
            classification,
            feedback
        )

        if success:
            del self.active_sessions[session_id]

        return success

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for HITL dashboard"""
        queue_status = self.queue.get_queue_status()

        # Recent activity
        recent_items = sorted(
            self.queue.items.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:10]

        return {
            "queue_status": queue_status,
            "recent_activity": [item.to_dict() for item in recent_items],
            "active_sessions": len(self.active_sessions),
            "metrics": self._calculate_system_metrics()
        }

    def _calculate_system_metrics(self) -> HITLMetrics:
        """Calculate system-wide HITL metrics"""
        all_items = list(self.queue.items.values())

        if not all_items:
            return HITLMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 0.0)

        total = len(all_items)
        pending = len([i for i in all_items if i.status == HITLStatus.PENDING])
        in_review = len([i for i in all_items if i.status == HITLStatus.IN_REVIEW])
        approved = len([i for i in all_items if i.status == HITLStatus.APPROVED])
        rejected = len([i for i in all_items if i.status == HITLStatus.REJECTED])

        # Calculate average review time
        reviewed_items = [i for i in all_items if i.review_time_seconds]
        avg_review_time = (
            sum(i.review_time_seconds for i in reviewed_items) / len(reviewed_items)
            if reviewed_items else 0
        )

        # Calculate accuracy improvement (simplified)
        accuracy_improvement = approved / (approved + rejected) if (approved + rejected) > 0 else 0

        # Calculate queue efficiency
        completed = approved + rejected
        queue_efficiency = completed / total if total > 0 else 0

        return HITLMetrics(
            total_items=total,
            pending_items=pending,
            in_review_items=in_review,
            approved_items=approved,
            rejected_items=rejected,
            average_review_time=avg_review_time,
            accuracy_improvement=accuracy_improvement,
            queue_efficiency=queue_efficiency
        )