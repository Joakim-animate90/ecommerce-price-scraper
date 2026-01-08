"""
Unit tests for pipelines.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from scrapy.exceptions import DropItem
from ecommerce.pipelines import (
    ValidationPipeline,
    DeduplicationPipeline,
    PostgreSQLPipeline,
)
from ecommerce.items import LaptopItem
from itemadapter import ItemAdapter


class TestValidationPipeline:
    """Test ValidationPipeline."""

    def setup_method(self):
        self.pipeline = ValidationPipeline()
        self.spider = Mock()

    def test_valid_item_passes(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        result = self.pipeline.process_item(item, self.spider)
        assert result == item

    def test_invalid_item_dropped(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            # Missing required price and url
        )

        with pytest.raises(DropItem):
            self.pipeline.process_item(item, self.spider)

    def test_adds_timestamp(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        result = self.pipeline.process_item(item, self.spider)
        adapter = ItemAdapter(result)
        assert adapter.get("scraped_at") is not None

    def test_adds_default_currency(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        result = self.pipeline.process_item(item, self.spider)
        adapter = ItemAdapter(result)
        assert adapter.get("currency") == "KES"


class TestDeduplicationPipeline:
    """Test DeduplicationPipeline."""

    def setup_method(self):
        self.pipeline = DeduplicationPipeline()
        self.spider = Mock()

    def test_first_item_passes(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product1",
        )

        result = self.pipeline.process_item(item, self.spider)
        assert result == item

    def test_duplicate_item_dropped(self):
        item1 = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product1",
        )

        item2 = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product1",  # Same URL
        )

        self.pipeline.process_item(item1, self.spider)

        with pytest.raises(DropItem):
            self.pipeline.process_item(item2, self.spider)

    def test_different_items_pass(self):
        item1 = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product1",
        )

        item2 = LaptopItem(
            platform="jumia",
            product_name="HP Pavilion",
            price=80000,
            url="https://jumia.co.ke/product2",  # Different URL
        )

        result1 = self.pipeline.process_item(item1, self.spider)
        result2 = self.pipeline.process_item(item2, self.spider)

        assert result1 == item1
        assert result2 == item2


@pytest.mark.integration
class TestPostgreSQLPipeline:
    """Test PostgreSQLPipeline (integration test)."""

    @pytest.fixture
    def mock_db_config(self):
        return {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }

    @pytest.fixture
    def pipeline(self, mock_db_config):
        return PostgreSQLPipeline(mock_db_config)

    def test_initialization(self, pipeline, mock_db_config):
        assert pipeline.db_config == mock_db_config
        assert pipeline.pool is None
        assert pipeline.items_saved == 0

    @patch("ecommerce.pipelines.SimpleConnectionPool")
    def test_open_spider(self, mock_pool, pipeline):
        spider = Mock()
        pipeline.open_spider(spider)

        mock_pool.assert_called_once()
        assert pipeline.pool is not None
