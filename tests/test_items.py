"""
Unit tests for items.py
"""

from ecommerce.items import (
    LaptopItem,
    clean_text,
    extract_price,
    validate_url,
    validate_laptop_item,
)
from itemadapter import ItemAdapter


class TestItemProcessors:
    """Test item field processors."""

    def test_clean_text(self):
        assert clean_text("  Hello  World  ") == "Hello World"
        assert clean_text("Multiple\n\nLines") == "Multiple Lines"
        assert clean_text(None) is None

    def test_extract_price(self):
        assert extract_price("KES 75,000") == 75000.0
        assert extract_price("75000") == 75000.0
        assert extract_price("KES 75,000.50") == 75000.50
        assert extract_price("Invalid") is None
        assert extract_price(None) is None

    def test_validate_url(self):
        assert validate_url("jumia.co.ke/product") == "https://jumia.co.ke/product"
        assert (
            validate_url("https://jumia.co.ke/product") == "https://jumia.co.ke/product"
        )
        assert validate_url(None) is None


class TestLaptopItem:
    """Test LaptopItem definition."""

    def test_create_item(self):
        item = LaptopItem()
        assert item is not None

    def test_item_fields(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        adapter = ItemAdapter(item)
        assert adapter.get("platform") == "jumia"
        assert adapter.get("product_name") == "Dell Inspiron 15"
        assert adapter.get("price") == 75000


class TestItemValidation:
    """Test item validation logic."""

    def test_valid_item(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        is_valid, errors = validate_laptop_item(item)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_fields(self):
        item = LaptopItem(platform="jumia", product_name="Dell Inspiron 15")

        is_valid, errors = validate_laptop_item(item)
        assert is_valid is False
        assert any("price" in error for error in errors)
        assert any("url" in error for error in errors)

    def test_invalid_price_range(self):
        # Price too low
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=5000,
            url="https://jumia.co.ke/product",
        )

        is_valid, errors = validate_laptop_item(item)
        assert is_valid is False
        assert any("range" in error.lower() for error in errors)

        # Price too high
        item["price"] = 600000
        is_valid, errors = validate_laptop_item(item)
        assert is_valid is False

    def test_invalid_platform(self):
        item = LaptopItem(
            platform="invalid_platform",
            product_name="Dell Inspiron 15",
            price=75000,
            url="https://jumia.co.ke/product",
        )

        is_valid, errors = validate_laptop_item(item)
        assert is_valid is False
        assert any("platform" in error.lower() for error in errors)

    def test_invalid_url_format(self):
        item = LaptopItem(
            platform="jumia",
            product_name="Dell Inspiron 15",
            price=75000,
            url="not-a-url",
        )

        is_valid, errors = validate_laptop_item(item)
        assert is_valid is False
        assert any("url" in error.lower() for error in errors)
