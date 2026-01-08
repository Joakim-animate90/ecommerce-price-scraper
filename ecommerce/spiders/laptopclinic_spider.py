"""
LaptopClinic Kenya spider.

Scrapes laptop listings from LaptopClinic Kenya
"""

import scrapy
from scrapy.loader import ItemLoader
from .base_spider import BaseEcommerceSpider
from ..items import LaptopItem


class LaptopClinicSpider(BaseEcommerceSpider):
    """Spider for scraping laptop prices from LaptopClinic Kenya."""

    name = "laptopclinic"
    allowed_domains = ["laptopclinickenya.co.ke", "laptopclinic.co.ke"]

    start_urls = [
        "https://www.laptopclinickenya.co.ke/shop/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def parse(self, response):
        """
        Parse laptop listing page.

        Note: Selectors are templates - update based on actual site structure.
        """
        # Extract product containers
        products = response.css("div.product")

        if not products:
            products = response.css("li.product-item")

        self.logger.info(f"Found {len(products)} products on page")

        for product in products:
            # Get product link
            product_url = product.css("a.product-link::attr(href)").get()
            if not product_url:
                product_url = product.css("h3 a::attr(href)").get()
            if not product_url:
                product_url = product.css("a::attr(href)").get()

            if product_url:
                yield response.follow(product_url, callback=self.parse_product)

        # Pagination
        next_page = response.css("a.next-page::attr(href)").get()
        if not next_page:
            next_page = response.css("a.next::attr(href)").get()
        if not next_page:
            next_page = response.css('link[rel="next"]::attr(href)').get()

        if next_page:
            self.logger.info(f"Following pagination: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """Parse individual product page."""
        loader = self.create_loader(response)

        # Product name
        product_name = response.css("h1.product-title::text").get()
        if not product_name:
            product_name = response.css("h1::text").get()

        if product_name:
            loader.add_value("product_name", product_name.strip())
            brand = self.extract_brand_from_name(product_name)
            if brand:
                loader.add_value("brand", brand)

        # Price
        price = response.css("span.woocommerce-Price-amount bdi::text").get()
        if not price:
            price = response.css("span.price ins bdi::text").get()
        if not price:
            price = response.css("span.price bdi::text").get()
        if not price:
            price = response.css("p.price::text").get()

        if price:
            loader.add_value("price", price)

        # Original price (if on sale)
        original_price = response.css("span.price del bdi::text").get()
        if original_price:
            loader.add_value("original_price", original_price)

        # Image
        image_url = response.css("img.wp-post-image::attr(src)").get()
        if not image_url:
            image_url = response.css("div.product-images img::attr(src)").get()

        if image_url:
            loader.add_value("image_url", image_url)

        # Availability
        availability = response.css("p.stock::text").get()
        if availability:
            loader.add_value("availability", availability.strip())

        # Specifications from WooCommerce attributes
        specs_dict = {}

        # Try WooCommerce product attributes
        attr_rows = response.css("table.woocommerce-product-attributes tr")
        for row in attr_rows:
            label = row.css("th::text").get()
            value = row.css("td ::text").get()

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
                elif "graphic" in label or "gpu" in label or "vga" in label:
                    loader.add_value("graphics", value)
                elif "os" in label or "operating" in label:
                    loader.add_value("operating_system", value)
                elif "condition" in label:
                    loader.add_value("condition", value)
                else:
                    specs_dict[label] = value

        # Product description
        description_parts = []

        # Short description
        short_desc = response.css(
            "div.woocommerce-product-details__short-description ::text"
        ).getall()
        description_parts.extend(short_desc)

        # Full description
        full_desc = response.css("div#tab-description ::text").getall()
        description_parts.extend(full_desc)

        description = " ".join(description_parts)

        if description:
            parsed_specs = self.parse_specs_from_description(description)

            # Fill missing specs from parsed description
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

        # Default condition
        if not loader.get_output_value("condition"):
            # Check if refurbished is mentioned
            if description and (
                "refurbished" in description.lower() or "renewed" in description.lower()
            ):
                loader.add_value("condition", "Refurbished")
            else:
                loader.add_value("condition", "New")

        yield loader.load_item()
