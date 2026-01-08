"""
Item definitions for the e-commerce price scraper.

Defines the data structure for scraped laptop products with validation.
"""

import scrapy
from itemadapter import ItemAdapter
from scrapy.loader.processors import TakeFirst, MapCompose, Join
import re
from decimal import Decimal, InvalidOperation


def clean_text(value):
    """Remove extra whitespace and normalize text."""
    if value:
        return " ".join(str(value).split())
    return value


def extract_price(value):
    """Extract numeric price from text (handles KES, commas, etc)."""
    if not value:
        return None

    # Remove currency symbols and text
    price_str = re.sub(r"[^\d.,]", "", str(value))
    # Remove commas
    price_str = price_str.replace(",", "")

    try:
        return float(price_str)
    except (ValueError, InvalidOperation):
        return None


def validate_url(value):
    """Ensure URL is properly formatted."""
    if value and isinstance(value, str):
        if not value.startswith(("http://", "https://")):
            return f"https://{value}"
        return value
    return value


class LaptopItem(scrapy.Item):
    """
    Laptop product item with comprehensive fields.

    Fields:
        platform: E-commerce platform name (jumia, masoko, phoneplace, laptopclinic)
        product_name: Full product name/title
        brand: Laptop brand (Dell, HP, Lenovo, etc.)
        model: Specific model identifier
        price: Price in KES (Kenyan Shillings)
        original_price: Original price if on sale
        currency: Currency code (default: KES)
        url: Product page URL
        image_url: Product image URL
        processor: CPU information
        ram: RAM size (e.g., "8GB", "16GB")
        storage: Storage capacity (e.g., "256GB SSD", "1TB HDD")
        screen_size: Display size (e.g., "15.6 inches")
        graphics: GPU information
        operating_system: OS (Windows 11, Ubuntu, etc.)
        condition: New/Refurbished/Used
        availability: In stock status
        specs: Additional specifications (JSON-compatible dict)
        scraped_at: Timestamp of scraping
    """

    # Core fields
    platform = scrapy.Field(
        input_processor=MapCompose(clean_text, str.lower), output_processor=TakeFirst()
    )

    product_name = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    brand = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    model = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Pricing
    price = scrapy.Field(
        input_processor=MapCompose(extract_price), output_processor=TakeFirst()
    )

    original_price = scrapy.Field(
        input_processor=MapCompose(extract_price), output_processor=TakeFirst()
    )

    currency = scrapy.Field(output_processor=TakeFirst())

    # URLs
    url = scrapy.Field(
        input_processor=MapCompose(validate_url, str.strip),
        output_processor=TakeFirst(),
    )

    image_url = scrapy.Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )

    # Specifications
    processor = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    ram = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    storage = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    screen_size = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    graphics = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    operating_system = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Product status
    condition = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    availability = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Metadata
    specs = scrapy.Field()  # Dictionary of additional specs
    scraped_at = scrapy.Field()

    # Internal fields for processing
    _duplicate_key = scrapy.Field()  # Used for deduplication


def validate_laptop_item(item):
    """
    Validate laptop item before storage.

    Args:
        item: LaptopItem instance

    Returns:
        tuple: (is_valid, error_messages)
    """
    adapter = ItemAdapter(item)
    errors = []

    # Required fields
    required_fields = ["platform", "product_name", "price", "url"]
    for field in required_fields:
        if not adapter.get(field):
            errors.append(f"Missing required field: {field}")

    # Price validation
    price = adapter.get("price")
    if price is not None:
        try:
            price_float = float(price)
            if price_float < 15000 or price_float > 500000:
                errors.append(
                    f"Price {price_float} KES out of reasonable range (15000-500000)"
                )
        except (ValueError, TypeError):
            errors.append(f"Invalid price format: {price}")

    # Platform validation
    valid_platforms = ["jumia", "masoko", "phoneplace", "laptopclinic"]
    platform = adapter.get("platform")
    if platform and platform.lower() not in valid_platforms:
        errors.append(f"Invalid platform: {platform}")

    # URL validation
    url = adapter.get("url")
    if url and not url.startswith(("http://", "https://")):
        errors.append(f"Invalid URL format: {url}")

    return len(errors) == 0, errors
