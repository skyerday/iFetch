import os
import sys
import time
from pathlib import Path
from typing import Optional, Union, List
from tqdm import tqdm
from pyicloud import PyiCloudService
from pyicloud.exceptions import (
    PyiCloudAPIResponseException,
    PyiCloud2SARequiredException,
    PyiCloudFailedLoginException,
    PyiCloudNoStoredPasswordAvailableException
)

def can_read_file(item) -> bool:
    """Check if the item is a readable file by attempting to open it."""
    # Debug info
    print(f"Checking item: {getattr(item, 'name', 'unknown')}")
    print(f"Item attributes: {dir(item)}")

    if not hasattr(item, 'open'):
        print("No 'open' attribute")
        return False

    if hasattr(item, 'type'):
        item_type = getattr(item, 'type', '').lower()
        print(f"Item type: {item_type}")
        if item_type == 'folder':
            return False

    try:
        with item.open(stream=True) as response:
            if not response.ok:
                print(f"Response not OK: {response.status_code}")
                return False
            # Try to read a small chunk to verify it's a readable file
            chunk = next(response.raw.stream(1024, decode_content=False), None)
            has_content = chunk is not None
            print(f"Has content: {has_content}")
            return has_content
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return False

def process_item(self, item, local_path: Path) -> None:
    """Process an item, determining whether to treat it as a file or directory."""
    try:
        item_name = getattr(item, 'name', 'unknown')
        print(f"\nProcessing item: {item_name}")

        # If it has a type attribute and it's a folder, process as directory
        if hasattr(item, 'type') and getattr(item, 'type', '').lower() == 'folder':
            print(f"Processing as directory: {item_name}")
            if hasattr(item, 'dir'):
                contents = item.dir()
                if contents:
                    local_path.mkdir(exist_ok=True)
                    for name in contents:
                        sub_item = item[name]
                        sub_path = local_path / name
                        self.process_item(sub_item, sub_path)
        elif can_read_file(item):
            print(f"Processing as file: {item_name}")
            if self.download_drive_item(item, local_path):
                tqdm.write(f"Successfully downloaded: {item_name}")
            else:
                print(f"Failed to download: {item_name}")
        else:
            print(f"Skipping unprocessable item: {item_name}")

    except Exception as e:
        print(f"Error processing {getattr(item, 'name', 'unknown')}: {str(e)}")

class iFetch:
    def __init__(self, email: Optional[str] = None):
        """Initialize the downloader with user's iCloud email."""
        self.email = email or os.environ.get('ICLOUD_EMAIL')
        if not self.email:
            raise ValueError("Email must be provided via argument or ICLOUD_EMAIL environment variable")
        self.api: Optional[PyiCloudService] = None

    def authenticate(self) -> None:
        """Handle iCloud authentication including 2FA if needed."""
        try:
            # Initialize PyiCloudService with proper parameters
            params = {
                "apple_id": self.email.strip(),
                "password": None,  # Will be fetched from keyring
            }

            # Add china_mainland parameter only if specified
            if os.environ.get('ICLOUD_CHINA', '').lower() == 'true':
                params["china_mainland"] = True

            self.api = PyiCloudService(**params)

            # Handle 2FA if required
            if self.api.requires_2fa:
                print("\nTwo-factor authentication required.")
                code = input("Enter the verification code: ")
                if not self.api.validate_2fa_code(code):
                    raise Exception("Failed to verify 2FA code")

                # Request trust for the session
                if not self.api.is_trusted_session:
                    print("Session is not trusted. Requesting trust...")
                    if not self.api.trust_session():
                        print("Warning: Failed to trust session. You may need to re-authenticate later.")

            elif self.api.requires_2sa:
                print("\nTwo-step authentication required.")
                devices = self.api.trusted_devices
                if not devices:
                    raise Exception("No trusted devices found")

                for i, device in enumerate(devices):
                    print(f"{i}: {device.get('deviceName', 'SMS to ' + device.get('phoneNumber', 'unknown'))}")

                device_index = int(input("\nChoose a device to receive the verification code: "))
                if not 0 <= device_index < len(devices):
                    raise Exception("Invalid device selection")

                device = devices[device_index]
                if not self.api.send_verification_code(device):
                    raise Exception("Failed to send verification code")

                code = input("Enter the verification code: ")
                if not self.api.validate_verification_code(device, code):
                    raise Exception("Failed to verify verification code")

        except PyiCloudFailedLoginException:
            raise Exception("Invalid username/password. Please check your credentials.")
        except PyiCloudNoStoredPasswordAvailableException:
            raise Exception("No stored password found. Please run 'icloud --username=your@email.com' first.")
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

    def get_drive_item(self, path: str):
        """Navigate to a specific path in iCloud Drive."""
        if not self.api or not self.api.drive:
            raise Exception("Not authenticated or Drive service not available")

        item = self.api.drive
        if path.strip('/'):
            for part in path.strip('/').split('/'):
                try:
                    item = item[part]
                except (KeyError, AttributeError):
                    raise Exception(f"Path not found: {path}")
        return item

    def list_contents(self, path: str) -> None:
        """List contents of a directory in iCloud Drive."""
        try:
            item = self.get_drive_item(path)
            if hasattr(item, 'dir'):
                contents = item.dir()
                if not contents:
                    print(f"\nDirectory '{path}' is empty")
                    return

                print(f"\nContents of {path or '/'}: ")
                for name in contents:
                    sub_item = item[name]
                    is_file = can_read_file(sub_item)
                    print(f"- {name}{'' if is_file else '/'}")
            else:
                print(f"'{path}' is a file")
        except Exception as e:
            print(f"Error listing contents: {str(e)}")

    def download_drive_item(self, item, local_path: Path) -> bool:
        """Download a single file from iCloud Drive."""
        if not hasattr(item, 'name') or not hasattr(item, 'open'):
            return False

        try:
            # Create parent directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with item.open(stream=True) as response:
                total_size = int(response.headers.get('content-length', 0))

                with open(local_path, 'wb') as out_file, tqdm(
                    desc=f"Downloading {item.name}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for chunk in response.raw.stream(8192, decode_content=False):
                        if chunk:
                            out_file.write(chunk)
                            pbar.update(len(chunk))
            return True
        except Exception as e:
            if local_path.exists() and local_path.stat().st_size == 0:
                local_path.unlink()  # Remove empty file
            return False

    def process_item(self, item, local_path: Path) -> None:
        """Process an item, determining whether to treat it as a file or directory."""
        try:
            if can_read_file(item):
                # It's a readable file, download it
                if self.download_drive_item(item, local_path):
                    tqdm.write(f"Successfully downloaded: {item.name}")
                else:
                    print(f"Failed to download: {item.name}")
            elif hasattr(item, 'dir'):
                # Try to process as directory
                contents = item.dir()
                if contents:
                    local_path.mkdir(exist_ok=True)
                    for name in contents:
                        sub_item = item[name]
                        sub_path = local_path / name
                        self.process_item(sub_item, sub_path)
        except Exception as e:
            print(f"Error processing {getattr(item, 'name', 'unknown')}: {str(e)}")

    def download(self, icloud_path: str, local_path: str = '.') -> None:
        """Download files/folders from iCloud Drive to local directory."""
        if not self.api:
            self.authenticate()

        if not self.api or not self.api.drive:
            raise Exception("iCloud Drive service not available")

        try:
            # Convert to Path object
            local_path = Path(local_path).resolve()

            # Get the item from iCloud Drive
            item = self.get_drive_item(icloud_path)

            print(f"Processing: {icloud_path}")
            self.process_item(item, local_path)
            print("\nDownload completed successfully!")

        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <icloud_path> [local_path]")
        print("\nExample:")
        print("  python main.py Documents/MyFolder")
        print("  python main.py Documents/MyFolder /local/download/path")
        print("\nNote: Set ICLOUD_EMAIL environment variable or store password using:")
        print("  icloud --username=your@email.com")
        sys.exit(1)

    icloud_path = sys.argv[1]
    local_path = sys.argv[2] if len(sys.argv) > 2 else '.'

    try:
        ifetcher = iFetch()

        # List contents if --list flag is provided
        if '--list' in sys.argv:
            ifetcher.authenticate()
            ifetcher.list_contents(icloud_path)
        else:
            ifetcher.download(icloud_path, local_path)

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
