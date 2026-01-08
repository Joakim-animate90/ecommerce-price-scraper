"""
PhonePlace Kenya laptop spider.

Scrapes laptop listings from PhonePlace Kenya
"""

import scrapy
from scrapy.loader import ItemLoader
from .base_spider import BaseEcommerceSpider
from ..items import LaptopItem


class PhonePlaceSpider(BaseEcommerceSpider):
    """Spider for scraping laptop prices from PhonePlace Kenya."""

    name = "phoneplace"
    allowed_domains = ["phoneplacekenya.com"]

    start_urls = [
        "https://www.phoneplacekenya.com/laptops",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def parse(self, response):
        """
        Parse laptop listing page.

        Note: Selectors are templates - update based on actual site.
        """
        # Extract product containers
        products = response.css("div.product-item")

        if not products:
            products = response.css("div.product")

        self.logger.info(f"Found {len(products)} products on page")

        for product in products:
            # Extract product URL
            product_url = product.css("a::attr(href)").get()

            if product_url:
                yield response.follow(product_url, callback=self.parse_product)

        # Pagination
        next_page = response.css("a.next::attr(href)").get()
        if not next_page:
            next_page = response.css('link[rel="next"]::attr(href)').get()

        if next_page:
            self.logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """Parse individual product page."""
        loader = self.create_loader(response)

        # Product name
        product_name = response.css("h1.product-name::text").get()
        if not product_name:
            product_name = response.css("h1::text").get()

        if product_name:
            loader.add_value("product_name", product_name.strip())
            brand = self.extract_brand_from_name(product_name)
            if brand:
                loader.add_value("brand", brand)

        # Price - try multiple selectors
        price = response.css("span.price::text").get()
        if not price:
            price = response.css("div.product-price span::text").get()
        if not price:
            price = response.css('[itemprop="price"]::attr(content)').get()

        if price:
            loader.add_value("price", price)

        # Original price (if discounted)
        original_price = response.css("span.regular-price::text").get()
        if not original_price:
            original_price = response.css("s.price::text").get()

        if original_price:
            loader.add_value("original_price", original_price)

        # Image
        image_url = response.css("img.product-image::attr(src)").get()
        if not image_url:
            image_url = response.css('img[itemprop="image"]::attr(src)').get()

        if image_url:
            loader.add_value("image_url", image_url)

        # Availability
        stock_status = response.css("span.stock-status::text").get()
        if stock_status:
            loader.add_value("availability", stock_status.strip())

        # Specifications
        specs_dict = {}

        # Try structured spec table
        spec_rows = response.css("table.product-specs tr")
        for row in spec_rows:
            label = row.css("td:first-child::text").get()
            value = row.css("td:last-child::text").get()

            if label and value:
                label = label.strip().lower().rstrip(":")
                value = value.strip()

                if "processor" in label or "cpu" in label:
                    loader.add_value("processor", value)
                elif "ram" in label or "memory" in label:
                    loader.add_value("ram", value)
                elif "storage" in label or "hard" in label or "ssd" in label:
                    loader.add_value("storage", value)
                elif "screen" in label or "display" in label:
                    loader.add_value("screen_size", value)
                elif "graphic" in label or "gpu" in label:
                    loader.add_value("graphics", value)
                elif "operating" in label or "os" in label:
                    loader.add_value("operating_system", value)
                elif "condition" in label:
                    loader.add_value("condition", value)
                else:
                    specs_dict[label] = value

        # Try unstructured specs
        spec_list = response.css("ul.product-features li::text").getall()
        for spec_text in spec_list:
            spec_text_lower = spec_text.lower()

            if "processor" in spec_text_lower or "cpu" in spec_text_lower:
                loader.add_value("processor", spec_text)
            elif "ram" in spec_text_lower or "memory" in spec_text_lower:
                loader.add_value("ram", spec_text)
            elif (
                "storage" in spec_text_lower
                or "ssd" in spec_text_lower
                or "hdd" in spec_text_lower
            ):
                loader.add_value("storage", spec_text)

        # Product description
        description = " ".join(response.css("div.product-description ::text").getall())
        if description:
            parsed_specs = self.parse_specs_from_description(description)

            # Fill in missing specs
            if not loader.get_output_value("processor") and "processor" in parsed_specs:
                loader.add_value("processor", parsed_specs["processor"])
            if not loader.get_output_value("ram") and "ram" in parsed_specs:
                loader.add_value("ram", parsed_specs["ram"])
            if not loader.get_output_value("storage") and "storage" in parsed_specs:
                loader.add_value("storage", parsed_specs["storage"])
            if (
                not loader.get_output_value("screen_size")
                and "screen_size" in parsed_specs
            ):
                loader.add_value("screen_size", parsed_specs["screen_size"])

        loader.add_value("specs", specs_dict)

        # Default condition if not specified
        if not loader.get_output_value("condition"):
            loader.add_value("condition", "New")

        yield loader.load_item()
