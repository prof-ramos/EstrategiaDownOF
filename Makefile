# Makefile for EstrategiaDownOF
# Quick commands for development workflow

.PHONY: help install install-dev test clean lint format run backup-db security docker-build docker-run docs

# Default target - show help
help:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║            EstrategiaDownOF - Makefile Commands               ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install dev dependencies + pre-commit hooks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test             Run tests with coverage"
	@echo "  make test-fast        Run tests without coverage"
	@echo "  make test-unit        Run only unit tests"
	@echo "  make test-integration Run only integration tests"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint             Run all linters (ruff, mypy, bandit)"
	@echo "  make format           Format code with black + ruff"
	@echo "  make security         Run security checks"
	@echo "  make pre-commit       Run pre-commit hooks on all files"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make clean-db         Remove database files"
	@echo "  make clean-all        Deep clean (clean + clean-db)"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run              Run downloader (headless mode)"
	@echo "  make run-gui          Run downloader (GUI mode)"
	@echo "  make stats            Show download statistics"
	@echo "  make verify           Verify file integrity"
	@echo ""
	@echo "💾 Database:"
	@echo "  make backup-db        Backup database with timestamp"
	@echo "  make migrate          Migrate JSON to SQLite"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run in Docker container"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  make docs             Generate documentation"
	@echo "  make docs-serve       Serve documentation locally"
	@echo ""

# Installation targets
install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install
	@echo "✓ Development environment ready!"

# Testing targets
test:
	pytest -v --cov=. --cov-report=term-missing --cov-report=html

test-fast:
	pytest -v -x

test-unit:
	pytest -v -m unit

test-integration:
	pytest -v -m integration

test-watch:
	pytest-watch -v

# Code quality targets
lint:
	@echo "Running ruff..."
	ruff check .
	@echo "Running mypy..."
	mypy . --install-types --non-interactive || true
	@echo "Running bandit..."
	bandit -r . -c pyproject.toml || true

format:
	@echo "Formatting with black..."
	black .
	@echo "Auto-fixing with ruff..."
	ruff check --fix .

security:
	@echo "Running bandit security checks..."
	bandit -r . -f json -o bandit-report.json || true
	@echo "Checking dependencies for vulnerabilities..."
	safety check --json || true
	@echo "Security reports saved to bandit-report.json"

pre-commit:
	pre-commit run --all-files

# Cleanup targets
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .coverage htmlcov coverage.xml .tox
	@echo "✓ Cleanup complete"

clean-db:
	@echo "Removing database files..."
	rm -f download_index.db download_index.db-journal
	rm -f download_index.db-shm download_index.db-wal
	find . -type f -name "*.part" -delete
	@echo "✓ Database files removed"

clean-all: clean clean-db
	@echo "✓ Deep clean complete"

# Running targets
run:
	python main.py --headless --workers 8

run-gui:
	python main.py

stats:
	python main.py --stats

verify:
	python main.py --verify

compress:
	./compress.sh

# Database targets
backup-db:
	@if [ -f download_index.db ]; then \
		TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
		cp download_index.db "download_index.db.backup.$$TIMESTAMP"; \
		echo "✓ Database backed up to download_index.db.backup.$$TIMESTAMP"; \
	else \
		echo "⚠ No database file found"; \
	fi

migrate:
	@if [ -f download_index.json ]; then \
		echo "Migrating JSON to SQLite..."; \
		python -c "from download_database import DownloadDatabase; db = DownloadDatabase('.', use_sqlite=True)"; \
		echo "✓ Migration complete"; \
	else \
		echo "⚠ No JSON index file found"; \
	fi

# Docker targets
docker-build:
	docker build -t estrategia-downloader:latest .

docker-run:
	docker-compose up

docker-stop:
	docker-compose down

# Documentation targets
docs:
	cd docs && sphinx-build -b html . _build/html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Build and release targets
build:
	python -m build

publish-test:
	twine upload --repository testpypi dist/*

publish:
	twine upload dist/*

# Version bump helpers
bump-patch:
	@echo "Current version: $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"
	@read -p "Enter new patch version (e.g., 2.0.1): " version; \
	sed -i.bak "s/version = \".*\"/version = \"$$version\"/" pyproject.toml && rm pyproject.toml.bak
	@echo "✓ Version bumped to $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"

bump-minor:
	@echo "Current version: $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"
	@read -p "Enter new minor version (e.g., 2.1.0): " version; \
	sed -i.bak "s/version = \".*\"/version = \"$$version\"/" pyproject.toml && rm pyproject.toml.bak
	@echo "✓ Version bumped to $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"

bump-major:
	@echo "Current version: $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"
	@read -p "Enter new major version (e.g., 3.0.0): " version; \
	sed -i.bak "s/version = \".*\"/version = \"$$version\"/" pyproject.toml && rm pyproject.toml.bak
	@echo "✓ Version bumped to $$(grep version pyproject.toml | head -1 | cut -d'\"' -f2)"

# Quick development workflow
dev: clean install-dev format lint test
	@echo "✓ Development workflow complete!"
