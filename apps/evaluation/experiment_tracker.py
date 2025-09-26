"""
A/B testing and experiment tracking for RAG system improvements

Provides:
- Experiment design and configuration management
- Traffic splitting and randomization
- Statistical analysis and significance testing
- Canary deployment monitoring
- Automated rollback based on quality degradation
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import random
import json

import numpy as np
from scipy import stats

from .models import (
    ExperimentConfig, ExperimentResults, EvaluationResult,
    EvaluationMetrics, ExperimentRun
)
from ..api.database import db_manager

logger = logging.getLogger(__name__)

@dataclass
class ExperimentAssignment:
    """User assignment to experiment group"""
    user_id: str
    experiment_id: str
    group: str  # 'control' or 'treatment'
    assigned_at: datetime

class ExperimentTracker:
    """A/B testing and canary deployment tracker"""

    def __init__(self):
        self.active_experiments = {}  # experiment_id -> ExperimentConfig
        self.user_assignments = {}    # user_id -> ExperimentAssignment
        self.experiment_data = {}     # experiment_id -> {'control': [], 'treatment': []}

        # Statistical parameters
        self.min_sample_size = 50
        self.significance_threshold = 0.05
        self.power_threshold = 0.8

        # Canary deployment settings
        self.canary_rollback_threshold = 0.1  # 10% degradation triggers rollback
        self.canary_monitor_window_minutes = 15

    async def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new A/B testing experiment"""
        try:
            async with db_manager.async_session() as session:
                # Store experiment in database
                experiment_run = ExperimentRun(
                    experiment_id=config.experiment_id,
                    name=config.name,
                    description=config.description,
                    control_config=config.control_config,
                    treatment_config=config.treatment_config,
                    significance_threshold=config.significance_threshold,
                    minimum_sample_size=config.minimum_sample_size,
                    power_threshold=config.power_threshold,
                    status='planning'
                )

                session.add(experiment_run)
                await session.commit()

                # Store in memory for active tracking
                self.active_experiments[config.experiment_id] = config
                self.experiment_data[config.experiment_id] = {'control': [], 'treatment': []}

                logger.info(f"Created experiment: {config.name} ({config.experiment_id})")
                return config.experiment_id

        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start running an experiment"""
        try:
            if experiment_id not in self.active_experiments:
                raise ValueError(f"Experiment {experiment_id} not found")

            async with db_manager.async_session() as session:
                from sqlalchemy import text
                query = text("""
                    UPDATE experiment_runs
                    SET status = 'running', start_time = :start_time
                    WHERE experiment_id = :experiment_id
                """)

                await session.execute(query, {
                    'experiment_id': experiment_id,
                    'start_time': datetime.utcnow()
                })
                await session.commit()

                logger.info(f"Started experiment: {experiment_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to start experiment {experiment_id}: {e}")
            return False

    async def stop_experiment(self, experiment_id: str, reason: str = "manual_stop") -> bool:
        """Stop a running experiment"""
        try:
            if experiment_id not in self.active_experiments:
                return False

            # Analyze final results
            results = await self.analyze_experiment_results(experiment_id)

            async with db_manager.async_session() as session:
                from sqlalchemy import text
                query = text("""
                    UPDATE experiment_runs
                    SET status = 'completed',
                        end_time = :end_time,
                        results = :results
                    WHERE experiment_id = :experiment_id
                """)

                await session.execute(query, {
                    'experiment_id': experiment_id,
                    'end_time': datetime.utcnow(),
                    'results': json.dumps(results.dict()) if results else '{}'
                })
                await session.commit()

                logger.info(f"Stopped experiment: {experiment_id} ({reason})")
                return True

        except Exception as e:
            logger.error(f"Failed to stop experiment {experiment_id}: {e}")
            return False

    def assign_user_to_experiment(self, user_id: str, experiment_id: str) -> str:
        """Assign user to control or treatment group"""
        if experiment_id not in self.active_experiments:
            return 'control'  # Default to control if experiment not found

        # Check if user already assigned
        if user_id in self.user_assignments:
            assignment = self.user_assignments[user_id]
            if assignment.experiment_id == experiment_id:
                return assignment.group

        # Deterministic assignment based on user_id hash
        user_hash = hash(f"{user_id}_{experiment_id}")
        group = 'treatment' if user_hash % 2 == 0 else 'control'

        # Store assignment
        assignment = ExperimentAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            group=group,
            assigned_at=datetime.utcnow()
        )
        self.user_assignments[user_id] = assignment

        return group

    async def record_experiment_result(
        self,
        experiment_id: str,
        user_id: str,
        evaluation: EvaluationResult
    ):
        """Record evaluation result for experiment analysis"""
        try:
            if experiment_id not in self.active_experiments:
                return

            # Get user's group assignment
            group = self.assign_user_to_experiment(user_id, experiment_id)

            # Store result
            result_data = {
                'timestamp': evaluation.timestamp,
                'metrics': evaluation.metrics.dict(),
                'quality_flags': evaluation.quality_flags,
                'user_id': user_id
            }

            self.experiment_data[experiment_id][group].append(result_data)

            # Check if we should analyze results (periodic check)
            if len(self.experiment_data[experiment_id]['control']) % 20 == 0:
                await self._periodic_experiment_analysis(experiment_id)

        except Exception as e:
            logger.error(f"Failed to record experiment result: {e}")

    async def analyze_experiment_results(self, experiment_id: str) -> Optional[ExperimentResults]:
        """Analyze experiment results and determine statistical significance"""
        try:
            if experiment_id not in self.experiment_data:
                return None

            data = self.experiment_data[experiment_id]
            control_data = data['control']
            treatment_data = data['treatment']

            if not control_data or not treatment_data:
                return None

            # Extract metrics for analysis
            metrics_to_analyze = ['faithfulness', 'context_precision', 'context_recall', 'answer_relevancy']
            metric_comparisons = {}

            overall_significant = False

            for metric in metrics_to_analyze:
                control_values = [
                    entry['metrics'][metric] for entry in control_data
                    if entry['metrics'].get(metric) is not None
                ]
                treatment_values = [
                    entry['metrics'][metric] for entry in treatment_data
                    if entry['metrics'].get(metric) is not None
                ]

                if len(control_values) >= self.min_sample_size and len(treatment_values) >= self.min_sample_size:
                    # Perform t-test
                    t_stat, p_value = stats.ttest_ind(control_values, treatment_values)

                    # Calculate effect size (Cohen's d)
                    control_mean = statistics.mean(control_values)
                    treatment_mean = statistics.mean(treatment_values)
                    pooled_std = np.sqrt(
                        (np.var(control_values, ddof=1) + np.var(treatment_values, ddof=1)) / 2
                    )
                    effect_size = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0

                    # Calculate confidence interval
                    se = np.sqrt(np.var(control_values, ddof=1)/len(control_values) +
                                np.var(treatment_values, ddof=1)/len(treatment_values))
                    ci_lower = (treatment_mean - control_mean) - 1.96 * se
                    ci_upper = (treatment_mean - control_mean) - 1.96 * se

                    is_significant = p_value < self.significance_threshold

                    if is_significant:
                        overall_significant = True

                    metric_comparisons[metric] = {
                        'control_mean': control_mean,
                        'treatment_mean': treatment_mean,
                        'p_value': p_value,
                        'effect_size': effect_size,
                        'is_significant': is_significant,
                        'improvement': treatment_mean > control_mean
                    }

            # Generate recommendation
            recommendation = self._generate_experiment_recommendation(
                metric_comparisons, overall_significant, len(control_data), len(treatment_data)
            )

            # Create confidence intervals
            confidence_intervals = {}
            for metric, comparison in metric_comparisons.items():
                if 'control_mean' in comparison and 'treatment_mean' in comparison:
                    diff = comparison['treatment_mean'] - comparison['control_mean']
                    # Simplified CI calculation
                    margin = abs(diff) * 0.1  # 10% margin
                    confidence_intervals[metric] = [diff - margin, diff + margin]

            return ExperimentResults(
                experiment_id=experiment_id,
                status='completed',
                start_time=datetime.utcnow() - timedelta(hours=1),  # Placeholder
                end_time=datetime.utcnow(),
                control_samples=len(control_data),
                treatment_samples=len(treatment_data),
                metric_comparisons=metric_comparisons,
                is_statistically_significant=overall_significant,
                confidence_interval=confidence_intervals,
                recommendation=recommendation,
                summary=self._generate_experiment_summary(metric_comparisons, overall_significant)
            )

        except Exception as e:
            logger.error(f"Failed to analyze experiment results: {e}")
            return None

    async def monitor_canary_deployment(
        self,
        canary_config: Dict[str, Any],
        traffic_percentage: float = 5.0,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Monitor canary deployment and detect quality degradation"""
        canary_id = f"canary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Create temporary experiment for canary
            config = ExperimentConfig(
                experiment_id=canary_id,
                name=f"Canary Deployment {canary_id}",
                control_config={"type": "production"},
                treatment_config=canary_config,
                significance_threshold=0.1,  # More sensitive for canary
                minimum_sample_size=30  # Smaller sample size for faster detection
            )

            await self.create_experiment(config)
            await self.start_experiment(canary_id)

            # Monitor for specified duration
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(minutes=duration_minutes)

            monitoring_results = []

            while datetime.utcnow() < end_time:
                # Wait for monitoring window
                await asyncio.sleep(self.canary_monitor_window_minutes * 60)

                # Analyze current results
                results = await self.analyze_experiment_results(canary_id)

                if results:
                    # Check for quality degradation
                    degradation_detected = self._detect_quality_degradation(results)

                    monitoring_results.append({
                        'timestamp': datetime.utcnow(),
                        'results': results,
                        'degradation_detected': degradation_detected
                    })

                    # Trigger rollback if degradation detected
                    if degradation_detected:
                        await self.stop_experiment(canary_id, "quality_degradation")

                        return {
                            'canary_id': canary_id,
                            'status': 'rolled_back',
                            'reason': 'quality_degradation_detected',
                            'monitoring_results': monitoring_results,
                            'recommendation': 'rollback_canary'
                        }

            # Complete monitoring period without issues
            await self.stop_experiment(canary_id, "monitoring_complete")

            final_results = await self.analyze_experiment_results(canary_id)

            return {
                'canary_id': canary_id,
                'status': 'monitoring_complete',
                'final_results': final_results,
                'monitoring_results': monitoring_results,
                'recommendation': 'proceed_with_rollout' if final_results and not self._detect_quality_degradation(final_results) else 'investigate_further'
            }

        except Exception as e:
            logger.error(f"Canary monitoring failed: {e}")
            return {
                'canary_id': canary_id,
                'status': 'error',
                'error': str(e),
                'recommendation': 'rollback_canary'
            }

    async def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get current status of an experiment"""
        try:
            if experiment_id not in self.active_experiments:
                return {'error': 'Experiment not found'}

            config = self.active_experiments[experiment_id]
            data = self.experiment_data.get(experiment_id, {'control': [], 'treatment': []})

            # Get current results if sufficient data
            current_results = None
            if len(data['control']) >= 10 and len(data['treatment']) >= 10:
                current_results = await self.analyze_experiment_results(experiment_id)

            return {
                'experiment_id': experiment_id,
                'name': config.name,
                'status': 'running',
                'control_samples': len(data['control']),
                'treatment_samples': len(data['treatment']),
                'current_results': current_results.dict() if current_results else None,
                'progress': {
                    'control_progress': len(data['control']) / config.minimum_sample_size,
                    'treatment_progress': len(data['treatment']) / config.minimum_sample_size
                }
            }

        except Exception as e:
            logger.error(f"Failed to get experiment status: {e}")
            return {'error': str(e)}

    async def _periodic_experiment_analysis(self, experiment_id: str):
        """Periodic analysis to check for early stopping conditions"""
        try:
            results = await self.analyze_experiment_results(experiment_id)

            if not results:
                return

            # Check for strong evidence of harm (early stop condition)
            harm_detected = False
            for metric, comparison in results.metric_comparisons.items():
                if (comparison.get('is_significant', False) and
                    comparison.get('treatment_mean', 0) < comparison.get('control_mean', 0) and
                    abs(comparison.get('effect_size', 0)) > 0.5):  # Large negative effect
                    harm_detected = True
                    break

            if harm_detected:
                logger.warning(f"Harm detected in experiment {experiment_id}, stopping early")
                await self.stop_experiment(experiment_id, "early_stop_harm")

        except Exception as e:
            logger.error(f"Periodic analysis failed for experiment {experiment_id}: {e}")

    def _generate_experiment_recommendation(
        self,
        metric_comparisons: Dict[str, Any],
        is_significant: bool,
        control_samples: int,
        treatment_samples: int
    ) -> str:
        """Generate experiment recommendation based on results"""

        min_sample_reached = (control_samples >= self.min_sample_size and
                             treatment_samples >= self.min_sample_size)

        if not min_sample_reached:
            return "continue_testing"

        if not is_significant:
            return "no_significant_difference"

        # Count positive and negative changes
        positive_changes = 0
        negative_changes = 0

        for metric, comparison in metric_comparisons.items():
            if comparison.get('is_significant', False):
                if comparison.get('improvement', False):
                    positive_changes += 1
                else:
                    negative_changes += 1

        if positive_changes > negative_changes:
            return "rollout_treatment"
        elif negative_changes > positive_changes:
            return "rollback_to_control"
        else:
            return "mixed_results_investigate"

    def _generate_experiment_summary(
        self,
        metric_comparisons: Dict[str, Any],
        is_significant: bool
    ) -> str:
        """Generate human-readable experiment summary"""

        if not metric_comparisons:
            return "Insufficient data for analysis"

        significant_improvements = []
        significant_degradations = []

        for metric, comparison in metric_comparisons.items():
            if comparison.get('is_significant', False):
                change_pct = ((comparison.get('treatment_mean', 0) - comparison.get('control_mean', 0)) /
                             max(comparison.get('control_mean', 0.001), 0.001)) * 100

                if comparison.get('improvement', False):
                    significant_improvements.append(f"{metric}: +{change_pct:.1f}%")
                else:
                    significant_degradations.append(f"{metric}: {change_pct:.1f}%")

        summary_parts = []

        if significant_improvements:
            summary_parts.append(f"Significant improvements in: {', '.join(significant_improvements)}")

        if significant_degradations:
            summary_parts.append(f"Significant degradations in: {', '.join(significant_degradations)}")

        if not significant_improvements and not significant_degradations:
            summary_parts.append("No statistically significant changes detected")

        return ". ".join(summary_parts)

    def _detect_quality_degradation(self, results: ExperimentResults) -> bool:
        """Detect if canary deployment shows quality degradation"""

        critical_metrics = ['faithfulness', 'answer_relevancy']

        for metric in critical_metrics:
            comparison = results.metric_comparisons.get(metric)
            if not comparison:
                continue

            # Check if there's significant degradation
            if (comparison.get('is_significant', False) and
                not comparison.get('improvement', False) and
                abs(comparison.get('effect_size', 0)) > self.canary_rollback_threshold):
                return True

        return False