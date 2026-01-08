"""
Masoko Kenya laptop spider.

Scrapes laptop listings from Masoko.com
Note: Masoko may require JavaScript rendering - uses Playwright
"""

import scrapy
from scrapy.loader import ItemLoader
from .base_spider import BaseEcommerceSpider
from ..items import LaptopItem


class MasokoSpider(BaseEcommerceSpider):
    """Spider for scraping laptop prices from Masoko."""

    name = "masoko"
    allowed_domains = ["masoko.com"]

    start_urls = [
        "https://www.masoko.com/electronics/computers/laptops",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "PLAYWRIGHT_ENABLED": True,
    }

    def start_requests(self):
        """Start requests with Playwright for JavaScript rendering."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        ("wait_for_selector", "div.product-item", {"timeout": 10000}),
                    ],
                },
                errback=self.errback_close_page,
            )

    async def errback_close_page(self, failure):
        """Close Playwright page on error."""
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {failure.request.url}")

    async def parse(self, response):
        """
        Parse laptop listing page.

        Note: Selectors are templates - verify against actual site structure.
        """
        page = response.meta.get("playwright_page")

        # Extract product links
        product_links = response.css("a.product-link::attr(href)").getall()

        if not product_links:
            product_links = response.css("div.product-item a::attr(href)").getall()

        self.logger.info(f"Found {len(product_links)} products on page")

        # Close the page after extracting links
        if page:
            await page.close()

        # Follow product links
        for link in product_links:
            if link:
                yield scrapy.Request(
                    response.urljoin(link),
                    callback=self.parse_product,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                    },
                    errback=self.errback_close_page,
                )

        # Pagination
        next_page = response.css("a.next-page::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                errback=self.errback_close_page,
            )

    async def parse_product(self, response):
        """Parse individual product page."""
        page = response.meta.get("playwright_page")

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
        price = response.css("span.product-price::text").get()
        if not price:
            price = response.css("[data-price]::text").get()

        if price:
            loader.add_value("price", price)

        # Original price
        original_price = response.css("span.original-price::text").get()
        if original_price:
            loader.add_value("original_price", original_price)

        # Image
        image_url = response.css("img.product-image::attr(src)").get()
        if image_url:
            loader.add_value("image_url", image_url)

        # Specifications
        specs_dict = {}
        spec_items = response.css("div.specification-item")

        for spec in spec_items:
            label = spec.css("span.spec-label::text").get()
            value = spec.css("span.spec-value::text").get()

            if label and value:
                label = label.strip().lower()
                value = value.strip()

                if "processor" in label:
                    loader.add_value("processor", value)
                elif "ram" in label or "memory" in label:
                    loader.add_value("ram", value)
                elif "storage" in label or "hard drive" in label:
                    loader.add_value("storage", value)
                elif "screen" in label:
                    loader.add_value("screen_size", value)
                elif "graphic" in label:
                    loader.add_value("graphics", value)
                elif "os" in label or "operating" in label:
                    loader.add_value("operating_system", value)
                else:
                    specs_dict[label] = value

        # Description parsing
        description = " ".join(response.css("div.product-description ::text").getall())
        if description:
            parsed_specs = self.parse_specs_from_description(description)

            if not loader.get_output_value("processor") and "processor" in parsed_specs:
                loader.add_value("processor", parsed_specs["processor"])
            if not loader.get_output_value("ram") and "ram" in parsed_specs:
                loader.add_value("ram", parsed_specs["ram"])
            if not loader.get_output_value("storage") and "storage" in parsed_specs:
                loader.add_value("storage", parsed_specs["storage"])

        loader.add_value("specs", specs_dict)
        loader.add_value("condition", "New")

        # Close page
        if page:
            await page.close()

        yield loader.load_item()
