# Makefile for E-Commerce Price Scraper

.PHONY: help build up down logs clean test lint format

help:
	@echo "E-Commerce Price Scraper - Available Commands"
	@echo "=============================================="
	@echo "make build         - Build Docker images"
	@echo "make up            - Start all services"
	@echo "make down          - Stop all services"
	@echo "make scrape        - Run all scrapers"
	@echo "make scrape-jumia  - Run Jumia spider only"
	@echo "make logs          - View logs"
	@echo "make clean         - Clean up containers and volumes"
	@echo "make test          - Run tests"
	@echo "make lint          - Run linters"
	@echo "make format        - Format code with black"
	@echo "make shell         - Open Python shell in container"

build:
	docker-compose build

up:
	docker-compose up -d postgres superset

down:
	docker-compose down

scrape:
	docker-compose up scraper

scrape-jumia:
	docker-compose run --rm scraper scrapy crawl jumia

scrape-masoko:
	docker-compose run --rm scraper scrapy crawl masoko

scrape-phoneplace:
	docker-compose run --rm scraper scrapy crawl phoneplace

scrape-laptopclinic:
	docker-compose run --rm scraper scrapy crawl laptopclinic

logs:
	docker-compose logs -f

logs-scraper:
	docker-compose logs -f scraper

logs-postgres:
	docker-compose logs -f postgres

clean:
	docker-compose down -v
	rm -rf logs/*.log
	rm -rf .scrapy/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	pytest -v --cov=ecommerce --cov-report=term-missing

test-unit:
	pytest tests/test_*.py -v

test-integration:
	pytest tests/integration/ -v

lint:
	flake8 ecommerce tests
	black --check ecommerce tests

format:
	black ecommerce tests

shell:
	docker-compose run --rm scraper python

db-shell:
	docker-compose exec postgres psql -U scraper_user -d ecommerce_prices

pgadmin:
	docker-compose --profile tools up -d pgadmin
	@echo "PgAdmin available at http://localhost:5050"

setup:
	./setup.sh

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8
	playwright install chromium

health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Database status:"
	@docker-compose exec -T postgres pg_isready -U scraper_user || echo "❌ Database not ready"
