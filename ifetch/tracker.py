import json
from pathlib import Path
from typing import Dict, Any, Optional


class DownloadTracker:
    """Tracks download progress and enables resuming downloads."""

    def __init__(self, file_path: Path):
        """Initialize the tracker for a specific file.

        Args:
            file_path: Path to the file being downloaded
        """
        self.file_path = file_path
        self.status_path = file_path.with_suffix(file_path.suffix + '.download')
        self.current_position: int = 0
        self._load_status()

    def _load_status(self) -> None:
        """Load existing download status from status file if it exists."""
        if self.status_path.exists():
            try:
                with self.status_path.open('r') as f:
                    data = json.load(f)
                    self.current_position = data.get('position', 0)
            except (json.JSONDecodeError, OSError):
                # If status file is corrupt, start from beginning
                self.current_position = 0

    def save_status(self, position: int) -> None:
        """Save current download position to status file.

        Args:
            position: Current byte position in the download
        """
        self.current_position = position
        try:
            with self.status_path.open('w') as f:
                json.dump({'position': position}, f)
        except OSError:
            # Continue even if we can't save status
            pass

    def cleanup(self) -> None:
        """Remove status file after successful download."""
        if self.status_path.exists():
            try:
                self.status_path.unlink()
            except OSError:
                # Non-critical error, can be ignored
                pass
