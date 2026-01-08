"""
Jumia Kenya laptop spider.

Scrapes laptop listings from Jumia.co.ke
"""

import scrapy
from scrapy.loader import ItemLoader
from .base_spider import BaseEcommerceSpider
from ..items import LaptopItem


class JumiaSpider(BaseEcommerceSpider):
    """Spider for scraping laptop prices from Jumia Kenya."""

    name = "jumia"
    allowed_domains = ["jumia.co.ke"]

    start_urls = [
        "https://www.jumia.co.ke/laptops/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def parse(self, response):
        """
        Parse laptop listing page and extract product links.

        This is a template - actual selectors need to be verified
        by inspecting Jumia's current HTML structure.
        """
        # Extract product links
        product_links = response.css("article.prd a.core::attr(href)").getall()

        if not product_links:
            # Fallback selectors
            product_links = response.css("a.link::attr(href)").getall()

        self.logger.info(f"Found {len(product_links)} products on page")

        # Follow product links
        for link in product_links:
            if link:
                yield response.follow(link, callback=self.parse_product)

        # Follow pagination
        next_page = response.css('a[aria-label="Next Page"]::attr(href)').get()
        if next_page:
            self.logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """
        Parse individual product page and extract laptop details.

        Note: Selectors are templates and should be verified/updated
        based on actual Jumia website structure.
        """
        loader = self.create_loader(response)

        # Product name
        product_name = response.css("h1.title::text").get()
        if not product_name:
            product_name = response.css("h1::text").get()

        if product_name:
            loader.add_value("product_name", product_name.strip())

            # Extract brand from product name
            brand = self.extract_brand_from_name(product_name)
            if brand:
                loader.add_value("brand", brand)

        # Price
        price = response.css("span.price-has-discount::text").get()
        if not price:
            price = response.css("span.-b::text").get()
        if not price:
            price = response.css('[class*="price"]::text').get()

        if price:
            loader.add_value("price", price)

        # Original price (if on sale)
        original_price = response.css("span.price-old::text").get()
        if original_price:
            loader.add_value("original_price", original_price)

        # Image
        image_url = response.css("img.img::attr(src)").get()
        if not image_url:
            image_url = response.css('img[itemprop="image"]::attr(src)').get()

        if image_url:
            loader.add_value("image_url", image_url)

        # Availability
        availability = response.css("p.availability::text").get()
        if availability:
            loader.add_value("availability", availability.strip())

        # Specifications from table
        specs_dict = {}

        # Try to extract from specification table
        spec_rows = response.css("table.specifications tr")
        for row in spec_rows:
            key = row.css("th::text").get()
            value = row.css("td::text").get()

            if key and value:
                key = key.strip().lower()
                value = value.strip()

                if "processor" in key or "cpu" in key:
                    loader.add_value("processor", value)
                elif "ram" in key or "memory" in key:
                    loader.add_value("ram", value)
                elif "storage" in key or "hard" in key or "ssd" in key:
                    loader.add_value("storage", value)
                elif "screen" in key or "display" in key:
                    loader.add_value("screen_size", value)
                elif "graphic" in key or "gpu" in key:
                    loader.add_value("graphics", value)
                elif "operating system" in key or "os" in key:
                    loader.add_value("operating_system", value)
                else:
                    specs_dict[key] = value

        # Product description for additional spec extraction
        description = " ".join(response.css("div.description ::text").getall())
        if description:
            parsed_specs = self.parse_specs_from_description(description)

            # Add parsed specs if not already present
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

        # Add additional specs
        loader.add_value("specs", specs_dict)
        loader.add_value("condition", "New")  # Default for Jumia

        yield loader.load_item()
