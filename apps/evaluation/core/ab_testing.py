"""
A/B Testing Framework for RAG System Evaluation

Comprehensive A/B testing infrastructure for:
- Experiment design and randomization
- Statistical significance testing
- Effect size calculation and confidence intervals
- Power analysis and sample size estimation
- Multi-armed bandit optimization
- Automated experiment management
- Results interpretation and recommendations
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, mannwhitneyu, t, norm
import pandas as pd
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"

class ExperimentType(Enum):
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    BANDIT = "bandit"

class MetricType(Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    COUNT = "count"

@dataclass
class ExperimentMetric:
    """Definition of an experiment metric"""
    name: str
    type: MetricType
    description: str
    higher_is_better: bool = True
    minimum_detectable_effect: float = 0.05
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None

@dataclass
class ExperimentVariant:
    """Experiment variant configuration"""
    id: str
    name: str
    description: str
    traffic_allocation: float
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentDesign:
    """Complete experiment design specification"""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    primary_metric: ExperimentMetric
    secondary_metrics: List[ExperimentMetric]
    variants: List[ExperimentVariant]
    target_sample_size: int
    significance_level: float = 0.05
    statistical_power: float = 0.8
    expected_duration_days: float = 14
    randomization_unit: str = "user_id"
    stratification_factors: List[str] = field(default_factory=list)
    minimum_runtime_days: float = 7
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservationData:
    """Single observation in an experiment"""
    observation_id: str
    experiment_id: str
    variant_id: str
    randomization_unit_id: str
    metric_values: Dict[str, Union[float, int, str]]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StatisticalResult:
    """Statistical test result"""
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    interpretation: str
    power: Optional[float] = None

@dataclass
class ABTestResult:
    """A/B test analysis result"""
    experiment_id: str
    variant_comparisons: Dict[str, Dict[str, StatisticalResult]]
    overall_recommendation: str
    winning_variant: Optional[str]
    confidence_level: float
    sample_sizes: Dict[str, int]
    effect_sizes: Dict[str, float]
    business_impact: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ABTestingFramework:
    """A/B Testing framework for RAG system evaluation"""

    def __init__(self):
        self.experiments: Dict[str, ExperimentDesign] = {}
        self.observations: Dict[str, List[ObservationData]] = defaultdict(list)
        self.results: Dict[str, ABTestResult] = {}

        # Statistical configuration
        self.default_alpha = 0.05
        self.default_power = 0.80
        self.default_mde = 0.05  # Minimum detectable effect

        # Multiple testing corrections
        self.multiple_testing_methods = ['bonferroni', 'holm', 'benjamini_hochberg']

    async def design_experiment(
        self,
        name: str,
        description: str,
        primary_metric: ExperimentMetric,
        variants: List[ExperimentVariant],
        secondary_metrics: List[ExperimentMetric] = None,
        experiment_type: ExperimentType = ExperimentType.AB_TEST,
        significance_level: float = 0.05,
        statistical_power: float = 0.8,
        expected_runtime_days: float = 14,
        **kwargs
    ) -> ExperimentDesign:
        """
        Design a new experiment with proper statistical planning

        Args:
            name: Experiment name
            description: Experiment description
            primary_metric: Primary metric to optimize
            variants: List of variants to test
            secondary_metrics: Additional metrics to track
            experiment_type: Type of experiment
            significance_level: Alpha level for hypothesis testing
            statistical_power: Desired statistical power
            expected_runtime_days: Expected experiment duration

        Returns:
            ExperimentDesign object
        """
        logger.info(f"Designing experiment: {name}")

        # Generate experiment ID
        experiment_id = str(uuid.uuid4())

        # Validate variants
        self._validate_variants(variants)

        # Calculate sample size requirements
        sample_size = self._calculate_sample_size(
            primary_metric, significance_level, statistical_power
        )

        # Create experiment design
        design = ExperimentDesign(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            variants=variants,
            target_sample_size=sample_size,
            significance_level=significance_level,
            statistical_power=statistical_power,
            expected_duration_days=expected_runtime_days,
            **kwargs
        )

        # Store experiment
        self.experiments[experiment_id] = design

        logger.info(f"Experiment designed: {experiment_id}, target sample size: {sample_size}")
        return design

    def _validate_variants(self, variants: List[ExperimentVariant]):
        """Validate experiment variants"""

        if len(variants) < 2:
            raise ValueError("At least 2 variants required for A/B testing")

        # Check traffic allocation
        total_allocation = sum(v.traffic_allocation for v in variants)
        if abs(total_allocation - 1.0) > 0.001:
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")

        # Check for duplicate variant IDs
        variant_ids = [v.id for v in variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("Variant IDs must be unique")

    def _calculate_sample_size(
        self,
        metric: ExperimentMetric,
        alpha: float,
        power: float
    ) -> int:
        """Calculate required sample size for experiment"""

        if metric.type == MetricType.CONTINUOUS:
            # For continuous metrics, use t-test sample size calculation
            effect_size = metric.minimum_detectable_effect

            if metric.baseline_value and metric.baseline_value > 0:
                # Convert to Cohen's d if baseline is available
                std_estimate = metric.baseline_value * 0.2  # Assume 20% CV
                cohens_d = effect_size / std_estimate
            else:
                cohens_d = effect_size  # Assume effect size is already standardized

            # Two-sided t-test sample size calculation
            z_alpha = norm.ppf(1 - alpha / 2)
            z_beta = norm.ppf(power)

            n_per_group = ((z_alpha + z_beta) ** 2) * 2 / (cohens_d ** 2)
            return max(int(np.ceil(n_per_group)) * 2, 100)  # Minimum 50 per group

        elif metric.type == MetricType.BINARY:
            # For binary metrics, use proportion test sample size calculation
            p1 = metric.baseline_value or 0.1  # Default 10% baseline
            p2 = p1 + metric.minimum_detectable_effect

            p_pooled = (p1 + p2) / 2

            z_alpha = norm.ppf(1 - alpha / 2)
            z_beta = norm.ppf(power)

            n_per_group = ((z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) +
                           z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / ((p2 - p1) ** 2)

            return max(int(np.ceil(n_per_group)) * 2, 200)  # Minimum 100 per group

        else:
            # For other metric types, use conservative estimate
            return 1000

    async def record_observation(
        self,
        experiment_id: str,
        variant_id: str,
        randomization_unit_id: str,
        metric_values: Dict[str, Union[float, int, str]],
        metadata: Dict[str, Any] = None
    ):
        """Record an observation for an experiment"""

        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        observation = ObservationData(
            observation_id=str(uuid.uuid4()),
            experiment_id=experiment_id,
            variant_id=variant_id,
            randomization_unit_id=randomization_unit_id,
            metric_values=metric_values,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        self.observations[experiment_id].append(observation)

    async def analyze_experiment(
        self,
        experiment_id: str,
        interim_analysis: bool = False
    ) -> ABTestResult:
        """
        Analyze experiment results with comprehensive statistical testing

        Args:
            experiment_id: Experiment identifier
            interim_analysis: Whether this is an interim analysis

        Returns:
            ABTestResult with comprehensive analysis
        """
        logger.info(f"Analyzing experiment: {experiment_id}")

        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        design = self.experiments[experiment_id]
        observations = self.observations[experiment_id]

        if not observations:
            raise ValueError(f"No observations found for experiment {experiment_id}")

        # Prepare data for analysis
        df = self._prepare_analysis_data(observations, design)

        # Perform statistical tests
        variant_comparisons = {}

        # Compare each variant against control (assuming first variant is control)
        control_variant = design.variants[0]

        for variant in design.variants[1:]:
            comparison_key = f"{control_variant.id}_vs_{variant.id}"

            # Primary metric analysis
            primary_result = await self._compare_variants(
                df, control_variant.id, variant.id, design.primary_metric, design.significance_level
            )

            # Secondary metrics analysis
            secondary_results = {}
            for metric in design.secondary_metrics:
                secondary_results[metric.name] = await self._compare_variants(
                    df, control_variant.id, variant.id, metric, design.significance_level
                )

            variant_comparisons[comparison_key] = {
                'primary': primary_result,
                'secondary': secondary_results
            }

        # Apply multiple testing correction if needed
        if len(design.secondary_metrics) > 0:
            variant_comparisons = self._apply_multiple_testing_correction(
                variant_comparisons, design.significance_level
            )

        # Determine overall recommendation
        recommendation, winning_variant = self._generate_recommendation(
            variant_comparisons, design, interim_analysis
        )

        # Calculate business impact
        business_impact = self._calculate_business_impact(df, design, variant_comparisons)

        # Sample sizes by variant
        sample_sizes = df.groupby('variant_id').size().to_dict()

        # Effect sizes
        effect_sizes = {}
        for comparison_key, results in variant_comparisons.items():
            effect_sizes[comparison_key] = results['primary'].effect_size

        result = ABTestResult(
            experiment_id=experiment_id,
            variant_comparisons=variant_comparisons,
            overall_recommendation=recommendation,
            winning_variant=winning_variant,
            confidence_level=1 - design.significance_level,
            sample_sizes=sample_sizes,
            effect_sizes=effect_sizes,
            business_impact=business_impact
        )

        # Store result
        self.results[experiment_id] = result

        logger.info(f"Experiment analysis completed: {experiment_id}")
        return result

    def _prepare_analysis_data(
        self,
        observations: List[ObservationData],
        design: ExperimentDesign
    ) -> pd.DataFrame:
        """Prepare observation data for statistical analysis"""

        records = []
        for obs in observations:
            record = {
                'observation_id': obs.observation_id,
                'variant_id': obs.variant_id,
                'randomization_unit_id': obs.randomization_unit_id,
                'timestamp': obs.timestamp,
                **obs.metric_values
            }
            records.append(record)

        df = pd.DataFrame(records)

        # Aggregate by randomization unit if needed
        if design.randomization_unit == "user_id":
            # Group by user and variant, taking mean of metrics
            metric_columns = [design.primary_metric.name] + [m.name for m in design.secondary_metrics]

            agg_dict = {}
            for metric_name in metric_columns:
                if metric_name in df.columns:
                    metric = next((m for m in [design.primary_metric] + design.secondary_metrics if m.name == metric_name), None)
                    if metric and metric.type in [MetricType.CONTINUOUS, MetricType.COUNT]:
                        agg_dict[metric_name] = 'mean'
                    else:
                        agg_dict[metric_name] = 'first'  # For binary/categorical

            if agg_dict:
                df = df.groupby(['randomization_unit_id', 'variant_id']).agg(agg_dict).reset_index()

        return df

    async def _compare_variants(
        self,
        df: pd.DataFrame,
        control_id: str,
        treatment_id: str,
        metric: ExperimentMetric,
        alpha: float
    ) -> StatisticalResult:
        """Compare two variants using appropriate statistical test"""

        # Extract data for comparison
        control_data = df[df['variant_id'] == control_id][metric.name].dropna()
        treatment_data = df[df['variant_id'] == treatment_id][metric.name].dropna()

        if len(control_data) == 0 or len(treatment_data) == 0:
            return StatisticalResult(
                test_name="insufficient_data",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                is_significant=False,
                interpretation="Insufficient data for comparison"
            )

        # Choose appropriate statistical test based on metric type
        if metric.type == MetricType.CONTINUOUS:
            return await self._continuous_metric_test(control_data, treatment_data, alpha, metric.name)
        elif metric.type == MetricType.BINARY:
            return await self._binary_metric_test(control_data, treatment_data, alpha, metric.name)
        elif metric.type == MetricType.COUNT:
            return await self._count_metric_test(control_data, treatment_data, alpha, metric.name)
        else:
            return await self._categorical_metric_test(control_data, treatment_data, alpha, metric.name)

    async def _continuous_metric_test(
        self,
        control_data: pd.Series,
        treatment_data: pd.Series,
        alpha: float,
        metric_name: str
    ) -> StatisticalResult:
        """Statistical test for continuous metrics"""

        # Check for normality (simplified)
        control_mean = control_data.mean()
        treatment_mean = treatment_data.mean()

        # Perform Welch's t-test (unequal variances)
        statistic, p_value = stats.ttest_ind(treatment_data, control_data, equal_var=False)

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(control_data) - 1) * control_data.var() +
                             (len(treatment_data) - 1) * treatment_data.var()) /
                             (len(control_data) + len(treatment_data) - 2))

        cohens_d = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0

        # Calculate confidence interval for difference in means
        se_diff = np.sqrt(control_data.var() / len(control_data) +
                         treatment_data.var() / len(treatment_data))

        df = len(control_data) + len(treatment_data) - 2
        t_critical = t.ppf(1 - alpha / 2, df)
        margin_error = t_critical * se_diff

        diff = treatment_mean - control_mean
        ci_lower = diff - margin_error
        ci_upper = diff + margin_error

        # Determine significance
        is_significant = p_value < alpha

        # Generate interpretation
        if is_significant:
            direction = "increase" if diff > 0 else "decrease"
            interpretation = f"Significant {direction} of {abs(diff):.3f} in {metric_name} (p={p_value:.3f})"
        else:
            interpretation = f"No significant difference in {metric_name} (p={p_value:.3f})"

        return StatisticalResult(
            test_name="welch_t_test",
            statistic=statistic,
            p_value=p_value,
            effect_size=cohens_d,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            interpretation=interpretation
        )

    async def _binary_metric_test(
        self,
        control_data: pd.Series,
        treatment_data: pd.Series,
        alpha: float,
        metric_name: str
    ) -> StatisticalResult:
        """Statistical test for binary metrics"""

        # Convert to proportions
        control_success = control_data.sum()
        control_total = len(control_data)
        treatment_success = treatment_data.sum()
        treatment_total = len(treatment_data)

        control_rate = control_success / control_total
        treatment_rate = treatment_success / treatment_total

        # Chi-square test for independence
        contingency_table = [[control_success, control_total - control_success],
                           [treatment_success, treatment_total - treatment_success]]

        chi2_stat, p_value, _, _ = chi2_contingency(contingency_table)

        # Calculate effect size (odds ratio and relative risk)
        if control_rate > 0 and control_rate < 1 and treatment_rate > 0 and treatment_rate < 1:
            odds_ratio = (treatment_rate / (1 - treatment_rate)) / (control_rate / (1 - control_rate))
            effect_size = np.log(odds_ratio)  # Log odds ratio
        else:
            effect_size = treatment_rate - control_rate  # Risk difference

        # Calculate confidence interval for rate difference
        se_diff = np.sqrt(control_rate * (1 - control_rate) / control_total +
                         treatment_rate * (1 - treatment_rate) / treatment_total)

        z_critical = norm.ppf(1 - alpha / 2)
        margin_error = z_critical * se_diff

        diff = treatment_rate - control_rate
        ci_lower = diff - margin_error
        ci_upper = diff + margin_error

        is_significant = p_value < alpha

        if is_significant:
            direction = "increase" if diff > 0 else "decrease"
            interpretation = f"Significant {direction} of {abs(diff):.3f} in {metric_name} rate (p={p_value:.3f})"
        else:
            interpretation = f"No significant difference in {metric_name} rate (p={p_value:.3f})"

        return StatisticalResult(
            test_name="chi_square_test",
            statistic=chi2_stat,
            p_value=p_value,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            interpretation=interpretation
        )

    async def _count_metric_test(
        self,
        control_data: pd.Series,
        treatment_data: pd.Series,
        alpha: float,
        metric_name: str
    ) -> StatisticalResult:
        """Statistical test for count metrics"""

        # Use Mann-Whitney U test (non-parametric)
        statistic, p_value = mannwhitneyu(treatment_data, control_data, alternative='two-sided')

        # Calculate effect size (rank-biserial correlation)
        n1, n2 = len(control_data), len(treatment_data)
        effect_size = 1 - (2 * statistic) / (n1 * n2)

        # Calculate medians for interpretation
        control_median = control_data.median()
        treatment_median = treatment_data.median()
        diff = treatment_median - control_median

        # Approximate confidence interval (simplified)
        ci_lower = diff - 1.96 * np.sqrt((control_data.var() + treatment_data.var()) / 2)
        ci_upper = diff + 1.96 * np.sqrt((control_data.var() + treatment_data.var()) / 2)

        is_significant = p_value < alpha

        if is_significant:
            direction = "increase" if diff > 0 else "decrease"
            interpretation = f"Significant {direction} of {abs(diff):.3f} in {metric_name} median (p={p_value:.3f})"
        else:
            interpretation = f"No significant difference in {metric_name} median (p={p_value:.3f})"

        return StatisticalResult(
            test_name="mann_whitney_u",
            statistic=statistic,
            p_value=p_value,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            interpretation=interpretation
        )

    async def _categorical_metric_test(
        self,
        control_data: pd.Series,
        treatment_data: pd.Series,
        alpha: float,
        metric_name: str
    ) -> StatisticalResult:
        """Statistical test for categorical metrics"""

        # Chi-square test for distribution differences
        control_counts = control_data.value_counts()
        treatment_counts = treatment_data.value_counts()

        # Align categories
        all_categories = set(control_counts.index) | set(treatment_counts.index)

        control_aligned = [control_counts.get(cat, 0) for cat in all_categories]
        treatment_aligned = [treatment_counts.get(cat, 0) for cat in all_categories]

        if len(all_categories) < 2:
            return StatisticalResult(
                test_name="insufficient_categories",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                is_significant=False,
                interpretation="Insufficient categories for comparison"
            )

        # Perform chi-square test
        contingency_table = [control_aligned, treatment_aligned]
        chi2_stat, p_value, _, _ = chi2_contingency(contingency_table)

        # Effect size (Cramér's V)
        n = len(control_data) + len(treatment_data)
        cramers_v = np.sqrt(chi2_stat / (n * (min(len(all_categories), 2) - 1)))

        is_significant = p_value < alpha

        if is_significant:
            interpretation = f"Significant difference in {metric_name} distribution (p={p_value:.3f}, Cramér's V={cramers_v:.3f})"
        else:
            interpretation = f"No significant difference in {metric_name} distribution (p={p_value:.3f})"

        return StatisticalResult(
            test_name="chi_square_distribution",
            statistic=chi2_stat,
            p_value=p_value,
            effect_size=cramers_v,
            confidence_interval=(0.0, 1.0),  # Cramér's V range
            is_significant=is_significant,
            interpretation=interpretation
        )

    def _apply_multiple_testing_correction(
        self,
        variant_comparisons: Dict[str, Dict[str, StatisticalResult]],
        alpha: float,
        method: str = 'benjamini_hochberg'
    ) -> Dict[str, Dict[str, StatisticalResult]]:
        """Apply multiple testing correction to secondary metrics"""

        # Collect all p-values from secondary metrics
        p_values = []
        comparison_keys = []

        for comparison_key, results in variant_comparisons.items():
            for metric_name, result in results['secondary'].items():
                p_values.append(result.p_value)
                comparison_keys.append((comparison_key, metric_name))

        if not p_values:
            return variant_comparisons

        # Apply correction
        if method == 'bonferroni':
            corrected_alpha = alpha / len(p_values)
            corrected_p_values = p_values  # Don't adjust p-values, adjust alpha
        elif method == 'benjamini_hochberg':
            # Benjamini-Hochberg procedure
            sorted_indices = np.argsort(p_values)
            corrected_p_values = p_values.copy()

            for i, idx in enumerate(sorted_indices):
                corrected_p_values[idx] = min(1.0, p_values[idx] * len(p_values) / (i + 1))

            corrected_alpha = alpha
        else:
            corrected_alpha = alpha
            corrected_p_values = p_values

        # Update results with corrected significance
        corrected_comparisons = variant_comparisons.copy()

        for i, (comparison_key, metric_name) in enumerate(comparison_keys):
            original_result = corrected_comparisons[comparison_key]['secondary'][metric_name]

            # Update significance based on correction
            is_significant = corrected_p_values[i] < corrected_alpha if method == 'benjamini_hochberg' else p_values[i] < corrected_alpha

            # Create updated result
            updated_result = StatisticalResult(
                test_name=f"{original_result.test_name}_corrected",
                statistic=original_result.statistic,
                p_value=corrected_p_values[i] if method == 'benjamini_hochberg' else original_result.p_value,
                effect_size=original_result.effect_size,
                confidence_interval=original_result.confidence_interval,
                is_significant=is_significant,
                interpretation=f"{original_result.interpretation} (multiple testing corrected)"
            )

            corrected_comparisons[comparison_key]['secondary'][metric_name] = updated_result

        return corrected_comparisons

    def _generate_recommendation(
        self,
        variant_comparisons: Dict[str, Dict[str, StatisticalResult]],
        design: ExperimentDesign,
        interim_analysis: bool
    ) -> Tuple[str, Optional[str]]:
        """Generate overall recommendation and identify winning variant"""

        primary_results = []
        winning_variants = []

        # Analyze primary metric results
        for comparison_key, results in variant_comparisons.items():
            primary_result = results['primary']

            if primary_result.is_significant:
                # Extract treatment variant from comparison key
                treatment_variant = comparison_key.split('_vs_')[1]

                # Check if improvement is in the right direction
                if design.primary_metric.higher_is_better:
                    if primary_result.effect_size > 0:  # Positive effect
                        winning_variants.append((treatment_variant, primary_result.effect_size))
                else:
                    if primary_result.effect_size < 0:  # Negative effect (improvement for "lower is better")
                        winning_variants.append((treatment_variant, abs(primary_result.effect_size)))

                primary_results.append(primary_result)

        # Determine recommendation
        if not winning_variants:
            recommendation = "No significant improvement detected. Consider continuing with control variant or extending experiment duration."
            winning_variant = None
        elif len(winning_variants) == 1:
            winning_variant = winning_variants[0][0]
            effect_size = winning_variants[0][1]

            if interim_analysis:
                recommendation = f"Preliminary results show {winning_variant} performing significantly better (effect size: {effect_size:.3f}). Consider early stopping if business impact is sufficient."
            else:
                recommendation = f"Recommend implementing {winning_variant}. Significant improvement detected with effect size: {effect_size:.3f}."
        else:
            # Multiple winning variants - choose the best one
            best_variant = max(winning_variants, key=lambda x: x[1])
            winning_variant = best_variant[0]
            effect_size = best_variant[1]

            recommendation = f"Multiple variants show improvement, but {winning_variant} has the largest effect size ({effect_size:.3f}). Recommend implementing {winning_variant}."

        # Add cautions for interim analysis
        if interim_analysis:
            recommendation += " Note: This is an interim analysis. Consider statistical stopping rules and business context before making final decisions."

        return recommendation, winning_variant

    def _calculate_business_impact(
        self,
        df: pd.DataFrame,
        design: ExperimentDesign,
        variant_comparisons: Dict[str, Dict[str, StatisticalResult]]
    ) -> Dict[str, Any]:
        """Calculate business impact metrics"""

        business_impact = {
            'primary_metric_impact': {},
            'secondary_metrics_impact': {},
            'confidence_intervals': {},
            'practical_significance': {}
        }

        # Calculate impact for primary metric
        primary_metric = design.primary_metric

        for comparison_key, results in variant_comparisons.items():
            primary_result = results['primary']
            treatment_variant = comparison_key.split('_vs_')[1]

            # Calculate absolute and relative impact
            control_mean = df[df['variant_id'] == design.variants[0].id][primary_metric.name].mean()
            treatment_mean = df[df['variant_id'] == treatment_variant][primary_metric.name].mean()

            absolute_impact = treatment_mean - control_mean
            relative_impact = (absolute_impact / control_mean * 100) if control_mean != 0 else 0

            business_impact['primary_metric_impact'][treatment_variant] = {
                'absolute_change': absolute_impact,
                'relative_change_percent': relative_impact,
                'baseline_value': control_mean,
                'new_value': treatment_mean
            }

            # Store confidence intervals
            business_impact['confidence_intervals'][treatment_variant] = {
                'primary_metric': primary_result.confidence_interval
            }

            # Assess practical significance
            if primary_metric.minimum_detectable_effect:
                is_practically_significant = abs(primary_result.effect_size) >= primary_metric.minimum_detectable_effect
                business_impact['practical_significance'][treatment_variant] = is_practically_significant

        return business_impact

    async def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get current status of an experiment"""

        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        design = self.experiments[experiment_id]
        observations = self.observations[experiment_id]

        # Calculate current metrics
        current_sample_size = len(observations)
        target_sample_size = design.target_sample_size
        progress_percent = (current_sample_size / target_sample_size * 100) if target_sample_size > 0 else 0

        # Sample size by variant
        variant_counts = Counter(obs.variant_id for obs in observations)

        # Calculate experiment duration
        if observations:
            start_time = min(obs.timestamp for obs in observations)
            current_duration = (datetime.utcnow() - start_time).days
        else:
            current_duration = 0

        # Statistical power assessment
        if current_sample_size > 50:  # Minimum for power calculation
            estimated_power = self._estimate_current_power(design, observations)
        else:
            estimated_power = None

        status = {
            'experiment_id': experiment_id,
            'name': design.name,
            'status': 'running' if observations else 'not_started',
            'progress': {
                'current_sample_size': current_sample_size,
                'target_sample_size': target_sample_size,
                'progress_percent': min(progress_percent, 100),
                'variant_distribution': dict(variant_counts)
            },
            'timing': {
                'current_duration_days': current_duration,
                'target_duration_days': design.expected_duration_days,
                'minimum_runtime_days': design.minimum_runtime_days
            },
            'statistical_status': {
                'estimated_power': estimated_power,
                'significance_level': design.significance_level,
                'ready_for_analysis': current_sample_size >= 100 and current_duration >= design.minimum_runtime_days
            }
        }

        return status

    def _estimate_current_power(self, design: ExperimentDesign, observations: List[ObservationData]) -> float:
        """Estimate current statistical power based on observed data"""

        try:
            # Prepare data
            df = self._prepare_analysis_data(observations, design)

            if len(df) < 50:  # Insufficient data
                return 0.0

            # Calculate observed effect size
            control_id = design.variants[0].id
            treatment_ids = [v.id for v in design.variants[1:]]

            if not treatment_ids:
                return 0.0

            treatment_id = treatment_ids[0]  # Use first treatment for power calculation

            control_data = df[df['variant_id'] == control_id][design.primary_metric.name].dropna()
            treatment_data = df[df['variant_id'] == treatment_id][design.primary_metric.name].dropna()

            if len(control_data) < 10 or len(treatment_data) < 10:
                return 0.0

            # Calculate observed effect size (Cohen's d)
            pooled_std = np.sqrt(((len(control_data) - 1) * control_data.var() +
                                 (len(treatment_data) - 1) * treatment_data.var()) /
                                 (len(control_data) + len(treatment_data) - 2))

            if pooled_std == 0:
                return 0.0

            observed_cohens_d = abs((treatment_data.mean() - control_data.mean()) / pooled_std)

            # Calculate power using observed effect size
            n_per_group = min(len(control_data), len(treatment_data))
            z_alpha = norm.ppf(1 - design.significance_level / 2)
            z_beta = (observed_cohens_d * np.sqrt(n_per_group / 2)) - z_alpha

            power = norm.cdf(z_beta)
            return max(0.0, min(1.0, power))

        except Exception as e:
            logger.warning(f"Power estimation failed: {str(e)}")
            return 0.0

    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of all experiments"""

        summary = {
            'total_experiments': len(self.experiments),
            'experiments_by_status': {},
            'recent_results': [],
            'performance_overview': {}
        }

        # Count by status
        status_counts = defaultdict(int)
        for exp_id in self.experiments:
            if exp_id in self.results:
                status_counts['completed'] += 1
            elif self.observations[exp_id]:
                status_counts['running'] += 1
            else:
                status_counts['planned'] += 1

        summary['experiments_by_status'] = dict(status_counts)

        # Recent results (last 5)
        recent_results = sorted(
            [(exp_id, result) for exp_id, result in self.results.items()],
            key=lambda x: x[1].timestamp,
            reverse=True
        )[:5]

        for exp_id, result in recent_results:
            summary['recent_results'].append({
                'experiment_id': exp_id,
                'name': self.experiments[exp_id].name,
                'winning_variant': result.winning_variant,
                'recommendation': result.overall_recommendation[:100] + "..." if len(result.overall_recommendation) > 100 else result.overall_recommendation,
                'timestamp': result.timestamp.isoformat()
            })

        # Performance overview
        if self.results:
            successful_experiments = sum(1 for result in self.results.values() if result.winning_variant is not None)
            summary['performance_overview'] = {
                'success_rate': successful_experiments / len(self.results),
                'total_completed': len(self.results),
                'significant_improvements': successful_experiments
            }

        return summary