"""Google Drive API client with quota management and error handling."""

from typing import Any, Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.integrations.base import BaseIntegration
from src.core.logging import logger


class DriveQuotaExceededError(Exception):
    """Raised when Drive API quota is exceeded."""

    pass


class DriveAPIError(Exception):
    """Raised when Drive API returns an error."""

    pass


class DriveClient(BaseIntegration):
    """Google Drive API client with quota management and retries."""

    # Drive API quotas (per user per day)
    # Free tier: 1,000,000,000 quota units per day
    # Each API call consumes quota units (e.g., files.list: 100, files.get: 0, files.get_media: varies)
    DAILY_QUOTA_UNITS = 1_000_000_000
    QUOTA_WARNING_THRESHOLD = 0.8  # Warn at 80% usage

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        on_token_refresh: Optional[Any] = None,
    ):
        """Initialize Drive client.

        Args:
            access_token: Google access token
            refresh_token: Google refresh token (optional)
            on_token_refresh: Optional callback when token is refreshed.
                Should accept (access_token, refresh_token, expires_in) as arguments.
        """
        super().__init__(access_token, refresh_token)
        self._on_token_refresh = on_token_refresh
        self._service = None
        self._docs_service = None
        self._quota_used = 0
        self._quota_reset_at = datetime.utcnow() + timedelta(days=1)

    def _get_service(self):
        """Get or create Drive service instance."""
        if self._service is None:
            # Import here to avoid circular dependency
            from src.integrations.gmail.oauth import GoogleOAuth

            oauth = GoogleOAuth()
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=oauth.client_id,  # Required for token refresh
                client_secret=oauth.client_secret,  # Required for token refresh
            )
            self._service = build("drive", "v3", credentials=credentials)
        return self._service

    def _get_docs_service(self):
        """Get or create Google Docs service instance."""
        if self._docs_service is None:
            # Import here to avoid circular dependency
            from src.integrations.gmail.oauth import GoogleOAuth

            oauth = GoogleOAuth()
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=oauth.client_id,
                client_secret=oauth.client_secret,
            )
            self._docs_service = build("docs", "v1", credentials=credentials)
        return self._docs_service

    async def _check_quota(self) -> None:
        """Check if quota is available."""
        if self._quota_used >= self.DAILY_QUOTA_UNITS * self.QUOTA_WARNING_THRESHOLD:
            raise DriveQuotaExceededError(
                f"Drive API quota warning: {self._quota_used}/{self.DAILY_QUOTA_UNITS} units used"
            )

    async def refresh_access_token(self) -> dict[str, Any]:
        """Refresh the access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        from src.integrations.gmail.oauth import GoogleOAuth

        oauth = GoogleOAuth()
        token = await oauth.refresh_token(self.refresh_token)
        self.access_token = token["access_token"]
        if "refresh_token" in token:
            self.refresh_token = token["refresh_token"]

        # Invalidate services to rebuild with new credentials
        self._service = None
        self._docs_service = None

        # Call callback if provided to update database
        if self._on_token_refresh:
            expires_in = token.get("expires_in")
            if not expires_in and token.get("expires_at"):
                from datetime import datetime
                expires_at = datetime.fromisoformat(
                    token["expires_at"].replace("Z", "+00:00"))
                expires_in = int(
                    (expires_at - datetime.utcnow().replace(tzinfo=None)).total_seconds())
            await self._on_token_refresh(
                self.access_token,
                self.refresh_token,
                expires_in,
            )

        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": token.get("expires_in"),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def search_files(
        self,
        query: str,
        fields: str = "files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
        max_results: int = 10,
    ) -> List[dict[str, Any]]:
        """Search for files in Google Drive.

        Args:
            query: Drive search query (e.g., "name contains 'transcript'", "mimeType='text/plain'")
            fields: Fields to return in response (default: basic file info)
            max_results: Maximum number of results (default: 10)

        Returns:
            List of file dictionaries
        """
        await self._check_quota()

        try:
            service = self._get_service()

            def search_files_sync():
                return (
                    service.files()
                    .list(
                        q=query,
                        fields=f"nextPageToken, {fields}",
                        pageSize=min(max_results, 100),
                        orderBy="modifiedTime desc",
                    )
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, search_files_sync)

            files = result.get("files", [])
            self._quota_used += 100  # files.list operation costs 100 quota units

            logger.debug(f"Found {len(files)} files in Drive")
            return files
        except HttpError as e:
            if e.resp.status == 401:
                # Token expired, try to refresh
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    # Retry the request with new token
                    service = self._get_service()

                    def search_files_sync_retry():
                        return (
                            service.files()
                            .list(
                                q=query,
                                fields=f"nextPageToken, {fields}",
                                pageSize=min(max_results, 100),
                                orderBy="modifiedTime desc",
                            )
                            .execute()
                        )

                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        result = await loop.run_in_executor(executor, search_files_sync_retry)
                    files = result.get("files", [])
                    self._quota_used += 100
                    return files
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            raise DriveAPIError(f"Drive API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def get_file_metadata(self, file_id: str) -> dict[str, Any]:
        """Get file metadata.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            def get_file_sync():
                return (
                    service.files()
                    .get(fileId=file_id, fields="id, name, mimeType, createdTime, modifiedTime, webViewLink, size")
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, get_file_sync)

            # files.get doesn't consume quota (it's free)
            return result
        except HttpError as e:
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    service = self._get_service()
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        result = await loop.run_in_executor(executor, get_file_sync)
                    return result
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            raise DriveAPIError(f"Drive API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def download_file(self, file_id: str) -> str:
        """Download file content as text.

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as string
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # First get file metadata to check MIME type
            metadata = await self.get_file_metadata(file_id)
            mime_type = metadata.get("mimeType", "")

            # Google Docs need special handling - must use export_media
            if "google-apps.document" in mime_type:
                # For Google Docs, need to export as plain text
                def export_file_sync():
                    try:
                        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
                        from io import BytesIO
                        from googleapiclient.http import MediaIoBaseDownload

                        file_content = BytesIO()
                        downloader = MediaIoBaseDownload(file_content, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                        return file_content.getvalue()
                    except Exception as ex:
                        # Re-raise to preserve exception type and traceback
                        raise

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    content_bytes = await loop.run_in_executor(executor, export_file_sync)
                decoded_content = content_bytes.decode("utf-8")
            else:
                # For other files (plain text, etc.), use get_media
                def download_file_sync():
                    request = service.files().get_media(fileId=file_id)
                    # Download file content
                    from io import BytesIO
                    from googleapiclient.http import MediaIoBaseDownload

                    file_content = BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                    return file_content.getvalue()

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    content_bytes = await loop.run_in_executor(executor, download_file_sync)

                # Decode plain text files
                try:
                    decoded_content = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other encodings
                    decoded_content = content_bytes.decode(
                        "utf-8", errors="ignore")

            # Download operations consume variable quota (typically 0-100 units)
            self._quota_used += 100
            return decoded_content

        except HttpError as e:
            # Extract detailed error message
            error_details = getattr(e, 'error_details', '')
            error_reason = getattr(e, 'reason', '')
            error_content = getattr(e, 'content', b'')

            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    # Retry after refresh would be complex, raise error instead
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            else:
                # Include detailed error information
                error_msg = f"Drive API error (status {e.resp.status})"
                if error_reason:
                    error_msg += f": {error_reason}"
                if error_details:
                    error_msg += f" - {error_details}"
                elif error_content:
                    try:
                        error_msg += f" - {error_content.decode('utf-8')[:200]}"
                    except:
                        pass
                logger.error(
                    f"Drive download_file error: {error_msg}", exc_info=True)
                raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def create_file(
        self,
        name: str,
        content: str,
        mime_type: str = "text/plain",
        folder_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new file in Google Drive.

        Args:
            name: File name
            content: File content (text)
            mime_type: MIME type (text/plain, application/vnd.google-apps.document, etc.)
            folder_id: Optional parent folder ID

        Returns:
            Created file metadata dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # For Google Docs, create the file and insert content using Google Docs API
            if mime_type == "application/vnd.google-apps.document":
                # Create empty Google Doc first
                def create_doc_sync():
                    file_metadata = {"name": name, "mimeType": mime_type}
                    if folder_id:
                        file_metadata["parents"] = [folder_id]

                    file = service.files().create(body=file_metadata,
                                                  fields="id, name, mimeType, webViewLink").execute()
                    return file

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    file_result = await loop.run_in_executor(executor, create_doc_sync)

                document_id = file_result["id"]
                self._quota_used += 100  # files.create consumes ~100 units

                # Insert content using Google Docs API
                if content:
                    await self.insert_text_to_doc(document_id, content)

                return file_result
            else:
                # For text files, create with content
                def create_file_sync():
                    from io import BytesIO
                    from googleapiclient.http import MediaIoBaseUpload

                    file_metadata = {"name": name}
                    if folder_id:
                        file_metadata["parents"] = [folder_id]

                    media = MediaIoBaseUpload(
                        BytesIO(content.encode("utf-8")),
                        mimetype=mime_type,
                        resumable=True
                    )

                    file = service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id, name, mimeType, webViewLink"
                    ).execute()
                    return file

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    file_result = await loop.run_in_executor(executor, create_file_sync)

                self._quota_used += 100
                return file_result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    # Retry the operation after token refresh
                    service = self._get_service()
                    if mime_type == "application/vnd.google-apps.document":
                        def create_doc_sync_retry():
                            file_metadata = {
                                "name": name, "mimeType": mime_type}
                            if folder_id:
                                file_metadata["parents"] = [folder_id]
                            file = service.files().create(body=file_metadata,
                                                          fields="id, name, mimeType, webViewLink").execute()
                            return file
                        loop = asyncio.get_event_loop()
                        with ThreadPoolExecutor() as executor:
                            file_result = await loop.run_in_executor(executor, create_doc_sync_retry)
                        self._quota_used += 100
                        return file_result
                    else:
                        def create_file_sync_retry():
                            from io import BytesIO
                            from googleapiclient.http import MediaIoBaseUpload
                            file_metadata = {"name": name}
                            if folder_id:
                                file_metadata["parents"] = [folder_id]
                            media = MediaIoBaseUpload(BytesIO(content.encode(
                                "utf-8")), mimetype=mime_type, resumable=True)
                            file = service.files().create(body=file_metadata, media_body=media,
                                                          fields="id, name, mimeType, webViewLink").execute()
                            return file
                        loop = asyncio.get_event_loop()
                        with ThreadPoolExecutor() as executor:
                            file_result = await loop.run_in_executor(executor, create_file_sync_retry)
                        self._quota_used += 100
                        return file_result
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive create_file error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def update_file_content(
        self,
        file_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Update file content.

        Args:
            file_id: Google Drive file ID
            content: New file content (text)

        Returns:
            Updated file metadata dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # First get file metadata to check MIME type
            metadata = await self.get_file_metadata(file_id)
            mime_type = metadata.get("mimeType", "")

            if "google-apps.document" in mime_type:
                # For Google Docs, clear existing content and insert new content
                # First, get the document to find the end index
                docs_service = self._get_docs_service()

                def get_doc_and_update_sync():
                    # Get document to find content range
                    doc = docs_service.documents().get(documentId=file_id).execute()

                    # Find the end index (excluding the final newline)
                    end_index = 1
                    if "body" in doc and "content" in doc["body"]:
                        for element in doc["body"]["content"]:
                            if "endIndex" in element:
                                end_index = max(end_index, element["endIndex"])

                    # Delete all content except the first newline
                    requests = []
                    if end_index > 1:
                        requests.append({
                            "deleteContentRange": {
                                "range": {
                                    "startIndex": 1,
                                    "endIndex": end_index - 1
                                }
                            }
                        })

                    # Insert new content
                    if content:
                        requests.append({
                            "insertText": {
                                "location": {"index": 1},
                                "text": content
                            }
                        })

                    if requests:
                        result = docs_service.documents().batchUpdate(
                            documentId=file_id,
                            body={"requests": requests}
                        ).execute()
                        return result
                    return {}

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    await loop.run_in_executor(executor, get_doc_and_update_sync)

                # Get updated metadata
                metadata = await self.get_file_metadata(file_id)
                self._quota_used += 50  # Docs API batchUpdate consumes ~50 units
                return metadata
            else:
                # For text files, update content
                def update_file_sync():
                    from io import BytesIO
                    from googleapiclient.http import MediaIoBaseUpload

                    media = MediaIoBaseUpload(
                        BytesIO(content.encode("utf-8")),
                        mimetype=mime_type or "text/plain",
                        resumable=True
                    )

                    file = service.files().update(
                        fileId=file_id,
                        media_body=media,
                        fields="id, name, mimeType, modifiedTime, webViewLink"
                    ).execute()
                    return file

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    file_result = await loop.run_in_executor(executor, update_file_sync)

                self._quota_used += 50  # files.update consumes ~50 units
                return file_result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive update_file_content error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def delete_file(self, file_id: str) -> None:
        """Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID
        """
        await self._check_quota()

        try:
            service = self._get_service()

            def delete_file_sync():
                service.files().delete(fileId=file_id).execute()

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, delete_file_sync)

            self._quota_used += 50  # files.delete consumes ~50 units

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 404:
                raise DriveAPIError(f"File {file_id} not found") from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive delete_file error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def create_folder(
        self,
        name: str,
        parent_folder_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a folder in Google Drive.

        Args:
            name: Folder name
            parent_folder_id: Optional parent folder ID

        Returns:
            Created folder metadata dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            def create_folder_sync():
                file_metadata = {
                    "name": name,
                    "mimeType": "application/vnd.google-apps.folder"
                }
                if parent_folder_id:
                    file_metadata["parents"] = [parent_folder_id]

                folder = service.files().create(
                    body=file_metadata,
                    fields="id, name, mimeType, webViewLink"
                ).execute()
                return folder

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                folder_result = await loop.run_in_executor(executor, create_folder_sync)

            self._quota_used += 100  # files.create consumes ~100 units
            return folder_result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive create_folder error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def insert_text_to_doc(
        self,
        document_id: str,
        text: str,
        index: Optional[int] = None,
    ) -> dict[str, Any]:
        """Insert text into a Google Doc at a specific index.

        Args:
            document_id: Google Docs document ID
            text: Text to insert
            index: Optional insertion index (if None, appends to end)

        Returns:
            Result from the batchUpdate operation
        """
        await self._check_quota()

        try:
            docs_service = self._get_docs_service()

            def insert_text_sync():
                # Get document to find end index if not provided
                if index is None:
                    doc = docs_service.documents().get(documentId=document_id).execute()
                    # Find the end index (length of all content)
                    end_index = 1  # Start after the document start
                    if "body" in doc and "content" in doc["body"]:
                        for element in doc["body"]["content"]:
                            if "endIndex" in element:
                                end_index = max(end_index, element["endIndex"])
                    insert_index = end_index - 1  # Insert before the final newline
                else:
                    insert_index = index

                requests = [
                    {
                        "insertText": {
                            "location": {"index": insert_index},
                            "text": text
                        }
                    }
                ]

                result = docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": requests}
                ).execute()
                return result

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, insert_text_sync)

            self._quota_used += 50  # Docs API batchUpdate consumes ~50 units
            return result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive insert_text_to_doc error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def format_doc_text(
        self,
        document_id: str,
        start_index: int,
        end_index: int,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        font_size: Optional[float] = None,
        heading: Optional[int] = None,  # 1-6 for heading levels
    ) -> dict[str, Any]:
        """Format text in a Google Doc.

        Args:
            document_id: Google Docs document ID
            start_index: Start index of text to format
            end_index: End index of text to format
            bold: Make text bold
            italic: Make text italic
            underline: Underline text
            font_size: Font size in points
            heading: Heading level (1-6, None for normal text)

        Returns:
            Result from the batchUpdate operation
        """
        await self._check_quota()

        try:
            docs_service = self._get_docs_service()

            def format_text_sync():
                requests = []

                # Text style (bold, italic, underline, font size)
                text_style = {}
                if bold is not None:
                    text_style["bold"] = bold
                if italic is not None:
                    text_style["italic"] = italic
                if underline is not None:
                    text_style["underline"] = underline
                if font_size is not None:
                    text_style["fontSize"] = {
                        "magnitude": font_size, "unit": "PT"}

                if text_style:
                    requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": start_index,
                                "endIndex": end_index
                            },
                            "textStyle": text_style,
                            "fields": ",".join(text_style.keys())
                        }
                    })

                # Paragraph style (heading level)
                if heading is not None:
                    paragraph_style = {}
                    if heading >= 1 and heading <= 6:
                        paragraph_style["namedStyleType"] = f"HEADING_{heading}"
                    else:
                        paragraph_style["namedStyleType"] = "NORMAL_TEXT"

                    requests.append({
                        "updateParagraphStyle": {
                            "range": {
                                "startIndex": start_index,
                                "endIndex": end_index
                            },
                            "paragraphStyle": paragraph_style,
                            "fields": "namedStyleType"
                        }
                    })

                if not requests:
                    return {}  # No formatting to apply

                result = docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": requests}
                ).execute()
                return result

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, format_text_sync)

            self._quota_used += 50
            return result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive format_doc_text error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (DriveQuotaExceededError, DriveAPIError)),
    )
    async def create_formatted_document(
        self,
        name: str,
        content: str,
        folder_id: Optional[str] = None,
        format_markdown: bool = True,
    ) -> dict[str, Any]:
        """Create a Google Doc with formatted content.

        Supports Markdown-like formatting:
        - # Heading 1, ## Heading 2, etc.
        - **bold**, *italic*
        - Bullet lists (- item)
        - Numbered lists (1. item)

        Args:
            name: Document name
            content: Document content (plain text or Markdown)
            folder_id: Optional parent folder ID
            format_markdown: If True, parse Markdown formatting

        Returns:
            Created document metadata dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()
            docs_service = self._get_docs_service()

            # First create the document
            def create_doc_sync():
                file_metadata = {
                    "name": name, "mimeType": "application/vnd.google-apps.document"}
                if folder_id:
                    file_metadata["parents"] = [folder_id]
                file = service.files().create(
                    body=file_metadata,
                    fields="id, name, mimeType, webViewLink"
                ).execute()
                return file

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                file_result = await loop.run_in_executor(executor, create_doc_sync)

            document_id = file_result["id"]
            self._quota_used += 100

            # Now add formatted content
            if format_markdown:
                # Parse Markdown and insert formatted content
                await self._insert_markdown_content(document_id, content)
            else:
                # Just insert plain text
                await self.insert_text_to_doc(document_id, content)

            return file_result

        except HttpError as e:
            error_reason = getattr(e, "reason", "")
            if e.resp.status == 401:
                if self.refresh_token:
                    logger.info("Drive token expired, attempting refresh...")
                    await self.refresh_access_token()
                    raise DriveAPIError(
                        "Drive authentication failed - please retry") from e
                else:
                    raise DriveAPIError(
                        "Drive authentication failed - no refresh token available"
                    ) from e
            elif e.resp.status == 429:
                raise DriveQuotaExceededError(
                    "Drive API quota exceeded") from e
            error_msg = f"Drive API error (status {e.resp.status})"
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Drive create_formatted_document error: {error_msg}", exc_info=True)
            raise DriveAPIError(error_msg) from e

    async def _insert_markdown_content_simple(self, document_id: str, markdown: str) -> None:
        """Simple Markdown parser (fallback)."""
        import re

        docs_service = self._get_docs_service()

        def get_doc_end_index():
            doc = docs_service.documents().get(documentId=document_id).execute()
            end_index = 1
            if "body" in doc and "content" in doc["body"]:
                for element in doc["body"]["content"]:
                    if "endIndex" in element:
                        end_index = max(end_index, element["endIndex"])
            return end_index - 1

        def parse_inline_formatting(text: str) -> Tuple[str, List[Dict]]:
            """Parse bold/italic in text and return plain text with formatting info.

            Returns:
                (plain_text, format_ranges) where format_ranges contains:
                [{"start": int, "end": int, "bold": bool, "italic": bool}, ...]
            """
            plain_text = ""
            format_ranges: List[Dict] = []
            i = 0

            while i < len(text):
                # Check for bold (**text** or __text__)
                if i + 2 <= len(text) and text[i:i+2] == "**":
                    # Find closing **
                    end = text.find("**", i + 2)
                    if end != -1:
                        bold_text = text[i+2:end]
                        start_pos = len(plain_text)
                        plain_text += bold_text
                        format_ranges.append({
                            "start": start_pos,
                            "end": len(plain_text),
                            "bold": True,
                            "italic": False
                        })
                        i = end + 2
                        continue
                elif i + 2 <= len(text) and text[i:i+2] == "__":
                    # Find closing __
                    end = text.find("__", i + 2)
                    if end != -1:
                        bold_text = text[i+2:end]
                        start_pos = len(plain_text)
                        plain_text += bold_text
                        format_ranges.append({
                            "start": start_pos,
                            "end": len(plain_text),
                            "bold": True,
                            "italic": False
                        })
                        i = end + 2
                        continue

                # Check for italic (*text* or _text_) - single char, not double
                if i + 1 <= len(text) and text[i] == "*" and (i + 1 >= len(text) or text[i+1] != "*"):
                    # Find closing *
                    end = text.find("*", i + 1)
                    if end != -1 and (end + 1 >= len(text) or text[end+1] != "*"):
                        italic_text = text[i+1:end]
                        start_pos = len(plain_text)
                        plain_text += italic_text
                        format_ranges.append({
                            "start": start_pos,
                            "end": len(plain_text),
                            "bold": False,
                            "italic": True
                        })
                        i = end + 1
                        continue
                elif i + 1 <= len(text) and text[i] == "_" and (i + 1 >= len(text) or text[i+1] != "_"):
                    # Find closing _
                    end = text.find("_", i + 1)
                    if end != -1 and (end + 1 >= len(text) or text[end+1] != "_"):
                        italic_text = text[i+1:end]
                        start_pos = len(plain_text)
                        plain_text += italic_text
                        format_ranges.append({
                            "start": start_pos,
                            "end": len(plain_text),
                            "bold": False,
                            "italic": True
                        })
                        i = end + 1
                        continue

                # Regular character
                plain_text += text[i]
                i += 1

            return plain_text, format_ranges

        # Parse Markdown and build requests
        lines = markdown.split('\n')
        start_index = get_doc_end_index()
        requests = []
        current_index = start_index

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('#'):
                # Heading - extract level and text
                heading_match = re.match(r'^(#+)\s+(.+)$', stripped)
                if heading_match:
                    level = min(len(heading_match.group(1)), 6)
                    heading_text = heading_match.group(2)

                    # Parse inline formatting in heading
                    plain_text, format_ranges = parse_inline_formatting(
                        heading_text)
                    text_with_newline = plain_text + "\n"

                    # Insert text
                    text_start = current_index
                    requests.append({
                        "insertText": {
                            "location": {"index": current_index},
                            "text": text_with_newline
                        }
                    })

                    # Apply heading paragraph style (exclude newline)
                    text_end = current_index + len(plain_text)
                    requests.append({
                        "updateParagraphStyle": {
                            "range": {
                                "startIndex": text_start,
                                "endIndex": text_end
                            },
                            "paragraphStyle": {
                                "namedStyleType": f"HEADING_{level}"
                            },
                            "fields": "namedStyleType"
                        }
                    })

                    # Apply inline formatting (bold/italic) within heading
                    for fmt_range in format_ranges:
                        fmt_start = text_start + fmt_range["start"]
                        fmt_end = text_start + fmt_range["end"]
                        text_style = {}
                        if fmt_range["bold"]:
                            text_style["bold"] = True
                        if fmt_range["italic"]:
                            text_style["italic"] = True

                        if text_style:
                            requests.append({
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": fmt_start,
                                        "endIndex": fmt_end
                                    },
                                    "textStyle": text_style,
                                    "fields": ",".join(text_style.keys())
                                }
                            })

                    current_index += len(text_with_newline)

            elif stripped.startswith('- ') or re.match(r'^\d+\. ', stripped):
                # List item
                list_prefix_match = re.match(r'^([-*] |\d+\. )', stripped)
                if list_prefix_match:
                    item_text = stripped[len(
                        list_prefix_match.group(1)):].strip()
                    if item_text:
                        # Parse inline formatting in list item
                        plain_text, format_ranges = parse_inline_formatting(
                            item_text)
                        list_text = "• " + plain_text + "\n"

                        # Insert text
                        text_start = current_index
                        requests.append({
                            "insertText": {
                                "location": {"index": current_index},
                                "text": list_text
                            }
                        })

                        # Apply inline formatting (bold/italic) within list item
                        # Note: +2 accounts for "• " prefix
                        for fmt_range in format_ranges:
                            fmt_start = text_start + 2 + fmt_range["start"]
                            fmt_end = text_start + 2 + fmt_range["end"]
                            text_style = {}
                            if fmt_range["bold"]:
                                text_style["bold"] = True
                            if fmt_range["italic"]:
                                text_style["italic"] = True

                            if text_style:
                                requests.append({
                                    "updateTextStyle": {
                                        "range": {
                                            "startIndex": fmt_start,
                                            "endIndex": fmt_end
                                        },
                                        "textStyle": text_style,
                                        "fields": ",".join(text_style.keys())
                                    }
                                })

                        current_index += len(list_text)

            elif stripped:
                # Regular text - parse inline formatting
                plain_text, format_ranges = parse_inline_formatting(stripped)
                text_with_newline = plain_text + "\n"

                # Insert text
                text_start = current_index
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": text_with_newline
                    }
                })

                # Apply inline formatting (bold/italic)
                for fmt_range in format_ranges:
                    fmt_start = text_start + fmt_range["start"]
                    fmt_end = text_start + fmt_range["end"]
                    text_style = {}
                    if fmt_range["bold"]:
                        text_style["bold"] = True
                    if fmt_range["italic"]:
                        text_style["italic"] = True

                    if text_style:
                        requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": fmt_start,
                                    "endIndex": fmt_end
                                },
                                "textStyle": text_style,
                                "fields": ",".join(text_style.keys())
                            }
                        })

                current_index += len(text_with_newline)
            else:
                # Empty line
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": "\n"
                    }
                })
                current_index += 1

        # Execute batch update
        if requests:
            def batch_update_sync():
                return docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": requests}
                ).execute()

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, batch_update_sync)

            self._quota_used += 50

    async def _insert_markdown_content(self, document_id: str, markdown: str) -> None:
        """Insert Markdown-formatted content into a Google Doc.

        Uses markdown-it-py for robust parsing, with fallback to simple parser.
        Supports: headings, bold, italic, lists, nested structures.
        """
        docs_service = self._get_docs_service()

        def get_doc_end_index():
            doc = docs_service.documents().get(documentId=document_id).execute()
            end_index = 1
            if "body" in doc and "content" in doc["body"]:
                for element in doc["body"]["content"]:
                    if "endIndex" in element:
                        end_index = max(end_index, element["endIndex"])
            return end_index - 1

        try:
            from src.integrations.drive.markdown_parser import parse_markdown_to_docs_requests

            # Use robust parser
            start_index = get_doc_end_index()
            plain_text, requests = parse_markdown_to_docs_requests(
                markdown, start_index)

            # Insert text first
            all_requests = [
                {
                    "insertText": {
                        "location": {"index": start_index},
                        "text": plain_text
                    }
                }
            ]
            # Then apply formatting
            all_requests.extend(requests)

        except ImportError:
            # Fallback to simple parser if markdown-it-py not available
            logger.warning("markdown-it-py not available, using simple parser")
            await self._insert_markdown_content_simple(document_id, markdown)
            return
        except Exception as e:
            # Fallback on any error
            logger.warning(
                f"Error in markdown parser: {e}, falling back to simple parser")
            await self._insert_markdown_content_simple(document_id, markdown)
            return

        # Execute batch update
        if all_requests:
            def batch_update_sync():
                return docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": all_requests}
                ).execute()

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, batch_update_sync)

            self._quota_used += 50

    async def test_connection(self) -> bool:
        """Test if the Drive integration is working."""
        try:
            await self.search_files("mimeType='text/plain'", max_results=1)
            return True
        except Exception:
            return False
