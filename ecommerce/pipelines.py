"""
Item pipelines for processing scraped data.

Pipeline order:
1. ValidationPipeline - Validates item fields
2. DeduplicationPipeline - Removes duplicate items
3. PostgreSQLPipeline - Stores data in PostgreSQL database
"""

import logging
import hashlib
from datetime import datetime
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from .items import validate_laptop_item


class ValidationPipeline:
    """
    Validates scraped items before further processing.
    Drops items that don't meet validation criteria.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_item(self, item, spider):
        """Validate item and drop if invalid."""
        adapter = ItemAdapter(item)

        # Run validation
        is_valid, errors = validate_laptop_item(item)

        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.warning(
                f"Dropping invalid item from {adapter.get('url')}: {error_msg}"
            )
            raise DropItem(f"Validation failed: {error_msg}")

        # Add timestamp if not present
        if not adapter.get("scraped_at"):
            adapter["scraped_at"] = datetime.now()

        # Set default currency
        if not adapter.get("currency"):
            adapter["currency"] = "KES"

        self.logger.debug(f"Validated item: {adapter.get('product_name')}")
        return item


class DeduplicationPipeline:
    """
    Removes duplicate items within the same scraping session.
    Uses product URL and platform as unique identifier.
    """

    def __init__(self):
        self.seen_items = set()
        self.logger = logging.getLogger(__name__)

    def process_item(self, item, spider):
        """Check for duplicates and drop if found."""
        adapter = ItemAdapter(item)

        # Create unique key from platform and URL
        platform = adapter.get("platform", "").lower()
        url = adapter.get("url", "")

        duplicate_key = hashlib.md5(f"{platform}:{url}".encode("utf-8")).hexdigest()

        if duplicate_key in self.seen_items:
            self.logger.debug(f"Duplicate item found: {url}")
            raise DropItem(f"Duplicate item: {url}")

        self.seen_items.add(duplicate_key)
        adapter["_duplicate_key"] = duplicate_key

        return item

    def close_spider(self, spider):
        """Clear seen items when spider closes."""
        self.logger.info(f"Processed {len(self.seen_items)} unique items")
        self.seen_items.clear()


class PostgreSQLPipeline:
    """
    Stores scraped items in PostgreSQL database.

    Features:
    - Connection pooling for efficient database access
    - Upsert logic (insert or update if exists)
    - Price history tracking
    - Error handling and logging
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self.items_saved = 0
        self.items_updated = 0
        self.items_failed = 0

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize pipeline with database configuration from settings."""
        db_config = crawler.settings.get("POSTGRES_CONFIG")
        return cls(db_config)

    def open_spider(self, spider):
        """Create database connection pool when spider opens."""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"],
            )
            self.logger.info("Database connection pool created successfully")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to create database connection pool: {e}")
            raise

    def close_spider(self, spider):
        """Close all database connections when spider closes."""
        if self.pool:
            self.pool.closeall()
            self.logger.info(
                f"Database pipeline stats - Saved: {self.items_saved}, "
                f"Updated: {self.items_updated}, "
                f"Failed: {self.items_failed}"
            )

    def process_item(self, item, spider):
        """Store item in database."""
        adapter = ItemAdapter(item)
        conn = None

        try:
            conn = self.pool.getconn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Check if product exists
            existing_id = self._check_existing_product(cursor, adapter)

            if existing_id:
                # Update existing product
                self._update_product(cursor, existing_id, adapter)
                self.items_updated += 1
            else:
                # Insert new product
                product_id = self._insert_product(cursor, adapter)
                existing_id = product_id
                self.items_saved += 1

            # Track price history
            self._track_price_history(cursor, existing_id, adapter)

            conn.commit()
            cursor.close()

            self.logger.debug(
                f"Stored item: {adapter.get('product_name')} "
                f"(Price: {adapter.get('price')} KES)"
            )

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            self.items_failed += 1
            # Don't raise - allow pipeline to continue

        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Unexpected error storing item: {e}")
            self.items_failed += 1

        finally:
            if conn:
                self.pool.putconn(conn)

        return item

    def _check_existing_product(self, cursor, adapter):
        """Check if product already exists in database."""
        query = """
            SELECT id FROM laptops
            WHERE platform = %s AND url = %s
            LIMIT 1
        """
        cursor.execute(query, (adapter.get("platform"), adapter.get("url")))
        result = cursor.fetchone()
        return result["id"] if result else None

    def _insert_product(self, cursor, adapter):
        """Insert new product into database."""
        specs = adapter.get("specs", {})
        if not isinstance(specs, dict):
            specs = {}

        query = """
            INSERT INTO laptops (
                platform, product_name, brand, model, price, original_price,
                currency, url, image_url, processor, ram, storage, screen_size,
                graphics, operating_system, condition, availability, specs,
                scraped_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            ) RETURNING id
        """

        cursor.execute(
            query,
            (
                adapter.get("platform"),
                adapter.get("product_name"),
                adapter.get("brand"),
                adapter.get("model"),
                adapter.get("price"),
                adapter.get("original_price"),
                adapter.get("currency", "KES"),
                adapter.get("url"),
                adapter.get("image_url"),
                adapter.get("processor"),
                adapter.get("ram"),
                adapter.get("storage"),
                adapter.get("screen_size"),
                adapter.get("graphics"),
                adapter.get("operating_system"),
                adapter.get("condition"),
                adapter.get("availability"),
                Json(specs),
                adapter.get("scraped_at", datetime.now()),
                datetime.now(),
            ),
        )

        result = cursor.fetchone()
        return result["id"]

    def _update_product(self, cursor, product_id, adapter):
        """Update existing product in database."""
        specs = adapter.get("specs", {})
        if not isinstance(specs, dict):
            specs = {}

        query = """
            UPDATE laptops SET
                product_name = %s, brand = %s, model = %s, price = %s,
                original_price = %s, currency = %s, image_url = %s,
                processor = %s, ram = %s, storage = %s, screen_size = %s,
                graphics = %s, operating_system = %s, condition = %s,
                availability = %s, specs = %s, updated_at = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                adapter.get("product_name"),
                adapter.get("brand"),
                adapter.get("model"),
                adapter.get("price"),
                adapter.get("original_price"),
                adapter.get("currency", "KES"),
                adapter.get("image_url"),
                adapter.get("processor"),
                adapter.get("ram"),
                adapter.get("storage"),
                adapter.get("screen_size"),
                adapter.get("graphics"),
                adapter.get("operating_system"),
                adapter.get("condition"),
                adapter.get("availability"),
                Json(specs),
                datetime.now(),
                product_id,
            ),
        )

    def _track_price_history(self, cursor, product_id, adapter):
        """Track price changes in price_history table."""
        query = """
            INSERT INTO price_history (
                laptop_id, price, currency, recorded_at
            ) VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_id,
                adapter.get("price"),
                adapter.get("currency", "KES"),
                adapter.get("scraped_at", datetime.now()),
            ),
        )
