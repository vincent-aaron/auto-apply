"""Application automation service"""

import os
from typing import Dict, Any, Optional
import logging
from app.browser.manager import BrowserManager, FormFiller

logger = logging.getLogger(__name__)


class ApplicationAutomationService:
    """Automates job application filling"""
    
    def __init__(self):
        self.browser_manager = BrowserManager(headless=True)
    
    async def prepare_application(
        self,
        job_url: str,
        candidate_info: Dict[str, Any],
        generated_answers: Dict[str, str],
        resume_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a job application for submission (fills the form, pauses before submit).

        Args:
            job_url: URL of job application
            candidate_info: Candidate information
            generated_answers: AI-generated answers
            resume_path: Optional path to the candidate's resume file for auto-upload

        Returns:
            Application status and details
        """
        try:
            # Start browser
            await self.browser_manager.start()
            page = await self.browser_manager.create_page()

            # Navigate to job page
            await page.goto(job_url, wait_until="networkidle")
            logger.info(f"Navigated to: {job_url}")

            # Create form filler
            filler = FormFiller(page)

            # Fill personal information (common fields)
            try:
                await self._fill_personal_info(filler, candidate_info)
                logger.info("Filled personal information")
            except Exception as e:
                logger.warning(f"Could not fill personal info: {e}")

            # Fill application answers
            try:
                await self._fill_application_answers(filler, generated_answers)
                logger.info("Filled application answers")
            except Exception as e:
                logger.warning(f"Could not fill answers: {e}")

            # Upload resume if available
            if resume_path and os.path.exists(resume_path):
                try:
                    await self._upload_resume(filler, resume_path)
                    logger.info(f"Uploaded resume: {resume_path}")
                except Exception as e:
                    logger.warning(f"Could not upload resume: {e}")

            # Get current page state (STOPPED before submission - human review)
            page_title = await filler.get_page_title()
            page_url = await filler.get_page_url()

            # Close browser (state is lost, but controlled sites are filled for review)
            await self.browser_manager.close()

            return {
                "status": "ready_for_review",
                "page_title": page_title,
                "page_url": page_url,
                "message": "Application form has been filled. Please review and click Submit to complete the application.",
            }

        except Exception as e:
            logger.error(f"Application automation error: {e}")
            await self.browser_manager.close()
            message = str(e)
            if "Executable doesn't exist" in message or "executable" in message.lower():
                message = (
                    "Playwright browsers are not installed yet. Run once in the project folder: "
                    "`playwright install chromium` (free, ~150MB). Then try again."
                )
            return {
                "status": "error",
                "message": f"Failed to prepare application: {message}",
            }

    async def _upload_resume(self, filler: FormFiller, resume_path: str):
        """Upload resume file to common file inputs."""
        selectors = [
            "input[type='file']",
            "input[name='resume']",
            "input[accept*='pdf']",
            "input[accept*='doc']",
            "input[multiple]",
        ]
        for selector in selectors:
            try:
                await filler.upload_file(selector, resume_path)
                logger.debug(f"Uploaded resume via {selector}")
                return
            except Exception:
                continue
        raise RuntimeError("No file input found on the page")
    
    async def _fill_personal_info(self, filler: FormFiller, candidate_info: Dict[str, Any]):
        """Fill personal information fields"""
        # Common field selectors (would need to be adapted per site)
        field_mappings = {
            "first_name": ["input[name='firstName']", "input[name='first_name']", "input[placeholder*='First']"],
            "last_name": ["input[name='lastName']", "input[name='last_name']", "input[placeholder*='Last']"],
            "email": ["input[name='email']", "input[type='email']"],
            "phone": ["input[name='phone']", "input[type='tel']", "input[name='phoneNumber']"],
        }
        
        for field_name, selectors in field_mappings.items():
            value = candidate_info.get(field_name)
            if value:
                for selector in selectors:
                    try:
                        await filler.fill_text_field(selector, str(value))
                        logger.debug(f"Filled {field_name}")
                        break
                    except:
                        continue
    
    async def _fill_application_answers(self, filler: FormFiller, answers: Dict[str, str]):
        """Fill application question answers"""
        # Try to find and fill textarea fields for essay questions
        textareas = await filler.page.query_selector_all("textarea")
        
        answer_values = list(answers.values())
        
        for i, textarea in enumerate(textareas):
            if i < len(answer_values):
                try:
                    selector = f"textarea:nth-of-type({i+1})"
                    await filler.fill_text_field(selector, answer_values[i])
                    logger.debug(f"Filled answer {i+1}")
                except Exception as e:
                    logger.warning(f"Could not fill answer {i+1}: {e}")


application_automation_service = ApplicationAutomationService()
