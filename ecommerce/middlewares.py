"""
Custom middleware for the e-commerce price scraper.

Includes:
- User-Agent rotation to avoid blocking
- Error handling and retry logic
- Request/response logging
"""

import random
import logging
from scrapy import signals


class UserAgentRotationMiddleware:
    """Rotates User-Agent headers to avoid detection and blocking."""

    def __init__(self, user_agent_list):
        self.user_agent_list = user_agent_list
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        user_agent_list = crawler.settings.get("USER_AGENT_LIST", [])
        if not user_agent_list:
            user_agent_list = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ]
        return cls(user_agent_list)

    def process_request(self, request, spider):
        """Set a random User-Agent for each request."""
        user_agent = random.choice(self.user_agent_list)
        request.headers["User-Agent"] = user_agent
        self.logger.debug(f"Using User-Agent: {user_agent[:50]}...")
        return None


class EcommerceSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class EcommerceDownloaderMiddleware:
    """
    Custom downloader middleware for enhanced error handling and logging.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        """Log outgoing requests."""
        self.logger.debug(f"Processing request: {request.url}")
        return None

    def process_response(self, request, response, spider):
        """Handle responses and log status codes."""
        self.logger.debug(f"Response received: {response.status} from {request.url}")

        # Handle specific status codes
        if response.status in [403, 429]:
            self.logger.warning(
                f"Possible blocking detected: {response.status} from " f"{request.url}"
            )

        return response

    def process_exception(self, request, exception, spider):
        """
        Handle exceptions during download.
        Log errors and allow retry mechanism to handle them.
        """
        self.logger.error(
            f"Exception occurred: {exception.__class__.__name__} "
            f"for {request.url}: {str(exception)}"
        )
        return None

    def spider_opened(self, spider):
        self.logger.info(f"Spider opened: {spider.name}")

    def spider_closed(self, spider):
        self.logger.info(f"Spider closed: {spider.name}")
