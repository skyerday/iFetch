class DownloadStatus:
    """Model to track the status of downloaded files."""
    def __init__(
        self,
        path: str,
        size: int = 0,
        downloaded: int = 0,
        checksum: str = "",  # Default to empty string
        status: str = "pending",
        changes: int = 0,
        error: str = ""
    ):
        self.path = path
        self.size = size
        self.downloaded = downloaded
        self.checksum = checksum or ""  # Ensure it's never None
        self.status = status
        self.changes = changes
        self.error = error
