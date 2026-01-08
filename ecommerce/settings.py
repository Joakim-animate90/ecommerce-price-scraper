"""
Scrapy settings for ecommerce price scraper project.

This configuration implements production-grade settings including:
- Concurrent request handling with rate limiting
- User-Agent rotation to avoid blocking
- Playwright integration for JavaScript-rendered content
- Retry logic with exponential backoff
- Database pipeline for PostgreSQL storage
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_NAME = "ecommerce"

SPIDER_MODULES = ["ecommerce.spiders"]
NEWSPIDER_MODULE = "ecommerce.spiders"

# ============================================================================
# CRAWLING POLITENESS & PERFORMANCE
# ============================================================================

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrent requests (balances speed with server load)
CONCURRENT_REQUESTS = int(os.getenv("SCRAPER_CONCURRENT_REQUESTS", 16))
CONCURRENT_REQUESTS_PER_DOMAIN = 4
CONCURRENT_REQUESTS_PER_IP = 4

# Download delay with randomization (2-5 seconds)
DOWNLOAD_DELAY = int(os.getenv("SCRAPER_DOWNLOAD_DELAY", 2))
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle for adaptive throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# ============================================================================
# USER-AGENT ROTATION (Avoid blocking)
# ============================================================================

USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Default headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Enable spider middlewares
SPIDER_MIDDLEWARES = {
    "ecommerce.middlewares.EcommerceSpiderMiddleware": 543,
}

# Enable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "ecommerce.middlewares.UserAgentRotationMiddleware": 400,
    "ecommerce.middlewares.EcommerceDownloaderMiddleware": 543,
}

# ============================================================================
# PLAYWRIGHT CONFIGURATION (JavaScript-rendered content)
# ============================================================================

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

# ============================================================================
# ITEM PIPELINES
# ============================================================================

ITEM_PIPELINES = {
    "ecommerce.pipelines.ValidationPipeline": 100,
    "ecommerce.pipelines.DeduplicationPipeline": 200,
    "ecommerce.pipelines.PostgreSQLPipeline": 300,
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "ecommerce_prices"),
    "user": os.getenv("POSTGRES_USER", "scraper_user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
RETRY_PRIORITY_ADJUST = -1

# Exponential backoff for retries
RETRY_BACKOFF_ENABLED = True
RETRY_BACKOFF_MAX_DELAY = 30

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# HTTP CACHING (for development/testing)
# ============================================================================

HTTPCACHE_ENABLED = os.getenv("HTTPCACHE_ENABLED", "False").lower() == "true"
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# ============================================================================
# TELEMETRY & EXTENSIONS
# ============================================================================

EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.logstats.LogStats": 0,
}

# Stats collection
STATS_CLASS = "scrapy.statscollectors.MemoryStatsCollector"

# ============================================================================
# SECURITY & COOKIES
# ============================================================================

COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Redirect settings
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

# DNS timeout
DNS_TIMEOUT = 60

# ============================================================================
# FEED EXPORT
# ============================================================================

FEED_EXPORT_ENCODING = "utf-8"

# ============================================================================
# REQUEST FINGERPRINTING
# ============================================================================

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
