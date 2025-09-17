"""
Evaluation Orchestrator

Central orchestration system for RAG evaluation workflows:
- Automated evaluation pipeline management
- RAGAS evaluation scheduling and execution
- Golden dataset integration and validation
- A/B testing coordination
- Performance monitoring and alerting
- Quality gate enforcement
- Automated reporting and notifications
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from pathlib import Path

# Import evaluation components
from ..core.ragas_engine import RAGASEvaluationEngine, RAGResponse, EvaluationResult
from ..core.golden_dataset import GoldenDatasetManager, GoldenDataset
from ..core.ab_testing import ABTestingFramework, ExperimentDesign, ExperimentMetric, MetricType

logger = logging.getLogger(__name__)

class EvaluationTrigger(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    MODEL_UPDATE = "model_update"
    DATA_UPDATE = "data_update"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    A_B_TEST_COMPLETION = "ab_test_completion"

class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class EvaluationJob:
    """Evaluation job configuration"""
    job_id: str
    name: str
    description: str
    trigger: EvaluationTrigger
    golden_dataset_id: str
    evaluation_config: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    status: EvaluationStatus = EvaluationStatus.PENDING
    result: Optional[EvaluationResult] = None
    error: Optional[str] = None

@dataclass
class QualityGate:
    """Quality gate configuration"""
    name: str
    metric_name: str
    threshold: float
    operator: str  # 'gte', 'lte', 'eq'
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str  # Python expression
    severity: str
    channels: List[str]  # email, slack, webhook
    enabled: bool = True

class EvaluationOrchestrator:
    """Orchestrates comprehensive RAG evaluation workflows"""

    def __init__(
        self,
        ragas_engine: Optional[RAGASEvaluationEngine] = None,
        golden_dataset_manager: Optional[GoldenDatasetManager] = None,
        ab_testing_framework: Optional[ABTestingFramework] = None,
        storage_path: str = "./evaluation_results"
    ):
        # Initialize components
        self.ragas_engine = ragas_engine or RAGASEvaluationEngine()
        self.golden_dataset_manager = golden_dataset_manager or GoldenDatasetManager()
        self.ab_testing_framework = ab_testing_framework or ABTestingFramework()

        # Storage
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Job management
        self.jobs: Dict[str, EvaluationJob] = {}
        self.job_queue: List[str] = []
        self.running_jobs: Dict[str, asyncio.Task] = {}

        # Quality gates and alerts
        self.quality_gates: List[QualityGate] = []
        self.alert_rules: List[AlertRule] = []

        # Scheduling
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        # Configuration
        self.config = {
            'max_concurrent_jobs': 3,
            'default_evaluation_timeout': 3600,  # 1 hour
            'quality_gate_enforcement': True,
            'auto_retry_failed_jobs': True,
            'max_retry_attempts': 2,
            'alert_cooldown_minutes': 15
        }

        # Metrics and monitoring
        self.metrics = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'average_evaluation_time': 0.0,
            'quality_gate_failures': 0,
            'alerts_triggered': 0
        }

        # Default quality gates
        self._setup_default_quality_gates()
        self._setup_default_alert_rules()

    def _setup_default_quality_gates(self):
        """Setup default quality gates"""
        default_gates = [
            QualityGate(
                name="Faithfulness Threshold",
                metric_name="faithfulness",
                threshold=0.85,
                operator="gte",
                severity="critical"
            ),
            QualityGate(
                name="Answer Relevancy Threshold",
                metric_name="answer_relevancy",
                threshold=0.80,
                operator="gte",
                severity="critical"
            ),
            QualityGate(
                name="Context Precision Threshold",
                metric_name="context_precision",
                threshold=0.75,
                operator="gte",
                severity="warning"
            ),
            QualityGate(
                name="Classification Accuracy Threshold",
                metric_name="classification_accuracy",
                threshold=0.90,
                operator="gte",
                severity="critical"
            )
        ]
        self.quality_gates.extend(default_gates)

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="Critical Quality Gate Failure",
                condition="quality_gate_failures > 0 and severity == 'critical'",
                severity="critical",
                channels=["email", "slack"]
            ),
            AlertRule(
                name="Performance Degradation",
                condition="metrics.get('faithfulness', 1.0) < 0.8",
                severity="warning",
                channels=["slack"]
            ),
            AlertRule(
                name="High Failure Rate",
                condition="failed_evaluations / max(total_evaluations, 1) > 0.2",
                severity="warning",
                channels=["email"]
            )
        ]
        self.alert_rules.extend(default_rules)

    async def schedule_evaluation(
        self,
        name: str,
        description: str,
        golden_dataset_id: str,
        trigger: EvaluationTrigger = EvaluationTrigger.MANUAL,
        scheduled_at: Optional[datetime] = None,
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a new evaluation job

        Args:
            name: Evaluation name
            description: Evaluation description
            golden_dataset_id: ID of golden dataset to use
            trigger: What triggered this evaluation
            scheduled_at: When to run (None for immediate)
            evaluation_config: Additional configuration

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job = EvaluationJob(
            job_id=job_id,
            name=name,
            description=description,
            trigger=trigger,
            golden_dataset_id=golden_dataset_id,
            evaluation_config=evaluation_config or {},
            scheduled_at=scheduled_at
        )

        self.jobs[job_id] = job

        if scheduled_at is None or scheduled_at <= datetime.utcnow():
            # Run immediately
            self.job_queue.append(job_id)
            logger.info(f"Evaluation job queued for immediate execution: {job_id}")
        else:
            logger.info(f"Evaluation job scheduled for {scheduled_at}: {job_id}")

        # Start scheduler if not running
        if not self.scheduler_running:
            await self.start_scheduler()

        return job_id

    async def run_evaluation_now(
        self,
        name: str,
        description: str,
        golden_dataset_id: str,
        rag_system_callable: Callable,
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Run evaluation immediately and return results

        Args:
            name: Evaluation name
            description: Evaluation description
            golden_dataset_id: Golden dataset ID
            rag_system_callable: Function to call RAG system
            evaluation_config: Additional configuration

        Returns:
            EvaluationResult
        """
        job_id = await self.schedule_evaluation(
            name=name,
            description=description,
            golden_dataset_id=golden_dataset_id,
            trigger=EvaluationTrigger.MANUAL,
            evaluation_config=evaluation_config
        )

        # Execute job immediately
        result = await self._execute_evaluation_job(job_id, rag_system_callable)

        return result

    async def _execute_evaluation_job(
        self,
        job_id: str,
        rag_system_callable: Callable
    ) -> EvaluationResult:
        """Execute a single evaluation job"""

        job = self.jobs[job_id]
        logger.info(f"Starting evaluation job: {job_id} - {job.name}")

        try:
            job.status = EvaluationStatus.RUNNING
            start_time = datetime.utcnow()

            # Load golden dataset
            golden_dataset = await self.golden_dataset_manager.load_dataset(job.golden_dataset_id)
            if not golden_dataset:
                raise ValueError(f"Golden dataset not found: {job.golden_dataset_id}")

            logger.info(f"Loaded golden dataset: {golden_dataset.name} ({len(golden_dataset.data_points)} data points)")

            # Prepare test queries and expected answers
            test_queries = [dp.query for dp in golden_dataset.data_points]
            expected_answers = [dp.expected_answer for dp in golden_dataset.data_points]
            expected_contexts = [dp.expected_contexts for dp in golden_dataset.data_points]

            # Run RAG system on test queries
            logger.info("Running RAG system on test queries...")
            rag_responses = []

            for i, query in enumerate(test_queries):
                try:
                    # Call RAG system
                    response = await rag_system_callable(query)

                    # Convert response to RAGResponse format
                    if isinstance(response, dict):
                        rag_response = RAGResponse(
                            answer=response.get('answer', ''),
                            retrieved_docs=response.get('retrieved_docs', []),
                            confidence=response.get('confidence', 0.0),
                            metadata=response.get('metadata', {})
                        )
                    else:
                        # Assume it's already a RAGResponse object
                        rag_response = response

                    rag_responses.append(rag_response)

                except Exception as e:
                    logger.warning(f"RAG system failed for query {i}: {str(e)}")
                    # Create empty response for failed queries
                    rag_responses.append(RAGResponse(
                        answer="Error: RAG system failed",
                        retrieved_docs=[],
                        confidence=0.0,
                        metadata={'error': str(e)}
                    ))

            # Run RAGAS evaluation
            logger.info("Running RAGAS evaluation...")
            evaluation_result = await self.ragas_engine.evaluate_rag_system(
                test_queries=test_queries,
                rag_responses=rag_responses,
                ground_truths=expected_answers,
                expected_contexts=expected_contexts
            )

            # Check quality gates
            quality_gate_results = await self._check_quality_gates(evaluation_result)
            evaluation_result.analysis['quality_gates'] = quality_gate_results

            # Update job status
            job.status = EvaluationStatus.COMPLETED
            job.result = evaluation_result

            # Calculate metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration, True, quality_gate_results)

            # Save results
            await self._save_evaluation_result(job_id, evaluation_result)

            # Check alert rules
            await self._check_alert_rules(evaluation_result, quality_gate_results)

            logger.info(f"Evaluation job completed: {job_id}")
            return evaluation_result

        except Exception as e:
            job.status = EvaluationStatus.FAILED
            job.error = str(e)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration, False, [])

            logger.error(f"Evaluation job failed: {job_id} - {str(e)}")
            raise

    async def _check_quality_gates(self, evaluation_result: EvaluationResult) -> List[Dict[str, Any]]:
        """Check evaluation results against quality gates"""

        quality_gate_results = []

        for gate in self.quality_gates:
            if not gate.enabled:
                continue

            metric_value = evaluation_result.metrics.get(gate.metric_name)
            if metric_value is None:
                continue

            # Check threshold
            passed = False
            if gate.operator == 'gte':
                passed = metric_value >= gate.threshold
            elif gate.operator == 'lte':
                passed = metric_value <= gate.threshold
            elif gate.operator == 'eq':
                passed = abs(metric_value - gate.threshold) < 0.001

            gate_result = {
                'name': gate.name,
                'metric_name': gate.metric_name,
                'metric_value': metric_value,
                'threshold': gate.threshold,
                'operator': gate.operator,
                'passed': passed,
                'severity': gate.severity
            }

            quality_gate_results.append(gate_result)

            if not passed:
                self.metrics['quality_gate_failures'] += 1
                logger.warning(f"Quality gate failed: {gate.name} - {gate.metric_name} {gate.operator} {gate.threshold} (actual: {metric_value})")

        return quality_gate_results

    async def _check_alert_rules(self, evaluation_result: EvaluationResult, quality_gate_results: List[Dict[str, Any]]):
        """Check if any alert rules should be triggered"""

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            try:
                # Create context for rule evaluation
                context = {
                    'metrics': evaluation_result.metrics,
                    'quality_gate_failures': sum(1 for qg in quality_gate_results if not qg['passed']),
                    'quality_gates': quality_gate_results,
                    'total_evaluations': self.metrics['total_evaluations'],
                    'failed_evaluations': self.metrics['failed_evaluations'],
                    'severity': None  # Will be set based on quality gate results
                }

                # Check if any critical quality gates failed
                critical_failures = [qg for qg in quality_gate_results if not qg['passed'] and qg['severity'] == 'critical']
                if critical_failures:
                    context['severity'] = 'critical'

                # Evaluate rule condition
                if eval(rule.condition, {"__builtins__": {}}, context):
                    await self._trigger_alert(rule, context, evaluation_result)

            except Exception as e:
                logger.warning(f"Alert rule evaluation failed: {rule.name} - {str(e)}")

    async def _trigger_alert(self, rule: AlertRule, context: Dict[str, Any], evaluation_result: EvaluationResult):
        """Trigger an alert"""

        self.metrics['alerts_triggered'] += 1

        alert_data = {
            'rule_name': rule.name,
            'severity': rule.severity,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context,
            'evaluation_metrics': evaluation_result.metrics,
            'recommendations': evaluation_result.recommendations
        }

        logger.warning(f"Alert triggered: {rule.name} (severity: {rule.severity})")

        # Send alerts to configured channels
        for channel in rule.channels:
            try:
                await self._send_alert(channel, alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert to {channel}: {str(e)}")

    async def _send_alert(self, channel: str, alert_data: Dict[str, Any]):
        """Send alert to specific channel"""

        if channel == "email":
            await self._send_email_alert(alert_data)
        elif channel == "slack":
            await self._send_slack_alert(alert_data)
        elif channel == "webhook":
            await self._send_webhook_alert(alert_data)
        else:
            logger.warning(f"Unknown alert channel: {channel}")

    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert (placeholder implementation)"""
        # In practice, integrate with email service
        logger.info(f"Email alert: {alert_data['rule_name']}")

    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send Slack alert (placeholder implementation)"""
        # In practice, integrate with Slack API
        logger.info(f"Slack alert: {alert_data['rule_name']}")

    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send webhook alert (placeholder implementation)"""
        # In practice, make HTTP POST to webhook URL
        logger.info(f"Webhook alert: {alert_data['rule_name']}")

    def _update_metrics(self, duration: float, success: bool, quality_gate_results: List[Dict[str, Any]]):
        """Update evaluation metrics"""

        self.metrics['total_evaluations'] += 1

        if success:
            self.metrics['successful_evaluations'] += 1
        else:
            self.metrics['failed_evaluations'] += 1

        # Update average evaluation time
        total = self.metrics['total_evaluations']
        current_avg = self.metrics['average_evaluation_time']
        self.metrics['average_evaluation_time'] = ((current_avg * (total - 1)) + duration) / total

    async def _save_evaluation_result(self, job_id: str, result: EvaluationResult):
        """Save evaluation result to storage"""

        result_file = self.storage_path / f"evaluation_{job_id}.json"

        # Convert result to serializable format
        result_data = {
            'job_id': job_id,
            'timestamp': result.timestamp.isoformat(),
            'metrics': result.metrics,
            'analysis': result.analysis,
            'quality_gates_passed': result.quality_gates_passed,
            'recommendations': result.recommendations
        }

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"Evaluation result saved: {result_file}")

    async def start_scheduler(self):
        """Start the evaluation scheduler"""

        if self.scheduler_running:
            return

        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Evaluation scheduler started")

    async def stop_scheduler(self):
        """Stop the evaluation scheduler"""

        if not self.scheduler_running:
            return

        self.scheduler_running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # Cancel running jobs
        for task in self.running_jobs.values():
            task.cancel()

        if self.running_jobs:
            await asyncio.gather(*self.running_jobs.values(), return_exceptions=True)

        logger.info("Evaluation scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""

        while self.scheduler_running:
            try:
                # Process scheduled jobs
                await self._process_scheduled_jobs()

                # Process job queue
                await self._process_job_queue()

                # Clean up completed jobs
                await self._cleanup_completed_jobs()

                # Wait before next iteration
                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_scheduled_jobs(self):
        """Process jobs scheduled for execution"""

        current_time = datetime.utcnow()

        for job in self.jobs.values():
            if (job.status == EvaluationStatus.PENDING and
                job.scheduled_at and
                job.scheduled_at <= current_time and
                job.job_id not in self.job_queue):

                self.job_queue.append(job.job_id)
                logger.info(f"Scheduled job queued: {job.job_id}")

    async def _process_job_queue(self):
        """Process jobs in the queue"""

        max_concurrent = self.config['max_concurrent_jobs']

        while (len(self.running_jobs) < max_concurrent and
               self.job_queue and
               self.scheduler_running):

            job_id = self.job_queue.pop(0)

            if job_id not in self.jobs:
                continue

            job = self.jobs[job_id]

            if job.status != EvaluationStatus.PENDING:
                continue

            # Start job execution
            try:
                # Note: In practice, you would inject the RAG system callable
                # For now, we'll use a placeholder
                async def placeholder_rag_system(query: str) -> RAGResponse:
                    return RAGResponse(
                        answer="Placeholder answer",
                        retrieved_docs=[],
                        confidence=0.5
                    )

                task = asyncio.create_task(
                    self._execute_evaluation_job(job_id, placeholder_rag_system)
                )
                self.running_jobs[job_id] = task

                logger.info(f"Started evaluation job: {job_id}")

            except Exception as e:
                job.status = EvaluationStatus.FAILED
                job.error = str(e)
                logger.error(f"Failed to start evaluation job {job_id}: {str(e)}")

    async def _cleanup_completed_jobs(self):
        """Clean up completed job tasks"""

        completed_jobs = []

        for job_id, task in self.running_jobs.items():
            if task.done():
                completed_jobs.append(job_id)

                try:
                    await task  # Ensure any exceptions are raised
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {str(e)}")
                    if job_id in self.jobs:
                        self.jobs[job_id].status = EvaluationStatus.FAILED
                        self.jobs[job_id].error = str(e)

        for job_id in completed_jobs:
            del self.running_jobs[job_id]

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job"""

        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        status = {
            'job_id': job.job_id,
            'name': job.name,
            'description': job.description,
            'status': job.status.value,
            'trigger': job.trigger.value,
            'created_at': job.created_at.isoformat(),
            'scheduled_at': job.scheduled_at.isoformat() if job.scheduled_at else None,
            'golden_dataset_id': job.golden_dataset_id
        }

        if job.result:
            status['result'] = {
                'metrics': job.result.metrics,
                'quality_gates_passed': job.result.quality_gates_passed,
                'overall_score': job.result.analysis.get('overall_score', 0.0),
                'recommendations_count': len(job.result.recommendations)
            }

        if job.error:
            status['error'] = job.error

        return status

    async def list_jobs(
        self,
        status_filter: Optional[EvaluationStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List evaluation jobs"""

        jobs = list(self.jobs.values())

        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        # Limit results
        jobs = jobs[:limit]

        # Convert to summary format
        job_summaries = []
        for job in jobs:
            summary = {
                'job_id': job.job_id,
                'name': job.name,
                'status': job.status.value,
                'trigger': job.trigger.value,
                'created_at': job.created_at.isoformat(),
                'golden_dataset_id': job.golden_dataset_id
            }

            if job.result and job.result.analysis:
                summary['overall_score'] = job.result.analysis.get('overall_score', 0.0)
                summary['quality_gates_passed'] = job.result.quality_gates_passed

            job_summaries.append(summary)

        return job_summaries

    def get_metrics(self) -> Dict[str, Any]:
        """Get evaluation orchestrator metrics"""

        success_rate = 0.0
        if self.metrics['total_evaluations'] > 0:
            success_rate = self.metrics['successful_evaluations'] / self.metrics['total_evaluations']

        return {
            'total_evaluations': self.metrics['total_evaluations'],
            'successful_evaluations': self.metrics['successful_evaluations'],
            'failed_evaluations': self.metrics['failed_evaluations'],
            'success_rate': success_rate,
            'average_evaluation_time_seconds': self.metrics['average_evaluation_time'],
            'quality_gate_failures': self.metrics['quality_gate_failures'],
            'alerts_triggered': self.metrics['alerts_triggered'],
            'jobs_in_queue': len(self.job_queue),
            'running_jobs': len(self.running_jobs),
            'scheduler_running': self.scheduler_running
        }

    async def setup_continuous_evaluation(
        self,
        golden_dataset_id: str,
        schedule_interval_hours: int = 24,
        performance_thresholds: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Setup continuous evaluation monitoring

        Args:
            golden_dataset_id: Golden dataset to use
            schedule_interval_hours: How often to run evaluations
            performance_thresholds: Custom performance thresholds

        Returns:
            Schedule ID for managing continuous evaluation
        """
        schedule_id = str(uuid.uuid4())

        # Setup recurring evaluation
        # This would typically integrate with a job scheduler like Celery or similar
        # For now, we'll implement a simple in-memory scheduler

        async def recurring_evaluation():
            while True:
                try:
                    await self.schedule_evaluation(
                        name=f"Continuous Evaluation {schedule_id}",
                        description=f"Automated evaluation every {schedule_interval_hours} hours",
                        golden_dataset_id=golden_dataset_id,
                        trigger=EvaluationTrigger.SCHEDULED
                    )

                    await asyncio.sleep(schedule_interval_hours * 3600)  # Convert to seconds

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Continuous evaluation failed: {str(e)}")
                    await asyncio.sleep(3600)  # Wait 1 hour on error

        # Start the recurring task
        asyncio.create_task(recurring_evaluation())

        logger.info(f"Continuous evaluation setup: {schedule_id} (every {schedule_interval_hours} hours)")
        return schedule_id

    async def create_evaluation_report(
        self,
        job_ids: List[str],
        report_format: str = "markdown"
    ) -> str:
        """
        Create comprehensive evaluation report

        Args:
            job_ids: List of job IDs to include in report
            report_format: Format of report ('markdown', 'html', 'json')

        Returns:
            Report content as string
        """
        if report_format == "markdown":
            return await self._create_markdown_report(job_ids)
        elif report_format == "html":
            return await self._create_html_report(job_ids)
        elif report_format == "json":
            return await self._create_json_report(job_ids)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

    async def _create_markdown_report(self, job_ids: List[str]) -> str:
        """Create markdown evaluation report"""

        report_lines = [
            "# RAG System Evaluation Report",
            f"\nGenerated on: {datetime.utcnow().isoformat()}",
            f"\nEvaluations included: {len(job_ids)}",
            "\n## Executive Summary\n"
        ]

        # Collect metrics from all jobs
        all_metrics = []
        successful_jobs = 0

        for job_id in job_ids:
            if job_id in self.jobs and self.jobs[job_id].result:
                all_metrics.append(self.jobs[job_id].result.metrics)
                successful_jobs += 1

        if all_metrics:
            # Calculate average metrics
            avg_metrics = {}
            for key in all_metrics[0].keys():
                values = [m.get(key, 0) for m in all_metrics if key in m]
                avg_metrics[key] = sum(values) / len(values) if values else 0

            report_lines.extend([
                f"- **Success Rate**: {successful_jobs}/{len(job_ids)} ({successful_jobs/len(job_ids)*100:.1f}%)",
                f"- **Average Faithfulness**: {avg_metrics.get('faithfulness', 0):.3f}",
                f"- **Average Answer Relevancy**: {avg_metrics.get('answer_relevancy', 0):.3f}",
                f"- **Average Context Precision**: {avg_metrics.get('context_precision', 0):.3f}",
                f"- **Average Context Recall**: {avg_metrics.get('context_recall', 0):.3f}",
                "\n## Detailed Results\n"
            ])

            # Individual job results
            for job_id in job_ids:
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    report_lines.append(f"### {job.name} ({job_id})")
                    report_lines.append(f"- **Status**: {job.status.value}")
                    report_lines.append(f"- **Trigger**: {job.trigger.value}")
                    report_lines.append(f"- **Created**: {job.created_at.isoformat()}")

                    if job.result:
                        report_lines.append("- **Metrics**:")
                        for metric, value in job.result.metrics.items():
                            report_lines.append(f"  - {metric}: {value:.3f}")

                        if job.result.recommendations:
                            report_lines.append("- **Recommendations**:")
                            for rec in job.result.recommendations:
                                report_lines.append(f"  - {rec}")

                    if job.error:
                        report_lines.append(f"- **Error**: {job.error}")

                    report_lines.append("")

        return "\n".join(report_lines)

    async def _create_html_report(self, job_ids: List[str]) -> str:
        """Create HTML evaluation report"""
        # Placeholder implementation
        markdown_content = await self._create_markdown_report(job_ids)
        return f"<html><body><pre>{markdown_content}</pre></body></html>"

    async def _create_json_report(self, job_ids: List[str]) -> str:
        """Create JSON evaluation report"""

        report_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'job_ids': job_ids,
            'summary': {},
            'jobs': []
        }

        # Collect job data
        for job_id in job_ids:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job_data = {
                    'job_id': job.job_id,
                    'name': job.name,
                    'status': job.status.value,
                    'trigger': job.trigger.value,
                    'created_at': job.created_at.isoformat(),
                    'metrics': job.result.metrics if job.result else None,
                    'quality_gates_passed': job.result.quality_gates_passed if job.result else None,
                    'recommendations': job.result.recommendations if job.result else None,
                    'error': job.error
                }
                report_data['jobs'].append(job_data)

        return json.dumps(report_data, indent=2)