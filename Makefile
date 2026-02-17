.PHONY: test test-verbose test-coverage install-test-deps clean

# Default Python command
PYTHON := python3
PIP := pip3

# Install test dependencies
install-test-deps:
	$(PIP) install -r requirements-test.txt

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Run tests with verbose output
test-verbose:
	$(PYTHON) -m pytest tests/ -v -s

# Run tests with coverage
test-coverage:
	$(PYTHON) -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
test-auth:
	$(PYTHON) -m pytest tests/test_enhanced_auth.py -v

test-api:
	$(PYTHON) -m pytest tests/test_api_routes.py -v

test-cache:
	$(PYTHON) -m pytest tests/test_cache_manager.py -v

# Clean up
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Quick test setup and run
quick-test: install-test-deps test

# Help
help:
	@echo "Available commands:"
	@echo "  install-test-deps  - Install test dependencies"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-auth         - Run authentication tests only"
	@echo "  test-api          - Run API tests only"
	@echo "  test-cache        - Run cache tests only"
	@echo "  clean             - Clean up test artifacts"
	@echo "  quick-test        - Install deps and run tests"
