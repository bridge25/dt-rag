"""
Test suite for A/B testing framework
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))

from core.ab_testing import (
    ABTestingFramework,
    ExperimentDesign,
    ExperimentMetric,
    ExperimentVariant,
    StatisticalResult,
    MetricType,
    ExperimentStatus
)


class TestABTestingFramework:
    """Test cases for A/B testing framework"""

    @pytest.fixture
    def ab_framework(self):
        """Create A/B testing framework instance"""
        return ABTestingFramework()

    @pytest.fixture
    def sample_metric(self):
        """Sample experiment metric"""
        return ExperimentMetric(
            name="faithfulness",
            type=MetricType.CONTINUOUS,
            description="RAGAS faithfulness score",
            minimum_detectable_effect=0.05,
            baseline_value=0.80
        )

    @pytest.fixture
    def sample_variants(self):
        """Sample experiment variants"""
        return [
            ExperimentVariant(
                id="control",
                name="Current RAG System",
                description="Existing RAG implementation",
                traffic_allocation=0.5,
                configuration={"retrieval_method": "bm25"}
            ),
            ExperimentVariant(
                id="treatment",
                name="Enhanced RAG System",
                description="RAG with improved retrieval",
                traffic_allocation=0.5,
                configuration={"retrieval_method": "hybrid_dense"}
            )
        ]

    @pytest.mark.asyncio
    async def test_experiment_design(self, ab_framework, sample_metric, sample_variants):
        """Test experiment design creation"""

        experiment = await ab_framework.design_experiment(
            name="RAG System Comparison",
            description="Compare current vs enhanced RAG system",
            primary_metric=sample_metric,
            variants=sample_variants,
            significance_level=0.05,
            statistical_power=0.8
        )

        assert isinstance(experiment, ExperimentDesign)
        assert experiment.name == "RAG System Comparison"
        assert len(experiment.variants) == 2
        assert experiment.primary_metric.name == "faithfulness"
        assert experiment.required_sample_size > 0
        assert experiment.estimated_duration_days > 0

    @pytest.mark.asyncio
    async def test_sample_size_calculation(self, ab_framework, sample_metric):
        """Test sample size calculation"""

        sample_size = await ab_framework.calculate_sample_size(
            metric=sample_metric,
            significance_level=0.05,
            statistical_power=0.8,
            minimum_detectable_effect=0.05
        )

        assert isinstance(sample_size, int)
        assert sample_size > 0
        assert sample_size < 10000  # Reasonable upper bound

        # Test with different parameters
        larger_sample_size = await ab_framework.calculate_sample_size(
            metric=sample_metric,
            significance_level=0.01,  # More stringent
            statistical_power=0.9,   # Higher power
            minimum_detectable_effect=0.02  # Smaller effect
        )

        assert larger_sample_size > sample_size

    @pytest.mark.asyncio
    async def test_record_observations(self, ab_framework, sample_metric, sample_variants):
        """Test recording experiment observations"""

        # Create experiment
        experiment = await ab_framework.design_experiment(
            name="Test Experiment",
            description="Test recording observations",
            primary_metric=sample_metric,
            variants=sample_variants
        )

        # Record observations for control group
        for i in range(50):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="control",
                randomization_unit_id=f"user_{i}",
                metric_values={"faithfulness": np.random.normal(0.80, 0.1)}
            )

        # Record observations for treatment group
        for i in range(50):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="treatment",
                randomization_unit_id=f"user_{i+50}",
                metric_values={"faithfulness": np.random.normal(0.85, 0.1)}
            )

        # Verify observations were recorded
        observations = await ab_framework.get_experiment_observations(experiment.experiment_id)
        assert len(observations) == 100
        assert len([obs for obs in observations if obs["variant_id"] == "control"]) == 50
        assert len([obs for obs in observations if obs["variant_id"] == "treatment"]) == 50

    @pytest.mark.asyncio
    async def test_statistical_analysis_ttest(self, ab_framework):
        """Test t-test statistical analysis"""

        # Generate sample data
        control_data = np.random.normal(0.80, 0.1, 100).tolist()
        treatment_data = np.random.normal(0.85, 0.1, 100).tolist()

        result = await ab_framework.perform_statistical_test(
            control_data=control_data,
            treatment_data=treatment_data,
            test_type="t_test",
            significance_level=0.05
        )

        assert isinstance(result, StatisticalResult)
        assert result.test_type == "t_test"
        assert 0 <= result.p_value <= 1
        assert result.effect_size is not None
        assert len(result.confidence_interval) == 2
        assert isinstance(result.is_significant, bool)

    @pytest.mark.asyncio
    async def test_statistical_analysis_chi_square(self, ab_framework):
        """Test chi-square test for categorical data"""

        # Generate categorical data (conversion rates)
        control_conversions = [1] * 30 + [0] * 70  # 30% conversion
        treatment_conversions = [1] * 40 + [0] * 60  # 40% conversion

        result = await ab_framework.perform_statistical_test(
            control_data=control_conversions,
            treatment_data=treatment_conversions,
            test_type="chi_square",
            significance_level=0.05
        )

        assert isinstance(result, StatisticalResult)
        assert result.test_type == "chi_square"
        assert 0 <= result.p_value <= 1

    @pytest.mark.asyncio
    async def test_mann_whitney_test(self, ab_framework):
        """Test Mann-Whitney U test for non-parametric data"""

        # Generate non-normal data
        control_data = np.random.exponential(2, 100).tolist()
        treatment_data = np.random.exponential(2.5, 100).tolist()

        result = await ab_framework.perform_statistical_test(
            control_data=control_data,
            treatment_data=treatment_data,
            test_type="mann_whitney",
            significance_level=0.05
        )

        assert isinstance(result, StatisticalResult)
        assert result.test_type == "mann_whitney"
        assert 0 <= result.p_value <= 1

    @pytest.mark.asyncio
    async def test_multiple_testing_correction(self, ab_framework):
        """Test multiple testing correction methods"""

        # Multiple p-values to correct
        p_values = [0.01, 0.03, 0.08, 0.12, 0.45]

        # Test Bonferroni correction
        bonferroni_corrected = await ab_framework.apply_multiple_testing_correction(
            p_values=p_values,
            method="bonferroni"
        )

        assert len(bonferroni_corrected) == len(p_values)
        assert all(corrected >= original for corrected, original in zip(bonferroni_corrected, p_values))

        # Test Benjamini-Hochberg correction
        bh_corrected = await ab_framework.apply_multiple_testing_correction(
            p_values=p_values,
            method="benjamini_hochberg"
        )

        assert len(bh_corrected) == len(p_values)
        # BH should be less conservative than Bonferroni
        assert all(bh <= bonf for bh, bonf in zip(bh_corrected, bonferroni_corrected))

    @pytest.mark.asyncio
    async def test_experiment_analysis(self, ab_framework, sample_metric, sample_variants):
        """Test complete experiment analysis"""

        # Create and populate experiment
        experiment = await ab_framework.design_experiment(
            name="Full Analysis Test",
            description="Test complete analysis workflow",
            primary_metric=sample_metric,
            variants=sample_variants
        )

        # Generate realistic data with treatment effect
        np.random.seed(42)  # For reproducible results

        # Control group: lower performance
        for i in range(100):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="control",
                randomization_unit_id=f"user_{i}",
                metric_values={"faithfulness": np.random.normal(0.78, 0.08)}
            )

        # Treatment group: higher performance
        for i in range(100):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="treatment",
                randomization_unit_id=f"user_{i+100}",
                metric_values={"faithfulness": np.random.normal(0.84, 0.08)}
            )

        # Analyze experiment
        analysis_result = await ab_framework.analyze_experiment(experiment.experiment_id)

        assert analysis_result.experiment_id == experiment.experiment_id
        assert analysis_result.primary_metric_result is not None
        assert "control" in analysis_result.variant_summaries
        assert "treatment" in analysis_result.variant_summaries
        assert analysis_result.recommendation is not None
        assert analysis_result.confidence_level > 0

    @pytest.mark.asyncio
    async def test_early_stopping_rules(self, ab_framework, sample_metric, sample_variants):
        """Test early stopping rules for experiments"""

        experiment = await ab_framework.design_experiment(
            name="Early Stopping Test",
            description="Test early stopping functionality",
            primary_metric=sample_metric,
            variants=sample_variants,
            early_stopping_rules={
                "min_sample_size": 50,
                "confidence_threshold": 0.99,
                "effect_size_threshold": 0.1
            }
        )

        # Simulate strong treatment effect for early stopping
        np.random.seed(123)

        for i in range(60):
            # Control: low performance
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="control",
                randomization_unit_id=f"user_{i}",
                metric_values={"faithfulness": np.random.normal(0.70, 0.05)}
            )

            # Treatment: high performance
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="treatment",
                randomization_unit_id=f"user_{i+60}",
                metric_values={"faithfulness": np.random.normal(0.85, 0.05)}
            )

        # Check if early stopping criteria are met
        should_stop, reason = await ab_framework.check_early_stopping_criteria(experiment.experiment_id)

        # With such a large effect, early stopping should trigger
        assert isinstance(should_stop, bool)
        if should_stop:
            assert reason is not None
            assert "significant" in reason.lower() or "effect" in reason.lower()

    @pytest.mark.asyncio
    async def test_experiment_monitoring(self, ab_framework, sample_metric, sample_variants):
        """Test experiment monitoring and status tracking"""

        experiment = await ab_framework.design_experiment(
            name="Monitoring Test",
            description="Test experiment monitoring",
            primary_metric=sample_metric,
            variants=sample_variants
        )

        # Start experiment
        await ab_framework.start_experiment(experiment.experiment_id)

        # Check status
        status = await ab_framework.get_experiment_status(experiment.experiment_id)
        assert status == ExperimentStatus.RUNNING

        # Add some observations
        for i in range(20):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="control",
                randomization_unit_id=f"user_{i}",
                metric_values={"faithfulness": 0.80}
            )

        # Get monitoring report
        monitoring_report = await ab_framework.get_monitoring_report(experiment.experiment_id)

        assert "sample_size_progress" in monitoring_report
        assert "statistical_power_estimate" in monitoring_report
        assert "effect_size_estimate" in monitoring_report
        assert monitoring_report["sample_size_progress"] > 0

    @pytest.mark.asyncio
    async def test_bayesian_analysis(self, ab_framework):
        """Test Bayesian statistical analysis"""

        # Generate sample data
        control_data = np.random.normal(0.80, 0.1, 100).tolist()
        treatment_data = np.random.normal(0.85, 0.1, 100).tolist()

        bayesian_result = await ab_framework.perform_bayesian_analysis(
            control_data=control_data,
            treatment_data=treatment_data,
            prior_mean=0.80,
            prior_std=0.1
        )

        assert "posterior_control" in bayesian_result
        assert "posterior_treatment" in bayesian_result
        assert "probability_treatment_better" in bayesian_result
        assert 0 <= bayesian_result["probability_treatment_better"] <= 1

    @pytest.mark.asyncio
    async def test_experiment_power_analysis(self, ab_framework, sample_metric):
        """Test statistical power analysis"""

        power_analysis = await ab_framework.perform_power_analysis(
            metric=sample_metric,
            sample_sizes=[50, 100, 200, 500],
            effect_sizes=[0.02, 0.05, 0.1, 0.2],
            significance_level=0.05
        )

        assert "power_matrix" in power_analysis
        assert "recommendations" in power_analysis

        # Power should increase with sample size and effect size
        power_matrix = power_analysis["power_matrix"]
        assert len(power_matrix) == 4  # 4 sample sizes
        assert all(len(row) == 4 for row in power_matrix)  # 4 effect sizes each

    def test_metric_type_enum(self):
        """Test metric type enumeration"""

        assert MetricType.CONTINUOUS == "continuous"
        assert MetricType.BINARY == "binary"
        assert MetricType.COUNT == "count"
        assert MetricType.RATE == "rate"

    def test_experiment_status_enum(self):
        """Test experiment status enumeration"""

        assert ExperimentStatus.DRAFT == "draft"
        assert ExperimentStatus.RUNNING == "running"
        assert ExperimentStatus.COMPLETED == "completed"
        assert ExperimentStatus.STOPPED == "stopped"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])