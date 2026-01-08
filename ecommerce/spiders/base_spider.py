"""
Base spider class for e-commerce price scraping.

Provides common functionality for all platform-specific spiders.
"""

import scrapy
from scrapy.loader import ItemLoader
from ..items import LaptopItem
import re


class BaseEcommerceSpider(scrapy.Spider):
    """
    Base spider with common functionality for all e-commerce platforms.

    Platform-specific spiders should inherit from this class and implement:
    - start_urls
    - parse() method
    - _extract_specs() method (optional, platform-specific)
    """

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform_name = self.name  # Spider name = platform name

    def create_loader(self, response, selector=None):
        """
        Create ItemLoader with platform context.

        Args:
            response: Scrapy response object
            selector: Optional selector for the item

        Returns:
            ItemLoader instance
        """
        if selector:
            loader = ItemLoader(item=LaptopItem(), selector=selector, response=response)
        else:
            loader = ItemLoader(item=LaptopItem(), response=response)

        loader.add_value("platform", self.platform_name)
        loader.add_value("url", response.url)

        return loader

    def extract_brand_from_name(self, product_name):
        """
        Extract laptop brand from product name.

        Args:
            product_name: Product title/name string

        Returns:
            Brand name or None
        """
        if not product_name:
            return None

        brands = [
            "Dell",
            "HP",
            "Lenovo",
            "Asus",
            "Acer",
            "Apple",
            "MSI",
            "Razer",
            "Microsoft",
            "Samsung",
            "Huawei",
            "LG",
            "Toshiba",
            "Sony",
            "Fujitsu",
            "Alienware",
            "ThinkPad",
            "MacBook",
        ]

        product_name_lower = product_name.lower()
        for brand in brands:
            if brand.lower() in product_name_lower:
                return brand

        return None

    def clean_price(self, price_text):
        """
        Clean and extract price from text.

        Args:
            price_text: Price string (e.g., "KES 75,000", "75000")

        Returns:
            Float price or None
        """
        if not price_text:
            return None

        # Remove non-numeric characters except decimal point
        price_clean = re.sub(r"[^\d.]", "", str(price_text))

        try:
            return float(price_clean)
        except ValueError:
            self.logger.warning(f"Could not parse price: {price_text}")
            return None

    def parse_specs_from_description(self, description):
        """
        Extract specifications from product description text.

        Args:
            description: Product description text

        Returns:
            Dictionary with extracted specs
        """
        specs = {}

        if not description:
            return specs

        description_lower = description.lower()

        # Extract RAM
        ram_match = re.search(r"(\d+)\s*gb\s*(ram|memory)", description_lower)
        if ram_match:
            specs["ram"] = f"{ram_match.group(1)}GB"

        # Extract storage
        storage_patterns = [
            r"(\d+)\s*gb\s*ssd",
            r"(\d+)\s*tb\s*ssd",
            r"(\d+)\s*gb\s*hdd",
            r"(\d+)\s*tb\s*hdd",
        ]
        for pattern in storage_patterns:
            storage_match = re.search(pattern, description_lower)
            if storage_match:
                unit = "TB" if "tb" in pattern else "GB"
                storage_type = "SSD" if "ssd" in pattern else "HDD"
                specs["storage"] = f"{storage_match.group(1)}{unit} {storage_type}"
                break

        # Extract processor
        processor_brands = ["intel", "amd", "apple m1", "apple m2", "ryzen"]
        for brand in processor_brands:
            if brand in description_lower:
                # Try to extract full processor name
                if brand == "intel":
                    proc_match = re.search(
                        r"intel\s+(?:core\s+)?([a-z]\d+(?:-\d+)?[a-z]?)",
                        description_lower,
                    )
                    if proc_match:
                        specs["processor"] = f"Intel {proc_match.group(1).upper()}"
                elif brand == "amd" or brand == "ryzen":
                    proc_match = re.search(
                        r"(ryzen\s+\d+\s+\d+[a-z]*)", description_lower
                    )
                    if proc_match:
                        specs["processor"] = proc_match.group(1).title()
                else:
                    specs["processor"] = brand.title()
                break

        # Extract screen size
        screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\'\')', description_lower)
        if screen_match:
            specs["screen_size"] = f"{screen_match.group(1)} inches"

        return specs
