#!/usr/bin/env python3
"""
RAG Evaluation Runner Script

Command-line interface for running RAG evaluations:
- RAGAS evaluation execution
- Golden dataset validation
- A/B testing management
- Performance benchmarking
- Automated reporting
"""

import asyncio
import click
import json
import logging
from pathlib import Path
from typing import Optional, List
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.ragas_engine import RAGASEvaluationEngine, RAGResponse
from core.golden_dataset import GoldenDatasetManager
from core.ab_testing import ABTestingFramework, ExperimentMetric, ExperimentVariant, MetricType
from orchestrator.evaluation_orchestrator import EvaluationOrchestrator, EvaluationTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
def cli(verbose: bool, config: Optional[str]):
    """RAG Evaluation Framework CLI"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if config:
        # Load configuration file
        with open(config, 'r') as f:
            global_config = json.load(f)
            logger.info(f"Loaded configuration from {config}")

@cli.group()
def dataset():
    """Golden dataset management commands"""
    pass

@dataset.command()
@click.argument('name')
@click.argument('description')
@click.argument('data_file', type=click.Path(exists=True))
@click.option('--version', default='1.0', help='Dataset version')
@click.option('--validate/--no-validate', default=True, help='Validate dataset after creation')
def create(name: str, description: str, data_file: str, version: str, validate: bool):
    """Create a golden dataset from JSON file"""

    async def _create_dataset():
        # Load data from file
        with open(data_file, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'data_points' in data:
            data_points = data['data_points']
        elif isinstance(data, list):
            data_points = data
        else:
            raise ValueError("Invalid data format. Expected list or dict with 'data_points' key")

        # Create dataset manager
        manager = GoldenDatasetManager()

        # Create dataset
        dataset = await manager.create_golden_dataset(
            name=name,
            description=description,
            raw_data=data_points,
            version=version,
            validate_quality=validate
        )

        # Display results
        stats = manager.get_dataset_statistics(dataset)

        click.echo(f"\n✅ Dataset created successfully!")
        click.echo(f"Dataset ID: {dataset.id}")
        click.echo(f"Name: {dataset.name}")
        click.echo(f"Version: {dataset.version}")
        click.echo(f"Data points: {len(dataset.data_points)}")
        click.echo(f"Quality score: {dataset.quality_metrics.get('overall_quality', 'N/A'):.3f}")

        click.echo(f"\n📊 Statistics:")
        click.echo(f"Validated: {stats.validated_count}/{stats.total_size}")
        click.echo(f"Average query length: {stats.avg_query_length:.1f} words")
        click.echo(f"Average answer length: {stats.avg_answer_length:.1f} words")
        click.echo(f"Domains: {list(stats.domain_distribution.keys())}")

        return dataset.id

    dataset_id = asyncio.run(_create_dataset())
    click.echo(f"\n💾 Dataset saved with ID: {dataset_id}")

@dataset.command()
def list():
    """List all golden datasets"""

    async def _list_datasets():
        manager = GoldenDatasetManager()
        datasets = await manager.list_datasets()

        if not datasets:
            click.echo("No datasets found.")
            return

        click.echo(f"\n📚 Found {len(datasets)} dataset(s):")
        click.echo("-" * 80)

        for ds in datasets:
            quality_score = ds.get('quality_metrics', {}).get('overall_quality', 'N/A')
            if isinstance(quality_score, (int, float)):
                quality_str = f"{quality_score:.3f}"
            else:
                quality_str = str(quality_score)

            click.echo(f"ID: {ds['id']}")
            click.echo(f"Name: {ds['name']}")
            click.echo(f"Version: {ds['version']}")
            click.echo(f"Created: {ds['created_at']}")
            click.echo(f"Data points: {ds['data_points_count']}")
            click.echo(f"Quality: {quality_str}")
            click.echo("-" * 80)

    asyncio.run(_list_datasets())

@dataset.command()
@click.argument('dataset_id')
def validate(dataset_id: str):
    """Validate a golden dataset"""

    async def _validate_dataset():
        manager = GoldenDatasetManager()

        # Load dataset
        dataset = await manager.load_dataset(dataset_id)
        if not dataset:
            click.echo(f"❌ Dataset {dataset_id} not found")
            return

        # Validate dataset
        click.echo(f"🔍 Validating dataset: {dataset.name}")
        result = await manager.validate_dataset(dataset)

        # Display results
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        click.echo(f"\n{status} - Quality Score: {result.quality_score:.3f}")

        if result.errors:
            click.echo(f"\n🚨 Errors ({len(result.errors)}):")
            for error in result.errors:
                click.echo(f"  - {error}")

        if result.warnings:
            click.echo(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                click.echo(f"  - {warning}")

        if result.recommendations:
            click.echo(f"\n💡 Recommendations ({len(result.recommendations)}):")
            for rec in result.recommendations:
                click.echo(f"  - {rec}")

    asyncio.run(_validate_dataset())

@dataset.command()
@click.argument('dataset_id')
@click.option('--train-ratio', default=0.7, help='Training set ratio')
@click.option('--val-ratio', default=0.15, help='Validation set ratio')
@click.option('--test-ratio', default=0.15, help='Test set ratio')
def split(dataset_id: str, train_ratio: float, val_ratio: float, test_ratio: float):
    """Split a dataset into train/validation/test sets"""

    async def _split_dataset():
        manager = GoldenDatasetManager()

        # Load dataset
        dataset = await manager.load_dataset(dataset_id)
        if not dataset:
            click.echo(f"❌ Dataset {dataset_id} not found")
            return

        # Split dataset
        click.echo(f"✂️  Splitting dataset: {dataset.name}")
        train_ds, val_ds, test_ds = manager.split_dataset(
            dataset, train_ratio, val_ratio, test_ratio
        )

        # Save split datasets
        await manager.save_dataset(train_ds)
        await manager.save_dataset(val_ds)
        await manager.save_dataset(test_ds)

        click.echo(f"\n✅ Dataset split completed:")
        click.echo(f"Train: {train_ds.id} ({len(train_ds.data_points)} points)")
        click.echo(f"Validation: {val_ds.id} ({len(val_ds.data_points)} points)")
        click.echo(f"Test: {test_ds.id} ({len(test_ds.data_points)} points)")

    asyncio.run(_split_dataset())

@cli.group()
def evaluate():
    """Evaluation commands"""
    pass

@evaluate.command()
@click.argument('name')
@click.argument('dataset_id')
@click.option('--description', default='', help='Evaluation description')
@click.option('--config-file', type=click.Path(exists=True), help='Evaluation configuration file')
@click.option('--immediate/--scheduled', default=False, help='Run immediately or schedule')
def run(name: str, dataset_id: str, description: str, config_file: Optional[str], immediate: bool):
    """Run RAGAS evaluation"""

    async def _run_evaluation():
        # Load configuration if provided
        eval_config = {}
        if config_file:
            with open(config_file, 'r') as f:
                eval_config = json.load(f)

        # Create orchestrator
        orchestrator = EvaluationOrchestrator()
        await orchestrator.start_scheduler()

        try:
            if immediate:
                click.echo(f"🚀 Running immediate evaluation: {name}")

                # Mock RAG system for demo
                async def mock_rag_system(query: str) -> RAGResponse:
                    return RAGResponse(
                        answer=f"This is a mock answer for: {query}",
                        retrieved_docs=[{
                            "chunk_id": "mock_1",
                            "text": f"Mock context for {query}",
                            "score": 0.8,
                            "source": {"title": "Mock Doc", "url": "mock://doc"}
                        }],
                        confidence=0.75
                    )

                result = await orchestrator.run_evaluation_now(
                    name=name,
                    description=description,
                    golden_dataset_id=dataset_id,
                    rag_system_callable=mock_rag_system,
                    evaluation_config=eval_config
                )

                # Display results
                click.echo(f"\n✅ Evaluation completed!")
                click.echo(f"Overall score: {result.analysis.get('overall_score', 0.0):.3f}")
                click.echo(f"Quality gates passed: {result.quality_gates_passed}")

                click.echo(f"\n📊 Metrics:")
                for metric, value in result.metrics.items():
                    click.echo(f"  {metric}: {value:.3f}")

                if result.recommendations:
                    click.echo(f"\n💡 Recommendations:")
                    for rec in result.recommendations:
                        click.echo(f"  - {rec}")

            else:
                # Schedule evaluation
                job_id = await orchestrator.schedule_evaluation(
                    name=name,
                    description=description,
                    golden_dataset_id=dataset_id,
                    trigger=EvaluationTrigger.MANUAL,
                    evaluation_config=eval_config
                )

                click.echo(f"📅 Evaluation scheduled with ID: {job_id}")

                # Wait for completion or timeout
                click.echo("⏳ Waiting for evaluation to complete...")
                timeout = 300  # 5 minutes
                elapsed = 0

                while elapsed < timeout:
                    await asyncio.sleep(5)
                    elapsed += 5

                    status = await orchestrator.get_job_status(job_id)
                    if status['status'] == 'completed':
                        click.echo(f"✅ Evaluation completed!")
                        if 'result' in status:
                            result = status['result']
                            click.echo(f"Overall score: {result.get('overall_score', 'N/A')}")
                            click.echo(f"Quality gates passed: {result.get('quality_gates_passed', 'N/A')}")
                        break
                    elif status['status'] == 'failed':
                        click.echo(f"❌ Evaluation failed: {status.get('error', 'Unknown error')}")
                        break
                    elif elapsed % 30 == 0:  # Update every 30 seconds
                        click.echo(f"⏳ Still running... ({elapsed}s elapsed)")

                if elapsed >= timeout:
                    click.echo(f"⏰ Timeout waiting for evaluation to complete")

        finally:
            await orchestrator.stop_scheduler()

    asyncio.run(_run_evaluation())

@evaluate.command()
@click.option('--status', type=click.Choice(['pending', 'running', 'completed', 'failed']), help='Filter by status')
@click.option('--limit', default=10, help='Maximum number of results')
def list(status: Optional[str], limit: int):
    """List evaluation jobs"""

    async def _list_evaluations():
        orchestrator = EvaluationOrchestrator()

        # Convert status string to enum if provided
        status_filter = None
        if status:
            from orchestrator.evaluation_orchestrator import EvaluationStatus
            status_filter = EvaluationStatus(status.upper())

        jobs = await orchestrator.list_jobs(status_filter, limit)

        if not jobs:
            click.echo("No evaluation jobs found.")
            return

        click.echo(f"\n📋 Found {len(jobs)} evaluation job(s):")
        click.echo("-" * 80)

        for job in jobs:
            click.echo(f"ID: {job['job_id']}")
            click.echo(f"Name: {job['name']}")
            click.echo(f"Status: {job['status']}")
            click.echo(f"Trigger: {job['trigger']}")
            click.echo(f"Created: {job['created_at']}")

            if 'overall_score' in job:
                click.echo(f"Score: {job['overall_score']:.3f}")
            if 'quality_gates_passed' in job:
                click.echo(f"Quality gates: {'✅ PASSED' if job['quality_gates_passed'] else '❌ FAILED'}")

            click.echo("-" * 80)

    asyncio.run(_list_evaluations())

@evaluate.command()
@click.argument('job_id')
def status(job_id: str):
    """Get evaluation job status"""

    async def _get_status():
        orchestrator = EvaluationOrchestrator()

        try:
            status = await orchestrator.get_job_status(job_id)

            click.echo(f"\n📊 Evaluation Status:")
            click.echo(f"Job ID: {status['job_id']}")
            click.echo(f"Name: {status['name']}")
            click.echo(f"Description: {status['description']}")
            click.echo(f"Status: {status['status']}")
            click.echo(f"Trigger: {status['trigger']}")
            click.echo(f"Created: {status['created_at']}")

            if status.get('scheduled_at'):
                click.echo(f"Scheduled: {status['scheduled_at']}")

            if 'result' in status:
                result = status['result']
                click.echo(f"\n📈 Results:")
                click.echo(f"Overall score: {result.get('overall_score', 'N/A')}")
                click.echo(f"Quality gates passed: {result.get('quality_gates_passed', 'N/A')}")

                if 'metrics' in result:
                    click.echo(f"\n📊 Metrics:")
                    for metric, value in result['metrics'].items():
                        click.echo(f"  {metric}: {value:.3f}")

                if result.get('recommendations_count', 0) > 0:
                    click.echo(f"\n💡 Recommendations: {result['recommendations_count']} available")

            if status.get('error'):
                click.echo(f"\n❌ Error: {status['error']}")

        except ValueError as e:
            click.echo(f"❌ Error: {str(e)}")

    asyncio.run(_get_status())

@cli.group()
def abtest():
    """A/B testing commands"""
    pass

@abtest.command()
@click.argument('config_file', type=click.Path(exists=True))
def create(config_file: str):
    """Create A/B test from configuration file"""

    async def _create_abtest():
        with open(config_file, 'r') as f:
            config = json.load(f)

        framework = ABTestingFramework()

        # Parse configuration
        primary_metric = ExperimentMetric(
            name=config['primary_metric']['name'],
            type=MetricType(config['primary_metric']['type']),
            description=config['primary_metric']['description'],
            higher_is_better=config['primary_metric'].get('higher_is_better', True),
            minimum_detectable_effect=config['primary_metric'].get('minimum_detectable_effect', 0.05)
        )

        variants = []
        for v_config in config['variants']:
            variant = ExperimentVariant(
                id=v_config['id'],
                name=v_config['name'],
                description=v_config['description'],
                traffic_allocation=v_config['traffic_allocation'],
                config=v_config.get('config', {})
            )
            variants.append(variant)

        # Create experiment
        design = await framework.design_experiment(
            name=config['name'],
            description=config['description'],
            primary_metric=primary_metric,
            variants=variants,
            significance_level=config.get('significance_level', 0.05),
            statistical_power=config.get('statistical_power', 0.8)
        )

        click.echo(f"✅ A/B test created successfully!")
        click.echo(f"Experiment ID: {design.experiment_id}")
        click.echo(f"Name: {design.name}")
        click.echo(f"Target sample size: {design.target_sample_size}")
        click.echo(f"Expected duration: {design.expected_duration_days:.1f} days")

        click.echo(f"\n🧪 Variants:")
        for variant in design.variants:
            click.echo(f"  - {variant.name} ({variant.id}): {variant.traffic_allocation*100:.1f}% traffic")

    asyncio.run(_create_abtest())

@abtest.command()
@click.argument('experiment_id')
@click.option('--interim', is_flag=True, help='Run interim analysis')
def analyze(experiment_id: str, interim: bool):
    """Analyze A/B test results"""

    async def _analyze_abtest():
        framework = ABTestingFramework()

        try:
            result = await framework.analyze_experiment(experiment_id, interim_analysis=interim)

            click.echo(f"📊 A/B Test Analysis Results")
            click.echo(f"Experiment ID: {result.experiment_id}")
            click.echo(f"Analysis Type: {'Interim' if interim else 'Final'}")
            click.echo(f"Confidence Level: {result.confidence_level*100:.1f}%")

            if result.winning_variant:
                click.echo(f"🏆 Winning Variant: {result.winning_variant}")

            click.echo(f"\n📋 Recommendation:")
            click.echo(f"{result.overall_recommendation}")

            click.echo(f"\n📈 Sample Sizes:")
            for variant, size in result.sample_sizes.items():
                click.echo(f"  {variant}: {size} observations")

            click.echo(f"\n🎯 Effect Sizes:")
            for comparison, effect_size in result.effect_sizes.items():
                click.echo(f"  {comparison}: {effect_size:.3f}")

            if result.business_impact:
                click.echo(f"\n💰 Business Impact:")
                for variant, impact in result.business_impact.get('primary_metric_impact', {}).items():
                    abs_change = impact.get('absolute_change', 0)
                    rel_change = impact.get('relative_change_percent', 0)
                    click.echo(f"  {variant}: {abs_change:+.3f} ({rel_change:+.1f}%)")

        except ValueError as e:
            click.echo(f"❌ Error: {str(e)}")

    asyncio.run(_analyze_abtest())

@cli.command()
@click.option('--port', default=8002, help='API server port')
@click.option('--host', default='0.0.0.0', help='API server host')
def server(port: int, host: str):
    """Start the evaluation API server"""
    import uvicorn

    click.echo(f"🚀 Starting RAG Evaluation API server on {host}:{port}")
    click.echo(f"📚 API documentation will be available at http://{host}:{port}/docs")

    # Import and run the API
    from api.evaluation_api import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

@cli.command()
def benchmark():
    """Run comprehensive benchmark evaluation"""

    async def _run_benchmark():
        click.echo("🏃‍♂️ Running comprehensive RAG system benchmark...")

        # Create sample benchmark dataset
        benchmark_data = [
            {
                "query": "What is retrieval-augmented generation?",
                "expected_answer": "Retrieval-augmented generation (RAG) is a technique that combines information retrieval with text generation.",
                "expected_contexts": ["RAG combines retrieval and generation"],
                "taxonomy_path": ["AI", "RAG"],
                "difficulty_level": "easy",
                "domain": "ai_concepts"
            },
            {
                "query": "How does vector similarity search work in RAG systems?",
                "expected_answer": "Vector similarity search in RAG works by converting queries and documents into high-dimensional vectors and finding the most similar vectors using distance metrics like cosine similarity.",
                "expected_contexts": ["Vector search uses embeddings", "Cosine similarity measures vector distance"],
                "taxonomy_path": ["AI", "Vector Search"],
                "difficulty_level": "medium",
                "domain": "ai_technology"
            },
            {
                "query": "What are the advantages and disadvantages of different chunking strategies in RAG?",
                "expected_answer": "Different chunking strategies in RAG have various trade-offs. Fixed-size chunking is simple but may break semantic units. Semantic chunking preserves meaning but is more complex. Overlapping chunks improve context but increase storage.",
                "expected_contexts": ["Chunking strategies affect retrieval quality", "Trade-offs between simplicity and semantics"],
                "taxonomy_path": ["AI", "RAG", "Chunking"],
                "difficulty_level": "hard",
                "domain": "ai_technology"
            }
        ]

        # Create benchmark dataset
        manager = GoldenDatasetManager()
        dataset = await manager.create_golden_dataset(
            name="RAG Benchmark Dataset",
            description="Comprehensive benchmark for RAG system evaluation",
            raw_data=benchmark_data,
            version="benchmark-1.0"
        )

        click.echo(f"📊 Created benchmark dataset: {dataset.id}")

        # Run evaluation
        orchestrator = EvaluationOrchestrator()
        await orchestrator.start_scheduler()

        try:
            # Mock RAG system for benchmark
            async def benchmark_rag_system(query: str) -> RAGResponse:
                # Simulate realistic response patterns
                if "retrieval-augmented" in query.lower():
                    return RAGResponse(
                        answer="Retrieval-augmented generation (RAG) combines information retrieval with language generation to improve response accuracy.",
                        retrieved_docs=[{
                            "chunk_id": "rag_doc_1",
                            "text": "RAG is a powerful technique that enhances language models by retrieving relevant information before generating responses.",
                            "score": 0.92,
                            "source": {"title": "RAG Introduction", "url": "https://example.com/rag"}
                        }],
                        confidence=0.88
                    )
                elif "vector similarity" in query.lower():
                    return RAGResponse(
                        answer="Vector similarity search converts text into numerical vectors and uses distance metrics to find semantically similar content.",
                        retrieved_docs=[{
                            "chunk_id": "vector_doc_1",
                            "text": "Vector search uses embeddings to represent text as high-dimensional vectors, enabling semantic search capabilities.",
                            "score": 0.85,
                            "source": {"title": "Vector Search Guide", "url": "https://example.com/vector"}
                        }],
                        confidence=0.82
                    )
                else:
                    return RAGResponse(
                        answer="This is a comprehensive answer covering multiple aspects of the question with detailed explanations.",
                        retrieved_docs=[{
                            "chunk_id": "general_doc_1",
                            "text": "General information relevant to the query with good coverage of the topic.",
                            "score": 0.75,
                            "source": {"title": "General Reference", "url": "https://example.com/general"}
                        }],
                        confidence=0.75
                    )

            click.echo("🧪 Running RAGAS evaluation...")
            result = await orchestrator.run_evaluation_now(
                name="RAG System Benchmark",
                description="Comprehensive benchmark evaluation of RAG system performance",
                golden_dataset_id=dataset.id,
                rag_system_callable=benchmark_rag_system
            )

            # Display comprehensive results
            click.echo(f"\n🎯 Benchmark Results:")
            click.echo("=" * 60)
            click.echo(f"Overall Score: {result.analysis.get('overall_score', 0.0):.3f}")
            click.echo(f"Quality Gates: {'✅ PASSED' if result.quality_gates_passed else '❌ FAILED'}")

            click.echo(f"\n📊 Detailed Metrics:")
            for metric, value in result.metrics.items():
                # Add performance indicators
                if value >= 0.9:
                    indicator = "🟢 Excellent"
                elif value >= 0.8:
                    indicator = "🟡 Good"
                elif value >= 0.7:
                    indicator = "🟠 Fair"
                else:
                    indicator = "🔴 Poor"

                click.echo(f"  {metric:20s}: {value:.3f} {indicator}")

            # Performance analysis
            click.echo(f"\n🔍 Analysis:")
            strengths = result.analysis.get('strengths', [])
            weaknesses = result.analysis.get('weaknesses', [])

            if strengths:
                click.echo(f"  Strengths ({len(strengths)}):")
                for strength in strengths:
                    click.echo(f"    ✅ {strength['metric']}: {strength['score']:.3f}")

            if weaknesses:
                click.echo(f"  Areas for Improvement ({len(weaknesses)}):")
                for weakness in weaknesses:
                    click.echo(f"    ⚠️  {weakness['metric']}: {weakness['score']:.3f} (target: {weakness['threshold']:.3f})")

            # Recommendations
            if result.recommendations:
                click.echo(f"\n💡 Recommendations:")
                for i, rec in enumerate(result.recommendations, 1):
                    click.echo(f"  {i}. {rec}")

            click.echo(f"\n📋 Benchmark Summary:")
            click.echo(f"  • Dataset: {len(benchmark_data)} queries across {len(set(d['difficulty_level'] for d in benchmark_data))} difficulty levels")
            click.echo(f"  • Domains: {len(set(d['domain'] for d in benchmark_data))} different domains")
            click.echo(f"  • Evaluation Time: {datetime.utcnow().isoformat()}")
            click.echo(f"  • Framework: RAGAS v1.8.1")

        finally:
            await orchestrator.stop_scheduler()

    asyncio.run(_run_benchmark())

if __name__ == '__main__':
    cli()