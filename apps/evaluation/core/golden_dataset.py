"""
Golden Dataset Management System

Comprehensive system for managing high-quality evaluation datasets:
- Dataset creation, validation, and versioning
- Quality control and consistency checking
- Ground truth annotation and validation
- Dataset splitting and sampling strategies
- Inter-annotator agreement calculation
- Data augmentation for evaluation robustness
"""

import asyncio
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import uuid
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class GoldenDataPoint:
    """Individual data point in golden dataset"""
    id: str
    query: str
    expected_answer: str
    expected_contexts: List[str]
    taxonomy_path: List[str]
    difficulty_level: str  # 'easy', 'medium', 'hard'
    domain: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    validated: bool = False
    quality_score: float = 0.0

@dataclass
class GoldenDataset:
    """Golden dataset container"""
    id: str
    name: str
    description: str
    version: str
    data_points: List[GoldenDataPoint]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    quality_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Dataset validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    quality_score: float
    recommendations: List[str]

@dataclass
class DatasetStats:
    """Dataset statistics"""
    total_size: int
    validated_count: int
    domain_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    taxonomy_distribution: Dict[str, int]
    quality_distribution: Dict[str, int]
    avg_query_length: float
    avg_answer_length: float

class GoldenDatasetManager:
    """Manages golden datasets for RAG evaluation"""

    def __init__(self, storage_path: str = "./golden_datasets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Quality thresholds
        self.quality_thresholds = {
            'min_annotation_agreement': 0.8,
            'min_completeness': 0.95,
            'min_consistency': 0.9,
            'min_diversity': 0.7,
            'min_quality_score': 0.8
        }

        # Dataset constraints
        self.constraints = {
            'min_query_length': 10,
            'max_query_length': 500,
            'min_answer_length': 20,
            'max_answer_length': 2000,
            'min_contexts_per_query': 1,
            'max_contexts_per_query': 10
        }

    async def create_golden_dataset(
        self,
        name: str,
        description: str,
        raw_data: List[Dict[str, Any]],
        version: str = "1.0",
        validate_quality: bool = True
    ) -> GoldenDataset:
        """
        Create a new golden dataset with quality validation

        Args:
            name: Dataset name
            description: Dataset description
            raw_data: List of raw data points
            version: Dataset version
            validate_quality: Whether to perform quality validation

        Returns:
            GoldenDataset object
        """
        logger.info(f"Creating golden dataset '{name}' with {len(raw_data)} data points")

        # Generate dataset ID
        dataset_id = self._generate_dataset_id(name, version)

        # Convert raw data to GoldenDataPoint objects
        data_points = []
        for i, raw_point in enumerate(raw_data):
            try:
                data_point = self._create_data_point(raw_point, i)
                data_points.append(data_point)
            except Exception as e:
                logger.warning(f"Skipping invalid data point {i}: {str(e)}")

        # Create dataset
        dataset = GoldenDataset(
            id=dataset_id,
            name=name,
            description=description,
            version=version,
            data_points=data_points
        )

        # Validate dataset quality
        if validate_quality:
            validation_result = await self.validate_dataset(dataset)
            dataset.quality_metrics = self._extract_quality_metrics(validation_result)

            if not validation_result.is_valid:
                logger.warning(f"Dataset validation failed: {validation_result.errors}")
                # Continue with warnings but flag issues

        # Save dataset
        await self.save_dataset(dataset)

        logger.info(f"Golden dataset '{name}' created successfully with {len(data_points)} valid data points")
        return dataset

    def _create_data_point(self, raw_data: Dict[str, Any], index: int) -> GoldenDataPoint:
        """Create GoldenDataPoint from raw data"""

        # Validate required fields
        required_fields = ['query', 'expected_answer']
        for field in required_fields:
            if field not in raw_data or not raw_data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Extract data
        query = raw_data['query'].strip()
        expected_answer = raw_data['expected_answer'].strip()
        expected_contexts = raw_data.get('expected_contexts', [])
        taxonomy_path = raw_data.get('taxonomy_path', ['General'])
        difficulty_level = raw_data.get('difficulty_level', 'medium')
        domain = raw_data.get('domain', 'general')

        # Validate constraints
        if not (self.constraints['min_query_length'] <= len(query) <= self.constraints['max_query_length']):
            raise ValueError(f"Query length outside allowed range: {len(query)}")

        if not (self.constraints['min_answer_length'] <= len(expected_answer) <= self.constraints['max_answer_length']):
            raise ValueError(f"Answer length outside allowed range: {len(expected_answer)}")

        # Generate ID
        data_id = self._generate_data_point_id(query, expected_answer, index)

        return GoldenDataPoint(
            id=data_id,
            query=query,
            expected_answer=expected_answer,
            expected_contexts=expected_contexts,
            taxonomy_path=taxonomy_path,
            difficulty_level=difficulty_level,
            domain=domain,
            metadata=raw_data.get('metadata', {})
        )

    async def validate_dataset(self, dataset: GoldenDataset) -> ValidationResult:
        """
        Comprehensive dataset validation

        Checks:
        - Completeness: All required fields present
        - Consistency: Data format and value consistency
        - Diversity: Query and answer diversity
        - Quality: Overall data quality metrics
        - Duplicates: Duplicate detection and handling
        """
        logger.info(f"Validating dataset '{dataset.name}' with {len(dataset.data_points)} data points")

        errors = []
        warnings = []
        recommendations = []

        # Completeness validation
        completeness_result = self._validate_completeness(dataset)
        errors.extend(completeness_result['errors'])
        warnings.extend(completeness_result['warnings'])

        # Consistency validation
        consistency_result = self._validate_consistency(dataset)
        errors.extend(consistency_result['errors'])
        warnings.extend(consistency_result['warnings'])

        # Diversity validation
        diversity_result = self._validate_diversity(dataset)
        warnings.extend(diversity_result['warnings'])
        recommendations.extend(diversity_result['recommendations'])

        # Duplicate detection
        duplicate_result = self._detect_duplicates(dataset)
        warnings.extend(duplicate_result['warnings'])
        recommendations.extend(duplicate_result['recommendations'])

        # Quality scoring
        quality_scores = self._calculate_quality_scores(dataset)
        overall_quality = np.mean(list(quality_scores.values()))

        # Generate recommendations
        if overall_quality < self.quality_thresholds['min_quality_score']:
            recommendations.append(f"Overall quality score ({overall_quality:.3f}) below threshold ({self.quality_thresholds['min_quality_score']})")

        # Determine validation result
        is_valid = len(errors) == 0 and overall_quality >= self.quality_thresholds['min_quality_score']

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=overall_quality,
            recommendations=recommendations
        )

    def _validate_completeness(self, dataset: GoldenDataset) -> Dict[str, List[str]]:
        """Validate dataset completeness"""

        errors = []
        warnings = []

        if not dataset.data_points:
            errors.append("Dataset contains no data points")
            return {'errors': errors, 'warnings': warnings}

        # Check required fields for each data point
        required_fields = ['id', 'query', 'expected_answer']

        for i, data_point in enumerate(dataset.data_points):
            for field in required_fields:
                if not hasattr(data_point, field) or not getattr(data_point, field):
                    errors.append(f"Data point {i}: Missing required field '{field}'")

            # Check field lengths
            if len(data_point.query.strip()) < self.constraints['min_query_length']:
                warnings.append(f"Data point {i}: Query too short ({len(data_point.query)} chars)")

            if len(data_point.expected_answer.strip()) < self.constraints['min_answer_length']:
                warnings.append(f"Data point {i}: Answer too short ({len(data_point.expected_answer)} chars)")

        # Check overall completeness
        total_points = len(dataset.data_points)
        complete_points = sum(1 for dp in dataset.data_points
                            if dp.query and dp.expected_answer and dp.taxonomy_path)

        completeness_ratio = complete_points / total_points if total_points > 0 else 0

        if completeness_ratio < self.quality_thresholds['min_completeness']:
            errors.append(f"Dataset completeness ({completeness_ratio:.3f}) below threshold ({self.quality_thresholds['min_completeness']})")

        return {'errors': errors, 'warnings': warnings}

    def _validate_consistency(self, dataset: GoldenDataset) -> Dict[str, List[str]]:
        """Validate dataset consistency"""

        errors = []
        warnings = []

        # Check taxonomy path consistency
        taxonomy_formats = set()
        difficulty_levels = set()
        domains = set()

        for data_point in dataset.data_points:
            # Taxonomy format consistency
            if data_point.taxonomy_path:
                taxonomy_formats.add(len(data_point.taxonomy_path))

            # Valid difficulty levels
            valid_difficulties = {'easy', 'medium', 'hard'}
            if data_point.difficulty_level not in valid_difficulties:
                warnings.append(f"Invalid difficulty level: {data_point.difficulty_level}")
            difficulty_levels.add(data_point.difficulty_level)

            # Domain consistency
            domains.add(data_point.domain)

        # Check for too many different formats
        if len(taxonomy_formats) > 3:
            warnings.append(f"Too many different taxonomy path formats: {taxonomy_formats}")

        # Check for reasonable domain diversity
        if len(domains) > 20:
            warnings.append(f"Very high domain diversity ({len(domains)} domains) - consider consolidation")

        return {'errors': errors, 'warnings': warnings}

    def _validate_diversity(self, dataset: GoldenDataset) -> Dict[str, List[str]]:
        """Validate dataset diversity"""

        warnings = []
        recommendations = []

        if len(dataset.data_points) < 10:
            warnings.append("Dataset too small for meaningful diversity analysis")
            return {'warnings': warnings, 'recommendations': recommendations}

        # Query diversity analysis
        queries = [dp.query for dp in dataset.data_points]
        query_diversity = self._calculate_text_diversity(queries)

        if query_diversity < self.quality_thresholds['min_diversity']:
            warnings.append(f"Low query diversity ({query_diversity:.3f})")
            recommendations.append("Increase query diversity by adding varied question types and topics")

        # Answer diversity analysis
        answers = [dp.expected_answer for dp in dataset.data_points]
        answer_diversity = self._calculate_text_diversity(answers)

        if answer_diversity < self.quality_thresholds['min_diversity']:
            warnings.append(f"Low answer diversity ({answer_diversity:.3f})")
            recommendations.append("Increase answer diversity by varying response lengths and styles")

        # Domain distribution analysis
        domain_counts = Counter(dp.domain for dp in dataset.data_points)
        domain_entropy = self._calculate_entropy(list(domain_counts.values()))

        if domain_entropy < 1.0:  # Low entropy indicates poor distribution
            recommendations.append("Consider more balanced domain distribution")

        # Difficulty distribution analysis
        difficulty_counts = Counter(dp.difficulty_level for dp in dataset.data_points)
        if len(difficulty_counts) < 2:
            recommendations.append("Include multiple difficulty levels for comprehensive evaluation")

        return {'warnings': warnings, 'recommendations': recommendations}

    def _detect_duplicates(self, dataset: GoldenDataset) -> Dict[str, List[str]]:
        """Detect duplicate or near-duplicate data points"""

        warnings = []
        recommendations = []

        queries = [dp.query for dp in dataset.data_points]

        # Exact duplicates
        exact_duplicates = self._find_exact_duplicates(queries)
        if exact_duplicates:
            warnings.append(f"Found {len(exact_duplicates)} exact duplicate queries")
            recommendations.append("Remove or consolidate exact duplicate queries")

        # Near duplicates (using similarity threshold)
        near_duplicates = self._find_near_duplicates(queries, threshold=0.9)
        if near_duplicates:
            warnings.append(f"Found {len(near_duplicates)} near-duplicate query pairs")
            recommendations.append("Review near-duplicate queries for potential consolidation")

        return {'warnings': warnings, 'recommendations': recommendations}

    def _calculate_text_diversity(self, texts: List[str]) -> float:
        """Calculate diversity score for a collection of texts"""

        if len(texts) < 2:
            return 1.0

        try:
            # Use TF-IDF to calculate text similarity
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Calculate pairwise similarities
            similarities = cosine_similarity(tfidf_matrix)

            # Remove diagonal (self-similarity)
            np.fill_diagonal(similarities, 0)

            # Diversity is inverse of average similarity
            avg_similarity = np.mean(similarities)
            diversity = 1.0 - avg_similarity

            return max(0.0, min(1.0, diversity))

        except Exception as e:
            logger.warning(f"Diversity calculation failed: {str(e)}")
            return 0.5  # Neutral score

    def _calculate_entropy(self, values: List[int]) -> float:
        """Calculate entropy for distribution analysis"""

        if not values or sum(values) == 0:
            return 0.0

        total = sum(values)
        probabilities = [v / total for v in values if v > 0]

        entropy = -sum(p * np.log2(p) for p in probabilities)
        return entropy

    def _find_exact_duplicates(self, texts: List[str]) -> List[Tuple[int, int]]:
        """Find exact duplicate texts"""

        duplicates = []
        seen = {}

        for i, text in enumerate(texts):
            text_clean = text.strip().lower()
            if text_clean in seen:
                duplicates.append((seen[text_clean], i))
            else:
                seen[text_clean] = i

        return duplicates

    def _find_near_duplicates(self, texts: List[str], threshold: float = 0.9) -> List[Tuple[int, int]]:
        """Find near-duplicate texts using similarity threshold"""

        if len(texts) < 2:
            return []

        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)

            near_duplicates = []

            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarity = cosine_similarity(
                        tfidf_matrix[i:i+1],
                        tfidf_matrix[j:j+1]
                    )[0][0]

                    if similarity > threshold:
                        near_duplicates.append((i, j))

            return near_duplicates

        except Exception as e:
            logger.warning(f"Near-duplicate detection failed: {str(e)}")
            return []

    def _calculate_quality_scores(self, dataset: GoldenDataset) -> Dict[str, float]:
        """Calculate various quality scores for the dataset"""

        scores = {}

        # Data completeness score
        complete_points = sum(1 for dp in dataset.data_points
                            if dp.query and dp.expected_answer and dp.taxonomy_path)
        scores['completeness'] = complete_points / len(dataset.data_points) if dataset.data_points else 0

        # Query quality score (based on length and complexity)
        query_scores = []
        for dp in dataset.data_points:
            query_length = len(dp.query.split())
            complexity_score = min(1.0, query_length / 20)  # Normalize to 20 words
            query_scores.append(complexity_score)

        scores['query_quality'] = np.mean(query_scores) if query_scores else 0

        # Answer quality score (based on length and informativeness)
        answer_scores = []
        for dp in dataset.data_points:
            answer_length = len(dp.expected_answer.split())
            informativeness_score = min(1.0, answer_length / 50)  # Normalize to 50 words
            answer_scores.append(informativeness_score)

        scores['answer_quality'] = np.mean(answer_scores) if answer_scores else 0

        # Diversity score
        queries = [dp.query for dp in dataset.data_points]
        scores['diversity'] = self._calculate_text_diversity(queries)

        # Taxonomy coverage score
        unique_paths = set(tuple(dp.taxonomy_path) for dp in dataset.data_points if dp.taxonomy_path)
        scores['taxonomy_coverage'] = min(1.0, len(unique_paths) / 10)  # Normalize to 10 paths

        return scores

    def _extract_quality_metrics(self, validation_result: ValidationResult) -> Dict[str, float]:
        """Extract quality metrics from validation result"""

        return {
            'overall_quality': validation_result.quality_score,
            'validation_passed': 1.0 if validation_result.is_valid else 0.0,
            'error_count': len(validation_result.errors),
            'warning_count': len(validation_result.warnings),
            'recommendation_count': len(validation_result.recommendations)
        }

    async def save_dataset(self, dataset: GoldenDataset):
        """Save dataset to storage"""

        file_path = self.storage_path / f"{dataset.id}.json"

        # Convert to serializable format
        dataset_dict = {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'version': dataset.version,
            'created_at': dataset.created_at.isoformat(),
            'metadata': dataset.metadata,
            'quality_metrics': dataset.quality_metrics,
            'data_points': []
        }

        for dp in dataset.data_points:
            dp_dict = {
                'id': dp.id,
                'query': dp.query,
                'expected_answer': dp.expected_answer,
                'expected_contexts': dp.expected_contexts,
                'taxonomy_path': dp.taxonomy_path,
                'difficulty_level': dp.difficulty_level,
                'domain': dp.domain,
                'metadata': dp.metadata,
                'created_at': dp.created_at.isoformat(),
                'validated': dp.validated,
                'quality_score': dp.quality_score
            }
            dataset_dict['data_points'].append(dp_dict)

        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset saved to {file_path}")

    async def load_dataset(self, dataset_id: str) -> Optional[GoldenDataset]:
        """Load dataset from storage"""

        file_path = self.storage_path / f"{dataset_id}.json"

        if not file_path.exists():
            logger.error(f"Dataset file not found: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dataset_dict = json.load(f)

            # Convert back to objects
            data_points = []
            for dp_dict in dataset_dict['data_points']:
                dp = GoldenDataPoint(
                    id=dp_dict['id'],
                    query=dp_dict['query'],
                    expected_answer=dp_dict['expected_answer'],
                    expected_contexts=dp_dict['expected_contexts'],
                    taxonomy_path=dp_dict['taxonomy_path'],
                    difficulty_level=dp_dict['difficulty_level'],
                    domain=dp_dict['domain'],
                    metadata=dp_dict['metadata'],
                    created_at=datetime.fromisoformat(dp_dict['created_at']),
                    validated=dp_dict['validated'],
                    quality_score=dp_dict['quality_score']
                )
                data_points.append(dp)

            dataset = GoldenDataset(
                id=dataset_dict['id'],
                name=dataset_dict['name'],
                description=dataset_dict['description'],
                version=dataset_dict['version'],
                data_points=data_points,
                metadata=dataset_dict['metadata'],
                created_at=datetime.fromisoformat(dataset_dict['created_at']),
                quality_metrics=dataset_dict['quality_metrics']
            )

            logger.info(f"Dataset loaded: {dataset.name} ({len(dataset.data_points)} data points)")
            return dataset

        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_id}: {str(e)}")
            return None

    async def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets"""

        datasets = []

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    dataset_dict = json.load(f)

                dataset_info = {
                    'id': dataset_dict['id'],
                    'name': dataset_dict['name'],
                    'description': dataset_dict['description'],
                    'version': dataset_dict['version'],
                    'created_at': dataset_dict['created_at'],
                    'data_points_count': len(dataset_dict['data_points']),
                    'quality_metrics': dataset_dict.get('quality_metrics', {})
                }
                datasets.append(dataset_info)

            except Exception as e:
                logger.warning(f"Failed to read dataset info from {file_path}: {str(e)}")

        return sorted(datasets, key=lambda x: x['created_at'], reverse=True)

    def get_dataset_statistics(self, dataset: GoldenDataset) -> DatasetStats:
        """Get comprehensive statistics for a dataset"""

        # Basic counts
        total_size = len(dataset.data_points)
        validated_count = sum(1 for dp in dataset.data_points if dp.validated)

        # Distributions
        domain_dist = Counter(dp.domain for dp in dataset.data_points)
        difficulty_dist = Counter(dp.difficulty_level for dp in dataset.data_points)
        taxonomy_dist = Counter(tuple(dp.taxonomy_path) for dp in dataset.data_points if dp.taxonomy_path)

        # Quality distribution
        quality_ranges = {'0.0-0.5': 0, '0.5-0.7': 0, '0.7-0.8': 0, '0.8-0.9': 0, '0.9-1.0': 0}
        for dp in dataset.data_points:
            score = dp.quality_score
            if score < 0.5:
                quality_ranges['0.0-0.5'] += 1
            elif score < 0.7:
                quality_ranges['0.5-0.7'] += 1
            elif score < 0.8:
                quality_ranges['0.7-0.8'] += 1
            elif score < 0.9:
                quality_ranges['0.8-0.9'] += 1
            else:
                quality_ranges['0.9-1.0'] += 1

        # Average lengths
        query_lengths = [len(dp.query.split()) for dp in dataset.data_points]
        answer_lengths = [len(dp.expected_answer.split()) for dp in dataset.data_points]

        return DatasetStats(
            total_size=total_size,
            validated_count=validated_count,
            domain_distribution=dict(domain_dist),
            difficulty_distribution=dict(difficulty_dist),
            taxonomy_distribution={str(k): v for k, v in taxonomy_dist.items()},
            quality_distribution=quality_ranges,
            avg_query_length=np.mean(query_lengths) if query_lengths else 0,
            avg_answer_length=np.mean(answer_lengths) if answer_lengths else 0
        )

    def split_dataset(
        self,
        dataset: GoldenDataset,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        stratify_by: str = 'difficulty_level'
    ) -> Tuple[GoldenDataset, GoldenDataset, GoldenDataset]:
        """Split dataset into train/validation/test sets"""

        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Split ratios must sum to 1.0")

        data_points = dataset.data_points

        if stratify_by and hasattr(data_points[0], stratify_by):
            # Stratified split
            stratify_values = [getattr(dp, stratify_by) for dp in data_points]

            # First split: train vs (val + test)
            train_data, temp_data, train_strat, temp_strat = train_test_split(
                data_points, stratify_values,
                test_size=(val_ratio + test_ratio),
                stratify=stratify_values,
                random_state=42
            )

            # Second split: val vs test
            if val_ratio > 0 and test_ratio > 0:
                val_test_ratio = val_ratio / (val_ratio + test_ratio)
                val_data, test_data = train_test_split(
                    temp_data,
                    test_size=(1 - val_test_ratio),
                    stratify=temp_strat,
                    random_state=42
                )
            elif val_ratio > 0:
                val_data, test_data = temp_data, []
            else:
                val_data, test_data = [], temp_data
        else:
            # Random split
            train_data, temp_data = train_test_split(
                data_points,
                test_size=(val_ratio + test_ratio),
                random_state=42
            )

            if val_ratio > 0 and test_ratio > 0:
                val_test_ratio = val_ratio / (val_ratio + test_ratio)
                val_data, test_data = train_test_split(
                    temp_data,
                    test_size=(1 - val_test_ratio),
                    random_state=42
                )
            elif val_ratio > 0:
                val_data, test_data = temp_data, []
            else:
                val_data, test_data = [], temp_data

        # Create split datasets
        train_dataset = GoldenDataset(
            id=f"{dataset.id}_train",
            name=f"{dataset.name} (Train)",
            description=f"Training split of {dataset.name}",
            version=dataset.version,
            data_points=train_data,
            metadata={**dataset.metadata, 'split': 'train', 'parent_id': dataset.id}
        )

        val_dataset = GoldenDataset(
            id=f"{dataset.id}_val",
            name=f"{dataset.name} (Validation)",
            description=f"Validation split of {dataset.name}",
            version=dataset.version,
            data_points=val_data,
            metadata={**dataset.metadata, 'split': 'validation', 'parent_id': dataset.id}
        )

        test_dataset = GoldenDataset(
            id=f"{dataset.id}_test",
            name=f"{dataset.name} (Test)",
            description=f"Test split of {dataset.name}",
            version=dataset.version,
            data_points=test_data,
            metadata={**dataset.metadata, 'split': 'test', 'parent_id': dataset.id}
        )

        logger.info(f"Dataset split: train={len(train_data)}, val={len(val_data)}, test={len(test_data)}")

        return train_dataset, val_dataset, test_dataset

    def _generate_dataset_id(self, name: str, version: str) -> str:
        """Generate unique dataset ID"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(f"{name}_{version}".encode()).hexdigest()[:8]
        return f"golden_{timestamp}_{name_hash}"

    def _generate_data_point_id(self, query: str, answer: str, index: int) -> str:
        """Generate unique data point ID"""

        content_hash = hashlib.md5(f"{query}_{answer}".encode()).hexdigest()[:8]
        return f"dp_{index:06d}_{content_hash}"

    async def augment_dataset(
        self,
        dataset: GoldenDataset,
        augmentation_factor: float = 0.2,
        augmentation_methods: List[str] = None
    ) -> GoldenDataset:
        """
        Augment dataset with synthetic variations for robustness testing

        Args:
            dataset: Original dataset
            augmentation_factor: Fraction of original data to generate as augmented data
            augmentation_methods: List of augmentation methods to apply

        Returns:
            Augmented dataset
        """
        if augmentation_methods is None:
            augmentation_methods = ['paraphrase', 'synonym_replacement', 'question_variation']

        logger.info(f"Augmenting dataset with factor {augmentation_factor}")

        original_size = len(dataset.data_points)
        target_augmented = int(original_size * augmentation_factor)

        augmented_points = []

        for i in range(target_augmented):
            # Select random original data point
            original_dp = np.random.choice(dataset.data_points)

            # Apply random augmentation method
            method = np.random.choice(augmentation_methods)

            try:
                augmented_dp = await self._apply_augmentation(original_dp, method, i)
                augmented_points.append(augmented_dp)
            except Exception as e:
                logger.warning(f"Augmentation failed for method {method}: {str(e)}")

        # Create augmented dataset
        augmented_dataset = GoldenDataset(
            id=f"{dataset.id}_augmented",
            name=f"{dataset.name} (Augmented)",
            description=f"Augmented version of {dataset.name}",
            version=dataset.version,
            data_points=dataset.data_points + augmented_points,
            metadata={**dataset.metadata, 'augmented': True, 'augmentation_factor': augmentation_factor}
        )

        logger.info(f"Dataset augmented: {original_size} -> {len(augmented_dataset.data_points)} data points")

        return augmented_dataset

    async def _apply_augmentation(self, data_point: GoldenDataPoint, method: str, index: int) -> GoldenDataPoint:
        """Apply specific augmentation method to data point"""

        if method == 'paraphrase':
            # Simple paraphrasing (in practice, would use more sophisticated methods)
            augmented_query = self._simple_paraphrase(data_point.query)
            augmented_answer = data_point.expected_answer  # Keep answer the same

        elif method == 'synonym_replacement':
            # Replace some words with synonyms
            augmented_query = self._synonym_replacement(data_point.query)
            augmented_answer = data_point.expected_answer

        elif method == 'question_variation':
            # Vary question structure
            augmented_query = self._vary_question_structure(data_point.query)
            augmented_answer = data_point.expected_answer

        else:
            raise ValueError(f"Unknown augmentation method: {method}")

        # Create new data point
        augmented_dp = GoldenDataPoint(
            id=f"{data_point.id}_aug_{index}",
            query=augmented_query,
            expected_answer=augmented_answer,
            expected_contexts=data_point.expected_contexts.copy(),
            taxonomy_path=data_point.taxonomy_path.copy(),
            difficulty_level=data_point.difficulty_level,
            domain=data_point.domain,
            metadata={**data_point.metadata, 'augmented': True, 'method': method, 'original_id': data_point.id},
            validated=False,  # Augmented data needs validation
            quality_score=data_point.quality_score * 0.9  # Slight quality reduction for augmented data
        )

        return augmented_dp

    def _simple_paraphrase(self, text: str) -> str:
        """Simple paraphrasing transformations"""

        # Basic paraphrasing rules (in practice, use more sophisticated NLP models)
        transformations = [
            ('What is', 'What can you tell me about'),
            ('How does', 'In what way does'),
            ('Why is', 'What is the reason that'),
            ('Can you explain', 'Could you describe'),
            ('What are the benefits', 'What advantages are there'),
        ]

        paraphrased = text
        for original, replacement in transformations:
            if original in text:
                paraphrased = text.replace(original, replacement, 1)
                break

        return paraphrased if paraphrased != text else text + " Please provide details."

    def _synonym_replacement(self, text: str) -> str:
        """Replace words with synonyms"""

        # Simple synonym dictionary (in practice, use WordNet or similar)
        synonyms = {
            'good': 'excellent',
            'bad': 'poor',
            'big': 'large',
            'small': 'tiny',
            'fast': 'quick',
            'slow': 'gradual',
            'important': 'crucial',
            'different': 'distinct'
        }

        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?')
            if word_lower in synonyms:
                # Replace with 30% probability
                if np.random.random() < 0.3:
                    words[i] = words[i].replace(word_lower, synonyms[word_lower])

        return ' '.join(words)

    def _vary_question_structure(self, query: str) -> str:
        """Vary question structure while preserving meaning"""

        # Simple structural variations
        if query.startswith('What'):
            if 'is' in query:
                return query.replace('What is', 'Can you tell me what') + '?'
        elif query.startswith('How'):
            return query.replace('How', 'In what way')
        elif query.startswith('Why'):
            return query.replace('Why', 'What is the reason that')

        return query  # Return original if no transformation applies