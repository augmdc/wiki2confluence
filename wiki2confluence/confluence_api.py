from atlassian import Confluence
import markdown2
from functools import lru_cache
import logging
import time
import threading
import io
import os
import tempfile
import mimetypes

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ConfluenceAPI:
    def __init__(self, url, username, api_token, rate_limit=2):
        self.url = url
        self.username = username
        self.api_token = api_token
        self.rate_limit = rate_limit
        self.local = threading.local()

    @property
    def confluence(self):
        if not hasattr(self.local, 'confluence'):
            self.local.confluence = Confluence(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True
            )
        return self.local.confluence

    @property
    def last_request_time(self):
        if not hasattr(self.local, 'last_request_time'):
            self.local.last_request_time = 0
        return self.local.last_request_time

    @last_request_time.setter
    def last_request_time(self, value):
        self.local.last_request_time = value

    def rate_limit_request(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.0 / self.rate_limit:
            time.sleep((1.0 / self.rate_limit) - time_since_last_request)
        self.last_request_time = time.time()

    @lru_cache(maxsize=1000)
    def markdown_to_html(self, markdown_content):
        return markdown2.markdown(markdown_content)

    @lru_cache(maxsize=1000)
    def get_page_id(self, space, title):
        self.rate_limit_request()
        try:
            page = self.confluence.get_page_by_title(space, title)
            if page:
                return page['id']
            return None
        except Exception as e:
            logger.error(f"Error checking for existing page '{title}': {e}")
            return None

    def create_or_update_page(self, space, title, body, parent_id):
        self.rate_limit_request()
        try:
            html_body = self.markdown_to_html(body)

            existing_page_id = self.get_page_id(space, title)

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if existing_page_id:
                        page = self.confluence.update_page(
                            page_id=existing_page_id,
                            title=title,
                            body=html_body,
                            parent_id=parent_id,
                            type='page',
                            representation='storage'
                        )
                        logger.info(f"Updated page '{title}' (ID: {page['id']})")
                    else:
                        page = self.confluence.create_page(
                            space=space,
                            title=title,
                            body=html_body,
                            parent_id=parent_id,
                            type='page',
                            representation='storage'
                        )
                        logger.info(f"Created page '{title}' (ID: {page['id']})")
                    return page['id']
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Error creating/updating page '{title}': {error_message}")

                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed. Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        raise e

        except Exception as e:
            logger.error(f"Error creating or updating Confluence page '{title}': {e}")
            return None

    def update_page_content(self, page_id, title, body):
        self.rate_limit_request()
        try:
            html_body = self.markdown_to_html(body)
            page = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=html_body,
                type='page',
                representation='storage'
            )
            logger.info(f"Updated page content for '{title}' (ID: {page['id']})")
            return True
        except Exception as e:
            logger.error(f"Error updating page content for '{title}': {e}")
            return False

    def verify_page_exists(self, page_id):
        """
        Verify if a page exists by its ID.
        """
        self.rate_limit_request()
        try:
            page = self.confluence.get_page_by_id(page_id)
            return page is not None
        except Exception as e:
            logger.error(f"Error verifying page with ID '{page_id}': {e}")
            return False

    def upload_attachment(self, page_id, file_name, file_content):
        """
        Upload an attachment to a Confluence page.
        """
        self.rate_limit_request()
        temp_file = None
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Determine the content type
            content_type, _ = mimetypes.guess_type(file_name)
            if content_type is None:
                content_type = 'application/octet-stream'

            # Upload the temporary file
            attachment = self.confluence.attach_file(
                filename=temp_file_path,
                name=file_name,
                page_id=page_id,
                content_type=content_type,
                comment="Uploaded during wiki migration"
            )
            
            # Log more details about the upload
            logger.info(f"Successfully uploaded attachment '{file_name}' to page ID {page_id}")
            logger.info(f"Attachment details: {attachment}")
            
            # Verify the attachment
            self.verify_attachment(page_id, file_name)
            
            return True
        except Exception as e:
            logger.error(f"Error uploading attachment '{file_name}' to page ID {page_id}: {e}")
            return False
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def verify_attachment(self, page_id, file_name):
        """
        Verify that the attachment was successfully uploaded and is accessible.
        """
        try:
            attachments = self.confluence.get_attachments_from_content(page_id)
            for attachment in attachments['results']:
                if attachment['title'] == file_name:
                    logger.info(f"Verified attachment '{file_name}' on page ID {page_id}")
                    logger.info(f"Attachment URL: {attachment['_links']['download']}")
                    return
            logger.warning(f"Attachment '{file_name}' not found on page ID {page_id} after upload")
        except Exception as e:
            logger.error(f"Error verifying attachment '{file_name}' on page ID {page_id}: {e}")