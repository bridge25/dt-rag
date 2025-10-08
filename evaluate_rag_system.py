"""
RAG System Evaluation with RAGAS

Evaluates the DT-RAG system using:
- Golden dataset
- Hybrid search engine
- RAGAS metrics (Context Precision/Recall, Faithfulness, Answer Relevancy)
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def evaluate_system(golden_dataset_path: str):
    """
    Evaluate RAG system using golden dataset

    Args:
        golden_dataset_path: Path to golden dataset JSON file
    """
    from apps.evaluation.golden_dataset_generator import GoldenDatasetGenerator
    from apps.evaluation.ragas_engine import RAGASEvaluator
    from apps.search.hybrid_search_engine import hybrid_search

    logger.info("=" * 60)
    logger.info("RAG System Evaluation with RAGAS")
    logger.info("=" * 60)

    # Load golden dataset
    generator = GoldenDatasetGenerator()
    golden_samples = generator.load_dataset(golden_dataset_path)

    logger.info(f"Loaded {len(golden_samples)} golden samples")
    logger.info("")

    # Initialize RAGAS evaluator
    evaluator = RAGASEvaluator()

    # Evaluation results
    results = []
    metrics_summary = {
        "context_precision": [],
        "context_recall": [],
        "faithfulness": [],
        "answer_relevancy": []
    }

    logger.info("Running evaluations...")
    logger.info("")

    for idx, sample in enumerate(golden_samples[:10]):  # Evaluate first 10 for demo
        try:
            logger.info(f"[{idx+1}/{min(10, len(golden_samples))}] Evaluating: {sample.question[:60]}...")

            # Step 1: Perform hybrid search
            search_results, search_metrics = await hybrid_search(
                query=sample.question,
                top_k=5
            )

            # Extract contexts
            retrieved_contexts = [result["text"] for result in search_results]

            # Step 2: Generate answer (simplified - using first context)
            if retrieved_contexts:
                generated_answer = f"Based on the context: {retrieved_contexts[0][:200]}..."
            else:
                generated_answer = "No relevant information found."

            # Step 3: RAGAS evaluation
            eval_result = await evaluator.evaluate_rag_response(
                query=sample.question,
                response=generated_answer,
                retrieved_contexts=retrieved_contexts,
                ground_truth=sample.ground_truth_answer
            )

            # Collect metrics
            metrics_summary["context_precision"].append(eval_result.metrics.context_precision)
            metrics_summary["context_recall"].append(eval_result.metrics.context_recall)
            metrics_summary["faithfulness"].append(eval_result.metrics.faithfulness)
            metrics_summary["answer_relevancy"].append(eval_result.metrics.answer_relevancy)

            results.append({
                "question": sample.question,
                "ground_truth": sample.ground_truth_answer,
                "generated_answer": generated_answer,
                "retrieved_contexts_count": len(retrieved_contexts),
                "metrics": {
                    "context_precision": eval_result.metrics.context_precision,
                    "context_recall": eval_result.metrics.context_recall,
                    "faithfulness": eval_result.metrics.faithfulness,
                    "answer_relevancy": eval_result.metrics.answer_relevancy
                },
                "search_latency": search_metrics.get("total_time", 0)
            })

            logger.info(f"  ✓ Precision: {eval_result.metrics.context_precision:.2f}, "
                       f"Recall: {eval_result.metrics.context_recall:.2f}, "
                       f"Faithfulness: {eval_result.metrics.faithfulness:.2f}")

        except Exception as e:
            logger.warning(f"  ✗ Evaluation failed: {e}")
            continue

    # Calculate averages
    avg_metrics = {
        "context_precision": sum(metrics_summary["context_precision"]) / len(metrics_summary["context_precision"]) if metrics_summary["context_precision"] else 0,
        "context_recall": sum(metrics_summary["context_recall"]) / len(metrics_summary["context_recall"]) if metrics_summary["context_recall"] else 0,
        "faithfulness": sum(metrics_summary["faithfulness"]) / len(metrics_summary["faithfulness"]) if metrics_summary["faithfulness"] else 0,
        "answer_relevancy": sum(metrics_summary["answer_relevancy"]) / len(metrics_summary["answer_relevancy"]) if metrics_summary["answer_relevancy"] else 0
    }

    logger.info("")
    logger.info("=" * 60)
    logger.info("Evaluation Results Summary")
    logger.info("=" * 60)
    logger.info(f"Total Evaluated: {len(results)}")
    logger.info(f"")
    logger.info(f"Average Metrics:")
    logger.info(f"  Context Precision: {avg_metrics['context_precision']:.3f}")
    logger.info(f"  Context Recall:    {avg_metrics['context_recall']:.3f}")
    logger.info(f"  Faithfulness:      {avg_metrics['faithfulness']:.3f}")
    logger.info(f"  Answer Relevancy:  {avg_metrics['answer_relevancy']:.3f}")

    # Save results
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ragas_evaluation_{timestamp}.json"

    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "golden_dataset": str(golden_dataset_path),
            "total_samples": len(golden_samples),
            "evaluated_samples": len(results)
        },
        "average_metrics": avg_metrics,
        "detailed_results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info(f"Results saved to: {output_file}")
    logger.info("=" * 60)

    return avg_metrics

async def main():
    """Main execution"""

    # Find latest golden dataset
    golden_dir = Path("golden_datasets")
    if not golden_dir.exists():
        logger.error("No golden_datasets directory found!")
        logger.error("Please run: python generate_golden_dataset.py first")
        return

    # Get latest dataset
    datasets = list(golden_dir.glob("*.json"))
    if not datasets:
        logger.error("No golden datasets found!")
        logger.error("Please run: python generate_golden_dataset.py first")
        return

    latest_dataset = max(datasets, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using golden dataset: {latest_dataset}")
    logger.info("")

    # Run evaluation
    avg_metrics = await evaluate_system(str(latest_dataset))

    # Quality assessment
    logger.info("")
    logger.info("Quality Assessment:")
    if avg_metrics["context_precision"] >= 0.7 and avg_metrics["context_recall"] >= 0.7:
        logger.info("  ✅ EXCELLENT - Retrieval quality is high")
    elif avg_metrics["context_precision"] >= 0.5 and avg_metrics["context_recall"] >= 0.5:
        logger.info("  ⚠️  GOOD - Retrieval quality is acceptable")
    else:
        logger.info("  ❌ NEEDS IMPROVEMENT - Retrieval quality needs work")

    if avg_metrics["faithfulness"] >= 0.8:
        logger.info("  ✅ EXCELLENT - Generated answers are faithful")
    elif avg_metrics["faithfulness"] >= 0.6:
        logger.info("  ⚠️  GOOD - Generated answers are mostly faithful")
    else:
        logger.info("  ❌ NEEDS IMPROVEMENT - Faithfulness needs work")

if __name__ == "__main__":
    asyncio.run(main())
