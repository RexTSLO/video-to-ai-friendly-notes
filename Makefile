.PHONY: test test-cov clean init help

help:
	@echo "Available targets:"
	@echo "  init - Install pre-commit, gitleaks, and set up git hooks"
	@echo "  test            - Run pytest test suite"
	@echo "  test-cov        - Run pytest with coverage report"
	@echo "  clean           - Remove Python cache files"


init:
	@echo "Checking pre-commit..."
	@if ! command -v pre-commit >/dev/null 2>&1; then \
		echo "Installing pre-commit..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install pre-commit; \
		elif command -v pip >/dev/null 2>&1; then \
			pip install pre-commit; \
		else \
			echo "❌ Could not find brew or pip. Please install pre-commit manually: https://pre-commit.com/#install"; \
			exit 1; \
		fi; \
	else \
		echo "✓ pre-commit is already installed."; \
	fi
	@echo "Checking gitleaks..."
	@if ! command -v gitleaks >/dev/null 2>&1; then \
		echo "Installing gitleaks..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install gitleaks; \
		else \
			echo "⚠️ Suggest installing gitleaks manually: brew install gitleaks"; \
		fi; \
	else \
		echo "✓ gitleaks is already installed."; \
	fi
	@echo "🔧 Installing Git Hooks..."
	@pre-commit install
	@echo "🔍 Running initial safety scan..."
	@pre-commit run --all-files || echo "⚠️ Scan found issues, please check the output above."

test:
	PYTHONPATH=. ./venv/bin/pytest tests/ -v

test-cov:
	PYTHONPATH=. ./venv/bin/pytest --cov=src tests/ -v --cov-report=term-missing --cov-fail-under=95

security-scan:
	@echo "Running semgrep security scan..."
	@./venv/bin/semgrep scan --config auto || exit 1
	@echo ""
	@echo "Running pip-audit dependency check..."
	@IGNORE_ARGS=$$(if [ -f .audit-ignore ]; then grep -v '^#' .audit-ignore | grep -v '^$$' | awk '{print "--ignore-vuln " $$1}' | tr '\n' ' '; fi); \
	./venv/bin/pip-audit $$IGNORE_ARGS -r requirements.txt || exit 1
	@echo ""
	@echo "Security scan completed successfully."


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
