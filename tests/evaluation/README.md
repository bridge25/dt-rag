# RAG Evaluation Framework Test Suite

Comprehensive test suite for the Dynamic Taxonomy RAG v1.8.1 evaluation framework, ensuring quality, reliability, and performance of all evaluation components.

## 🎯 Overview

This test suite provides comprehensive coverage for:

- **RAGAS Engine**: Evaluation metrics and quality assessment
- **Golden Dataset Management**: Dataset creation, validation, and versioning
- **A/B Testing Framework**: Statistical testing and experiment management
- **Evaluation Orchestrator**: Automated workflows and quality gates
- **Integration Testing**: End-to-end evaluation workflows
- **Performance Testing**: Scalability and benchmarking

## 🏗️ Test Structure

```
tests/evaluation/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                    # Pytest configuration
├── run_tests.py                   # Test runner script
├── README.md                      # This documentation
├── test_ragas_engine.py          # RAGAS evaluation tests
├── test_golden_dataset.py        # Golden dataset management tests
├── test_ab_testing.py            # A/B testing framework tests
├── test_orchestrator.py          # Evaluation orchestrator tests
└── test_integration.py           # Integration and end-to-end tests
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Install evaluation framework dependencies
pip install -r ../../apps/evaluation/requirements.txt
```

### 2. Run Tests

```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py unit          # Fast unit tests
python run_tests.py integration   # Integration tests
python run_tests.py performance   # Performance tests

# Run with coverage
python run_tests.py coverage

# Check dependencies
python run_tests.py deps
```

### 3. Advanced Usage

```bash
# Run specific test file
python run_tests.py specific test_ragas_engine.py

# Run specific test function
pytest test_ragas_engine.py::TestRAGASEvaluationEngine::test_ragas_evaluation_basic -v

# Run with custom markers
pytest -m "not slow" -v

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## 📊 Test Categories

### Unit Tests (`pytest -m "not integration and not performance"`)

Fast tests with no external dependencies:

- **RAGAS Engine Tests** (`test_ragas_engine.py`)
  - Basic evaluation functionality
  - Quality gates enforcement
  - Custom metrics integration
  - Fallback mechanisms
  - Error handling

- **Golden Dataset Tests** (`test_golden_dataset.py`)
  - Dataset creation and validation
  - Quality assessment algorithms
  - Data point validation
  - Storage and retrieval

- **A/B Testing Tests** (`test_ab_testing.py`)
  - Statistical test implementations
  - Sample size calculations
  - Multiple testing corrections
  - Experiment design validation

- **Orchestrator Tests** (`test_orchestrator.py`)
  - Job scheduling and management
  - Quality gates implementation
  - Alert system functionality
  - Performance monitoring

### Integration Tests (`pytest -m integration`)

End-to-end workflow tests:

- **Complete Evaluation Workflow**
  - Dataset creation → RAG evaluation → Results analysis
  - Quality gates enforcement throughout pipeline
  - Error handling and recovery

- **A/B Testing Integration**
  - Experiment design → Data collection → Statistical analysis
  - Integration with evaluation metrics

- **Continuous Monitoring**
  - Automated evaluation scheduling
  - Alert generation and handling
  - Performance degradation detection

- **Multi-Domain Evaluation**
  - Cross-domain dataset evaluation
  - Domain-specific performance analysis

### Performance Tests (`pytest -m performance`)

Scalability and benchmarking tests:

- **Large Dataset Processing**
  - 1000+ query evaluation performance
  - Memory usage optimization
  - Concurrent evaluation handling

- **Statistical Analysis Performance**
  - Large-scale A/B test analysis
  - Multiple testing correction efficiency

- **Real-time Monitoring**
  - Continuous evaluation performance
  - Alert system responsiveness

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests/evaluation
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (slower, may use external resources)
    performance: Performance tests (very slow)
    slow: Slow running tests (require --runslow option)
    requires_openai: Tests that require OpenAI API key
    requires_database: Tests that require database connection

asyncio_mode = auto
timeout = 300
```

### Shared Fixtures (`conftest.py`)

Common test fixtures and utilities:

- `temp_directory`: Temporary storage for test files
- `sample_config`: Test configuration settings
- `mock_rag_responses`: Sample RAG system responses
- `mock_dt_rag_pipeline`: Mocked pipeline integration
- `performance_test_data`: Large datasets for performance testing

## 📈 Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| RAGAS Engine | 95% | ✅ Implemented |
| Golden Dataset | 90% | ✅ Implemented |
| A/B Testing | 90% | ✅ Implemented |
| Orchestrator | 85% | ✅ Implemented |
| API Layer | 80% | ✅ Implemented |
| Integration | 75% | ✅ Implemented |

## 🧪 Test Scenarios

### RAGAS Engine Test Scenarios

1. **Basic Evaluation**
   - Standard RAGAS metrics calculation
   - Quality gates validation
   - Result analysis generation

2. **Fallback Mechanisms**
   - RAGAS library unavailable
   - Custom metric implementations
   - Error recovery strategies

3. **Custom Metrics**
   - Taxonomy-specific evaluations
   - Domain adaptation metrics
   - Quality assessment algorithms

4. **Performance Optimization**
   - Large dataset processing
   - Memory usage optimization
   - Concurrent evaluation handling

### Golden Dataset Test Scenarios

1. **Dataset Creation**
   - Raw data validation
   - Quality score calculation
   - Metadata management

2. **Quality Assessment**
   - Completeness validation
   - Consistency checking
   - Diversity analysis
   - Inter-annotator agreement

3. **Dataset Evolution**
   - Version management
   - Dataset comparison
   - Augmentation strategies

4. **Storage and Retrieval**
   - Efficient data storage
   - Fast dataset loading
   - Backup and recovery

### A/B Testing Test Scenarios

1. **Experiment Design**
   - Sample size calculation
   - Statistical power analysis
   - Randomization strategies

2. **Statistical Analysis**
   - T-tests, chi-square, Mann-Whitney
   - Multiple testing corrections
   - Effect size calculations
   - Confidence intervals

3. **Experiment Management**
   - Data collection workflows
   - Early stopping rules
   - Result interpretation

4. **Bayesian Analysis**
   - Prior specification
   - Posterior calculation
   - Decision making

### Integration Test Scenarios

1. **End-to-End Evaluation**
   - Complete workflow execution
   - Error handling and recovery
   - Result validation

2. **System Integration**
   - dt-rag pipeline integration
   - Database connectivity
   - External service integration

3. **Performance Monitoring**
   - Continuous evaluation
   - Alert generation
   - Quality degradation detection

## 🚨 Error Handling Tests

### Graceful Degradation

- RAGAS library failures → Fallback implementations
- Database connectivity issues → Local storage fallback
- API timeouts → Retry mechanisms with exponential backoff

### Data Validation

- Malformed input data → Clear error messages
- Missing required fields → Validation errors
- Invalid configurations → Configuration validation

### Resource Management

- Memory limitations → Chunked processing
- Disk space issues → Cleanup mechanisms
- Network failures → Offline mode operation

## 📊 Performance Benchmarks

### Expected Performance Characteristics

| Operation | Target Performance | Test Verification |
|-----------|-------------------|------------------|
| RAGAS Evaluation (100 queries) | < 60 seconds | ✅ Performance test |
| Dataset Validation (1000 points) | < 30 seconds | ✅ Performance test |
| A/B Test Analysis (10k observations) | < 10 seconds | ✅ Performance test |
| Quality Gate Check | < 1 second | ✅ Unit test |
| Job Scheduling | < 0.1 seconds | ✅ Unit test |

### Memory Usage

- Base framework: < 100MB
- 1000 query evaluation: < 500MB additional
- Large dataset processing: < 1GB peak usage

## 🔄 Continuous Integration

### GitHub Actions Integration

```yaml
name: Evaluation Framework Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r apps/evaluation/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: |
          cd tests/evaluation
          python run_tests.py coverage
```

### Pre-commit Hooks

```yaml
repos:
  - repo: local
    hooks:
      - id: evaluation-tests
        name: RAG Evaluation Tests
        entry: python tests/evaluation/run_tests.py unit
        language: system
        pass_filenames: false
```

## 🛠️ Debugging Tests

### Common Issues and Solutions

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH includes evaluation modules
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/apps/evaluation"
   ```

2. **Async Test Issues**
   ```python
   # Use proper async test decoration
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

3. **Mock Configuration**
   ```python
   # Proper async mock setup
   with patch('module.async_function') as mock_func:
       mock_func.return_value = AsyncMock(return_value="result")
   ```

### Test Debugging Commands

```bash
# Run with verbose output
pytest -v -s

# Run with debugging breakpoints
pytest --pdb

# Run with coverage and missing lines
pytest --cov=core --cov-report=term-missing

# Run specific test with full traceback
pytest test_file.py::test_function -vvv --tb=long
```

## 🎯 Quality Assurance

### Code Quality Standards

- **Line Coverage**: > 85% for all components
- **Branch Coverage**: > 80% for critical paths
- **Test Isolation**: Each test runs independently
- **Performance**: Unit tests < 1s, Integration tests < 60s
- **Documentation**: All test functions documented

### Review Checklist

- [ ] All tests pass in isolation
- [ ] Tests cover both success and failure cases
- [ ] Performance tests validate scalability
- [ ] Integration tests verify end-to-end workflows
- [ ] Mocks are properly configured
- [ ] Test data is realistic and comprehensive
- [ ] Error handling is thoroughly tested

## 📚 Additional Resources

- [RAGAS Documentation](https://docs.ragas.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Statistical Testing Best Practices](https://en.wikipedia.org/wiki/A/B_testing)

## 🤝 Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Add appropriate markers (`unit`, `integration`, `performance`)
3. Include docstrings explaining test purpose
4. Mock external dependencies appropriately
5. Verify tests pass in isolation and with full suite
6. Update documentation for new test scenarios

## 🏆 Success Metrics

Target achievements for test suite:

- **Coverage**: > 85% line coverage across all components
- **Performance**: All tests complete within time limits
- **Reliability**: < 1% flaky test rate
- **Maintainability**: Tests remain stable across framework changes
- **Documentation**: All test scenarios clearly documented

---

## 📞 Support

For test-related issues:

1. Check test logs for specific error messages
2. Verify all dependencies are installed
3. Ensure proper environment configuration
4. Review test documentation for expected behavior
5. Run dependency checker: `python run_tests.py deps`

**Happy Testing! 🧪✨**