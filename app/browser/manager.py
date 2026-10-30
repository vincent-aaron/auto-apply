"""Browser manager for automation"""

from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instances"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def start(self):
        """Start browser instance"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless
            )
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def close(self):
        """Close browser instance"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def create_page(self) -> Page:
        """Create a new browser page"""
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        return await self.browser.new_page()


class FormFiller:
    """Automates form filling for job applications"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def fill_text_field(self, selector: str, value: str):
        """Fill a text field"""
        try:
            await self.page.fill(selector, value)
            logger.debug(f"Filled text field: {selector}")
        except Exception as e:
            logger.error(f"Failed to fill text field {selector}: {e}")
            raise
    
    async def select_dropdown(self, selector: str, value: str):
        """Select from dropdown"""
        try:
            await self.page.select_option(selector, value)
            logger.debug(f"Selected dropdown: {selector} = {value}")
        except Exception as e:
            logger.error(f"Failed to select dropdown {selector}: {e}")
            raise
    
    async def click_checkbox(self, selector: str, check: bool = True):
        """Click checkbox"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                is_checked = await element.is_checked()
                if is_checked != check:
                    await element.click()
            logger.debug(f"Clicked checkbox: {selector}")
        except Exception as e:
            logger.error(f"Failed to click checkbox {selector}: {e}")
            raise
    
    async def upload_file(self, selector: str, file_path: str):
        """Upload a file"""
        try:
            await self.page.set_input_files(selector, file_path)
            logger.debug(f"Uploaded file to: {selector}")
        except Exception as e:
            logger.error(f"Failed to upload file to {selector}: {e}")
            raise
    
    async def click_button(self, selector: str):
        """Click a button"""
        try:
            await self.page.click(selector)
            logger.debug(f"Clicked button: {selector}")
        except Exception as e:
            logger.error(f"Failed to click button {selector}: {e}")
            raise
    
    async def wait_for_element(self, selector: str, timeout: int = 5000):
        """Wait for element to appear"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            logger.debug(f"Element appeared: {selector}")
        except Exception as e:
            logger.error(f"Timeout waiting for {selector}: {e}")
            raise
    
    async def get_page_title(self) -> str:
        """Get page title"""
        return await self.page.title()
    
    async def get_page_url(self) -> str:
        """Get current page URL"""
        return self.page.url


browser_manager = BrowserManager()
