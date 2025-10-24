"""
Sample data generator for RAGAS evaluation system testing

Provides realistic test data including:
- Sample queries and responses
- Golden dataset entries
- Evaluation scenarios
- A/B testing configurations
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from .models import DatasetEntry, EvaluationRequest, ExperimentConfig


class SampleDataGenerator:
    """Generate realistic sample data for evaluation testing"""

    def __init__(self):
        self.sample_queries = [
            "What is Retrieval-Augmented Generation (RAG)?",
            "How does vector similarity search work?",
            "What are the advantages of using transformers in NLP?",
            "Explain the difference between BM25 and vector search",
            "What is the role of context in RAG systems?",
            "How do you evaluate the quality of a RAG system?",
            "What is semantic search and how does it differ from keyword search?",
            "What are the main components of a modern search engine?",
            "How does cross-encoder reranking improve search results?",
            "What is the purpose of document chunking in RAG?",
            "How do embedding models capture semantic meaning?",
            "What are the challenges in building production RAG systems?",
            "Explain the concept of faithfulness in RAG evaluation",
            "What is context precision and why is it important?",
            "How does context recall measure RAG system performance?",
            "What factors affect answer relevancy in RAG systems?",
            "How do you handle conflicting information in retrieved contexts?",
            "What is the impact of chunk size on RAG performance?",
            "How do you optimize retrieval for domain-specific content?",
            "What are the best practices for RAG system deployment?",
        ]

        self.sample_contexts = {
            "rag_definition": [
                "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with text generation. It first retrieves relevant documents from a knowledge base, then uses this context to generate more accurate and informative responses.",
                "RAG systems work by embedding queries and documents in a shared vector space, retrieving the most similar documents, and conditioning the generation model on this retrieved context.",
                "The main advantage of RAG is that it allows language models to access external knowledge without requiring fine-tuning on domain-specific data.",
            ],
            "vector_search": [
                "Vector similarity search works by converting text into high-dimensional numerical representations called embeddings. These embeddings capture semantic meaning, allowing for retrieval based on conceptual similarity rather than just keyword matching.",
                "Modern vector search systems use approximate nearest neighbor algorithms like FAISS or Annoy to efficiently search through millions of embeddings in real-time.",
                "Vector search is particularly effective for handling synonyms, related concepts, and complex queries where exact keyword matching would fail.",
            ],
            "transformers": [
                "Transformers use self-attention mechanisms to process sequences of text, allowing them to capture long-range dependencies and contextual relationships between words.",
                "The transformer architecture enables parallel processing of sequences, making it much faster to train than RNNs while achieving better performance on many NLP tasks.",
                "Pre-trained transformers like BERT and GPT have revolutionized NLP by providing strong baseline models that can be fine-tuned for specific tasks.",
            ],
        }

        self.sample_responses = {
            "rag_definition": "Retrieval-Augmented Generation (RAG) is an AI technique that combines information retrieval with text generation to provide more accurate and contextually relevant responses. RAG systems first search through a knowledge base to find relevant documents, then use this retrieved information as context to generate responses. This approach allows language models to access up-to-date information and domain-specific knowledge without requiring expensive retraining. The key components include a retriever (often using vector similarity search) and a generator (typically a large language model) that work together to produce well-grounded, factual responses.",
            "vector_search": "Vector similarity search converts text into numerical representations called embeddings that capture semantic meaning. Unlike traditional keyword search, vector search can find conceptually similar content even when exact words don't match. The process involves encoding both queries and documents into high-dimensional vectors, then computing similarity scores (typically cosine similarity) to rank results. Modern implementations use approximate nearest neighbor algorithms to efficiently search through millions of vectors in milliseconds.",
            "transformers": "Transformers are a neural network architecture that revolutionized natural language processing through the use of self-attention mechanisms. The key innovation is the ability to process all positions in a sequence simultaneously, capturing relationships between any two words regardless of their distance. This parallel processing makes transformers much faster to train than sequential models like RNNs, while the attention mechanism allows for better understanding of context and long-range dependencies in text.",
        }

    def generate_golden_dataset(self, size: int = 50) -> List[DatasetEntry]:
        """Generate golden dataset entries for evaluation"""
        dataset = []

        for i in range(size):
            # Select random query and corresponding context/response
            query_idx = i % len(self.sample_queries)
            query = self.sample_queries[query_idx]

            # Determine the topic based on query content
            if any(
                word in query.lower() for word in ["rag", "retrieval", "generation"]
            ):
                topic = "rag_definition"
            elif any(
                word in query.lower() for word in ["vector", "similarity", "embedding"]
            ):
                topic = "vector_search"
            elif any(
                word in query.lower()
                for word in ["transformer", "attention", "bert", "gpt"]
            ):
                topic = "transformers"
            else:
                topic = random.choice(
                    ["rag_definition", "vector_search", "transformers"]
                )

            contexts = self.sample_contexts[topic]
            response = self.sample_responses[topic]

            # Add some variation
            if i % 3 == 0:
                # Make some queries more complex
                query = f"Can you explain {query.lower()}?"
                difficulty = "medium"
            elif i % 5 == 0:
                # Make some queries harder
                query = f"Provide a detailed analysis of {query.lower()} including advantages and limitations"
                difficulty = "hard"
            else:
                difficulty = "easy"

            entry = DatasetEntry(
                query=query,
                ground_truth_answer=response,
                expected_contexts=contexts,
                difficulty_level=difficulty,
                category=topic.replace("_", " ").title(),
                tags=self._generate_tags(topic, difficulty),
            )

            dataset.append(entry)

        return dataset

    def generate_evaluation_requests(self, count: int = 20) -> List[EvaluationRequest]:
        """Generate sample evaluation requests"""
        requests = []

        for i in range(count):
            query = random.choice(self.sample_queries)

            # Select appropriate context and response
            if any(word in query.lower() for word in ["rag", "retrieval"]):
                topic = "rag_definition"
            elif any(word in query.lower() for word in ["vector", "similarity"]):
                topic = "vector_search"
            elif any(word in query.lower() for word in ["transformer", "attention"]):
                topic = "transformers"
            else:
                topic = random.choice(
                    ["rag_definition", "vector_search", "transformers"]
                )

            contexts = self.sample_contexts[topic]
            response = self.sample_responses[topic]

            # Add some noise/variation
            if i % 4 == 0:
                # Add irrelevant context
                irrelevant_topics = [
                    t for t in self.sample_contexts.keys() if t != topic
                ]
                irrelevant_topic = random.choice(irrelevant_topics)
                contexts = contexts + [
                    random.choice(self.sample_contexts[irrelevant_topic])
                ]

            if i % 6 == 0:
                # Generate partially incorrect response
                response = (
                    response[: len(response) // 2]
                    + " However, this approach has significant limitations and may not be suitable for all applications."
                )

            request = EvaluationRequest(
                query=query,
                response=response,
                retrieved_contexts=contexts,
                session_id=f"session_{i // 5 + 1}",
                model_version=random.choice(["v1.8.1", "v1.8.0", "v1.7.9"]),
            )

            requests.append(request)

        return requests

    def generate_experiment_config(self) -> ExperimentConfig:
        """Generate sample A/B testing experiment configuration"""
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ExperimentConfig(
            experiment_id=experiment_id,
            name="Retrieval Algorithm Comparison",
            description="Compare BM25 vs hybrid search performance",
            control_config={"search_type": "bm25_only", "top_k": 10, "rerank": False},
            treatment_config={
                "search_type": "hybrid",
                "bm25_weight": 0.3,
                "vector_weight": 0.7,
                "top_k": 10,
                "rerank": True,
                "rerank_model": "cross-encoder",
            },
            significance_threshold=0.05,
            minimum_sample_size=100,
            power_threshold=0.8,
        )

    def generate_quality_scenarios(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Generate scenarios for quality testing"""
        scenarios = [
            (
                "high_quality",
                {
                    "query": "What is machine learning?",
                    "response": "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. Instead of being explicitly programmed, these systems improve their performance through experience.",
                    "contexts": [
                        "Machine learning is a method of data analysis that automates analytical model building using algorithms that iteratively learn from data.",
                        "In machine learning, computers learn to make predictions or decisions by finding patterns in data.",
                        "The goal of machine learning is to develop algorithms that can learn and make predictions on data.",
                    ],
                    "expected_metrics": {
                        "faithfulness": 0.95,
                        "context_precision": 0.90,
                        "context_recall": 0.85,
                        "answer_relevancy": 0.92,
                    },
                },
            ),
            (
                "low_faithfulness",
                {
                    "query": "What is deep learning?",
                    "response": "Deep learning is a quantum computing technique that uses parallel processors to solve complex mathematical equations in real-time.",
                    "contexts": [
                        "Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers.",
                        "Deep neural networks can automatically learn hierarchical representations from data.",
                        "Deep learning has achieved breakthrough results in image recognition, natural language processing, and speech recognition.",
                    ],
                    "expected_metrics": {
                        "faithfulness": 0.20,  # Very low - response contradicts context
                        "context_precision": 0.85,
                        "context_recall": 0.80,
                        "answer_relevancy": 0.30,
                    },
                },
            ),
            (
                "low_precision",
                {
                    "query": "How does gradient descent work?",
                    "response": "Gradient descent is an optimization algorithm used to minimize a function by iteratively moving toward the minimum.",
                    "contexts": [
                        "Gradient descent is an optimization algorithm used to minimize functions.",
                        "Pizza is made with dough, sauce, and cheese.",
                        "The weather forecast shows rain tomorrow.",
                        "Cats are popular pets known for their independence.",
                        "Gradient descent uses derivatives to find the direction of steepest descent.",
                    ],
                    "expected_metrics": {
                        "faithfulness": 0.90,
                        "context_precision": 0.40,  # Low - many irrelevant contexts
                        "context_recall": 0.70,
                        "answer_relevancy": 0.85,
                    },
                },
            ),
            (
                "low_recall",
                {
                    "query": "Explain the transformer architecture in detail",
                    "response": "Transformers use attention mechanisms.",
                    "contexts": [
                        "The transformer architecture uses self-attention mechanisms to process sequences.",
                        "Transformers consist of encoder and decoder stacks with multi-head attention.",
                    ],
                    "expected_metrics": {
                        "faithfulness": 0.85,
                        "context_precision": 0.90,
                        "context_recall": 0.30,  # Low - response doesn't use much available context
                        "answer_relevancy": 0.60,
                    },
                },
            ),
            (
                "low_relevancy",
                {
                    "query": "What are the benefits of using RAG systems?",
                    "response": "The history of artificial intelligence dates back to the 1950s when researchers first began exploring machine intelligence.",
                    "contexts": [
                        "RAG systems combine retrieval and generation to provide more accurate responses.",
                        "Benefits of RAG include access to up-to-date information and reduced hallucination.",
                        "RAG allows language models to use external knowledge without retraining.",
                    ],
                    "expected_metrics": {
                        "faithfulness": 0.70,
                        "context_precision": 0.85,
                        "context_recall": 0.75,
                        "answer_relevancy": 0.25,  # Low - doesn't address the question
                    },
                },
            ),
        ]

        return scenarios

    def _generate_tags(self, topic: str, difficulty: str) -> List[str]:
        """Generate tags for dataset entries"""
        base_tags = [topic.replace("_", "-")]

        if difficulty == "hard":
            base_tags.append("complex")
        elif difficulty == "easy":
            base_tags.append("basic")

        topic_specific_tags = {
            "rag_definition": ["retrieval", "generation", "nlp"],
            "vector_search": ["embeddings", "similarity", "search"],
            "transformers": ["attention", "neural-networks", "deep-learning"],
        }

        if topic in topic_specific_tags:
            base_tags.extend(topic_specific_tags[topic])

        return base_tags

    def generate_realistic_evaluation_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """Generate realistic evaluation data for multiple days"""
        data = []
        base_time = datetime.utcnow() - timedelta(days=days)

        for day in range(days):
            # Simulate varying query volume
            daily_queries = random.randint(50, 200)

            for query_idx in range(daily_queries):
                timestamp = base_time + timedelta(
                    days=day,
                    hours=random.randint(8, 22),  # Business hours bias
                    minutes=random.randint(0, 59),
                )

                # Generate evaluation metrics with realistic variation
                base_faithfulness = 0.85 + random.gauss(0, 0.05)
                base_precision = 0.80 + random.gauss(0, 0.06)
                base_recall = 0.75 + random.gauss(0, 0.07)
                base_relevancy = 0.82 + random.gauss(0, 0.05)

                # Add daily trend (slight improvement over time)
                trend_factor = day * 0.002

                data.append(
                    {
                        "timestamp": timestamp,
                        "faithfulness": max(
                            0, min(1, base_faithfulness + trend_factor)
                        ),
                        "context_precision": max(
                            0, min(1, base_precision + trend_factor)
                        ),
                        "context_recall": max(0, min(1, base_recall + trend_factor)),
                        "answer_relevancy": max(
                            0, min(1, base_relevancy + trend_factor)
                        ),
                        "response_time": random.uniform(0.8, 3.5),
                        "query_length": random.randint(5, 50),
                        "num_contexts": random.randint(3, 8),
                    }
                )

        return data
