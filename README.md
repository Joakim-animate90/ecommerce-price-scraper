# E-Commerce Laptop Price Scraper

A production-grade web scraping system that monitors laptop prices across 4 major Kenyan e-commerce platforms (Jumia, Masoko, PhonePlace, and LaptopClinic), stores the data in PostgreSQL, and visualizes price comparisons using Apache Superset.

![Python](https://img.shields.io/badge/python-3.11-blue)
![Scrapy](https://img.shields.io/badge/scrapy-2.11-green)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Features

- **Multi-Platform Scraping**: Scrapes 4 Kenyan e-commerce platforms
- **JavaScript Rendering**: Playwright integration for dynamic content
- **Smart Rate Limiting**: Configurable concurrent requests with random delays
- **User-Agent Rotation**: Avoid detection and blocking
- **Data Validation**: Comprehensive validation with price range checks
- **Deduplication**: Automatic duplicate detection and removal
- **PostgreSQL Storage**: Robust database with connection pooling
- **Price History Tracking**: Track price changes over time
- **Beautiful Dashboards**: Apache Superset for data visualization
- **CI/CD Pipeline**: Automated testing and Docker image building
- **Production-Ready**: Error handling, logging, monitoring

## 📁 Project Structure

```
ecommerce-price-scraper/
├── ecommerce/                  # Scrapy project
│   ├── spiders/               # Spider implementations
│   │   ├── base_spider.py     # Base spider class
│   │   ├── jumia_spider.py
│   │   ├── masoko_spider.py
│   │   ├── phoneplace_spider.py
│   │   └── laptopclinic_spider.py
│   ├── items.py               # Data models with validation
│   ├── pipelines.py           # Database pipelines
│   ├── middlewares.py         # Custom middleware
│   └── settings.py            # Scrapy configuration
├── postgres_setup/            # Database setup
│   ├── init.sql              # Schema, indexes, views
│   └── Dockerfile            # PostgreSQL container
├── superset_config/          # Superset configuration
│   ├── superset_config.py
│   └── dashboard_template.json
├── tests/                    # Test suite
│   ├── test_items.py
│   ├── test_pipelines.py
│   ├── test_spiders.py
│   └── integration/
├── .github/workflows/        # CI/CD pipelines
│   ├── ci-cd.yml
│   └── scheduled-scraping.yml
├── docker-compose.yml        # Service orchestration
├── Dockerfile               # Scraper container
├── requirements.txt         # Python dependencies
└── README.md
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Web Scraping** | Scrapy 2.11, Scrapy-Playwright |
| **JavaScript Rendering** | Playwright (Chromium) |
| **Database** | PostgreSQL 15 |
| **Visualization** | Apache Superset |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Testing** | pytest, pytest-cov |
| **Code Quality** | black, flake8 |

## 📋 Prerequisites

- Docker and Docker Compose (20.10+)
- Python 3.11+ (for local development)
- Git
- 4GB+ RAM recommended
- Linux/macOS/Windows with WSL2

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Joakim-animate90/ecommerce-price-scraper.git
cd ecommerce-price-scraper
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

**Important**: Update these values in `.env`:
- `POSTGRES_PASSWORD`: Strong database password
- `SUPERSET_SECRET_KEY`: Random secret key
- `SUPERSET_ADMIN_PASSWORD`: Admin dashboard password

### 3. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start database and Superset
docker-compose up -d postgres superset

# Wait for services to initialize (30-60 seconds)
docker-compose logs -f superset

# Run the scraper
docker-compose up scraper
```

### 4. Access the Dashboard

- **Superset Dashboard**: http://localhost:8088
  - Username: `admin` (or your `SUPERSET_ADMIN_USER`)
  - Password: `admin` (or your `SUPERSET_ADMIN_PASSWORD`)

- **PgAdmin** (optional): http://localhost:5050
  - Email: `admin@localhost`
  - Password: `admin`

## 🔧 Configuration

### Scraper Settings

Edit [ecommerce/settings.py](ecommerce/settings.py) or use environment variables:

```bash
# Concurrent requests
SCRAPER_CONCURRENT_REQUESTS=16

# Download delay (seconds)
SCRAPER_DOWNLOAD_DELAY=2

# Log level
LOG_LEVEL=INFO

# Enable HTTP caching for development
HTTPCACHE_ENABLED=False
```

### Database Configuration

Database schema is automatically initialized from [postgres_setup/init.sql](postgres_setup/init.sql).

Key features:
- **Tables**: `laptops`, `price_history`
- **Indexes**: Optimized for common queries
- **Views**: Pre-built analytics views
- **Constraints**: Data integrity checks

## 📊 Database Schema

### Laptops Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| platform | VARCHAR(50) | E-commerce platform |
| product_name | VARCHAR(500) | Product title |
| brand | VARCHAR(100) | Laptop brand |
| price | DECIMAL(10,2) | Current price (KES) |
| url | TEXT | Product URL |
| processor | VARCHAR(200) | CPU info |
| ram | VARCHAR(50) | RAM size |
| storage | VARCHAR(100) | Storage capacity |
| specs | JSONB | Additional specs |
| scraped_at | TIMESTAMP | First scrape time |
| updated_at | TIMESTAMP | Last update time |

### Price History Table

Tracks price changes over time for trend analysis.

## 🕷️ Running Spiders

### Run All Spiders

```bash
docker-compose up scraper
```

### Run Specific Spider

```bash
# Run locally
scrapy crawl jumia

# Run in Docker
docker-compose run scraper scrapy crawl masoko
```

### Available Spiders

- `jumia` - Jumia Kenya
- `masoko` - Masoko
- `phoneplace` - PhonePlace Kenya
- `laptopclinic` - LaptopClinic Kenya

## 📈 Superset Dashboard Setup

### 1. Connect Database

After logging into Superset:

1. Go to **Data** → **Databases** → **+ Database**
2. Select **PostgreSQL**
3. Enter connection details:
   ```
   Host: postgres
   Port: 5432
   Database: ecommerce_prices
   Username: scraper_user
   Password: <your-password>
   ```

### 2. Create Dataset

1. Go to **Data** → **Datasets** → **+ Dataset**
2. Select database: PostgreSQL
3. Select table: `laptops`
4. Click **Add**

### 3. Create Charts

Pre-built chart configurations are available in [superset_config/dashboard_template.json](superset_config/dashboard_template.json).

**Recommended Charts**:
- Price comparison bar chart
- Platform distribution pie chart
- Price trends line chart
- Latest listings table
- Top deals table

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=ecommerce --cov-report=html
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/test_items.py -v

# Integration tests
pytest tests/integration/ -v

# Skip slow tests
pytest -m "not slow"
```

### Test Coverage

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

1. **CI/CD Pipeline** ([.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml))
   - Runs on push to main/develop
   - Linting (flake8, black)
   - Unit and integration tests
   - Build and push Docker images
   - Test coverage reporting

2. **Scheduled Scraping** ([.github/workflows/scheduled-scraping.yml](.github/workflows/scheduled-scraping.yml))
   - Runs daily at 2 AM UTC
   - Executes all spiders
   - Uploads logs as artifacts

### Required Secrets

Add these to your GitHub repository secrets:

```
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DOCKERHUB_USERNAME  (optional)
DOCKERHUB_TOKEN     (optional)
```

## 📦 Docker Images

### Pull Pre-Built Images

```bash
# From GitHub Container Registry
docker pull ghcr.io/joakim-animate90/ecommerce-price-scraper-scraper:latest

# From Docker Hub (if published)
docker pull username/ecommerce-scraper:latest
```

### Build Locally

```bash
# Build scraper
docker build -t ecommerce-scraper:latest .

# Build database
docker build -t ecommerce-postgres:latest ./postgres_setup
```

## 🔍 Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f scraper
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 scraper
```

### Scrapy Statistics

Scrapy outputs statistics after each run:
- Items scraped
- Items dropped
- Requests made
- Download errors
- Response status codes

### Database Monitoring

```bash
# Check database size
docker-compose exec postgres psql -U scraper_user -d ecommerce_prices -c "
  SELECT 
    pg_size_pretty(pg_database_size('ecommerce_prices')) as db_size,
    (SELECT count(*) FROM laptops) as total_laptops,
    (SELECT count(*) FROM price_history) as price_records;
"

# View latest prices
docker-compose exec postgres psql -U scraper_user -d ecommerce_prices -c "
  SELECT platform, count(*), avg(price), min(price), max(price)
  FROM laptops
  GROUP BY platform;
"
```

## 🛡️ Production Considerations

### Security

- ✅ Use strong passwords (20+ characters)
- ✅ Store secrets in environment variables
- ✅ Never commit `.env` file
- ✅ Use HTTPS in production
- ✅ Regularly update dependencies
- ✅ Implement rate limiting
- ✅ Monitor for blocked IPs

### Performance Optimization

- Adjust `CONCURRENT_REQUESTS` based on target sites
- Use `DOWNLOAD_DELAY` to be respectful
- Enable HTTP caching for development
- Set up database connection pooling
- Add indexes for frequent queries
- Monitor memory usage

### Legal and Ethical

- ⚠️ **Respect robots.txt** - Configured by default
- ⚠️ **Terms of Service** - Review each platform's ToS
- ⚠️ **Rate Limiting** - Avoid overwhelming servers
- ⚠️ **Data Usage** - Only for permitted purposes
- ⚠️ **Attribution** - Credit data sources appropriately

## 🐛 Troubleshooting

### Common Issues

**1. Spider returns no items**
- Verify CSS selectors are current (websites change!)
- Check logs for HTTP errors
- Inspect actual HTML structure

**2. Database connection fails**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**3. Playwright browser issues**
```bash
# Reinstall browsers in container
docker-compose run scraper playwright install chromium
```

**4. Out of memory**
```bash
# Reduce concurrent requests
SCRAPER_CONCURRENT_REQUESTS=8 docker-compose up scraper
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG docker-compose up scraper

# Run spider with more details
docker-compose run scraper scrapy crawl jumia -L DEBUG
```

## 📝 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r ecommerce/requirements.txt

# Install Playwright browsers
playwright install chromium

# Run tests
pytest

# Format code
black ecommerce/

# Lint
flake8 ecommerce/
```

### Adding New Spiders

1. Create spider file in `ecommerce/spiders/`
2. Inherit from `BaseEcommerceSpider`
3. Implement `parse()` and `parse_product()` methods
4. Update `allowed_domains` and `start_urls`
5. Add tests in `tests/test_spiders.py`

Example:
```python
from .base_spider import BaseEcommerceSpider

class NewSiteSpider(BaseEcommerceSpider):
    name = 'newsite'
    allowed_domains = ['newsite.com']
    start_urls = ['https://www.newsite.com/laptops']
    
    def parse(self, response):
        # Extract product links
        for link in response.css('a.product::attr(href)'):
            yield response.follow(link, self.parse_product)
    
    def parse_product(self, response):
        loader = self.create_loader(response)
        loader.add_css('product_name', 'h1::text')
        loader.add_css('price', 'span.price::text')
        yield loader.load_item()
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Write docstrings for all functions
- Add tests for new features
- Run `black` and `flake8` before committing

## 📧 Contact

**Project Author**: Joakim Animate  
**Repository**: https://github.com/Joakim-animate90/ecommerce-price-scraper

## 🙏 Acknowledgments

- Scrapy framework team
- Playwright developers
- PostgreSQL community
- Apache Superset team

---

**⚡ Built with Scrapy, PostgreSQL, and Docker for production-grade web scraping**
