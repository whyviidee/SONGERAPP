"""
Google Drive sync for SONGER.
Uploads music files to a configured Google Drive folder, skipping duplicates.
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
MUSIC_EXTENSIONS = {".mp3", ".flac", ".m4a", ".opus", ".ogg", ".wav", ".wma", ".aac", ".webm"}

# Paths
SONGER_DIR = Path(__file__).parent.parent
ENV_PATH = SONGER_DIR / ".env"
TOKEN_PATH = SONGER_DIR / "config" / "drive_token.json"


def _load_env():
    """Load .env and return config dict."""
    load_dotenv(ENV_PATH)
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    music_path = os.getenv("SONGER_MUSIC_PATH")

    if not client_id or not client_secret:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")

    # Default music path from SONGER config
    if not music_path:
        songer_config = Path.home() / ".songer" / "config.json"
        if songer_config.exists():
            cfg = json.loads(songer_config.read_text(encoding="utf-8"))
            music_path = cfg.get("download", {}).get("path", "")
        if not music_path:
            music_path = str(Path.home() / "Music" / "SONGER")

    # Expand ~ in path
    music_path = str(Path(music_path).expanduser())

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "folder_id": folder_id,
        "music_path": music_path,
    }


def authenticate(config):
    """Authenticate with Google Drive via OAuth2. Returns Drive service."""
    creds = None

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Build client config from env vars (no credentials.json file needed)
            client_config = {
                "installed": {
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds)


def list_drive_files(service, folder_id):
    """List all file names in the Drive folder. Returns set of filenames."""
    files = set()
    page_token = None

    while True:
        query = f"'{folder_id}' in parents and trashed = false"
        resp = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(name)",
            pageToken=page_token,
            pageSize=1000,
        ).execute()

        for f in resp.get("files", []):
            files.add(f["name"])

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def list_local_music(music_path, count=None, newest_first=True):
    """List music files in local folder. Returns list of Path objects."""
    music_dir = Path(music_path)
    if not music_dir.exists():
        raise FileNotFoundError(f"Music folder not found: {music_path}")

    # Collect all music files recursively
    files = []
    for f in music_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() in MUSIC_EXTENSIONS:
            files.append(f)

    # Sort by modification time (newest first by default)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=newest_first)

    if count:
        files = files[:count]

    return files


def upload_file(service, file_path, folder_id):
    """Upload a single file to Google Drive folder."""
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
    uploaded = service.files().create(body=metadata, media_body=media, fields="id, name").execute()

    return uploaded


def sync(count=None, files=None, dry_run=False):
    """
    Main sync function.
    - count: upload the N most recent files
    - files: list of specific file paths to upload
    - dry_run: just list what would be uploaded
    Returns dict with results.
    """
    config = _load_env()

    if not config["folder_id"]:
        return {"error": "GOOGLE_DRIVE_FOLDER_ID not set in .env. Set the ID of your Drive folder."}

    service = authenticate(config)

    # Get what's already on Drive
    existing = list_drive_files(service, config["folder_id"])

    # Get local files
    if files:
        local_files = [Path(f) for f in files if Path(f).exists()]
    else:
        local_files = list_local_music(config["music_path"], count=count)

    # Filter duplicates
    to_upload = [f for f in local_files if f.name not in existing]
    skipped = [f for f in local_files if f.name in existing]

    if dry_run:
        return {
            "would_upload": [f.name for f in to_upload],
            "skipped_duplicates": [f.name for f in skipped],
            "total_local": len(local_files),
        }

    # Upload
    uploaded = []
    errors = []
    for f in to_upload:
        try:
            result = upload_file(service, f, config["folder_id"])
            uploaded.append(result["name"])
            print(f"  Uploaded: {result['name']}")
        except Exception as e:
            errors.append({"file": f.name, "error": str(e)})
            print(f"  Error: {f.name} — {e}")

    return {
        "uploaded": uploaded,
        "skipped_duplicates": [f.name for f in skipped],
        "errors": errors,
        "total": len(uploaded),
    }


def list_remote(count=20):
    """List files currently on Drive."""
    config = _load_env()
    if not config["folder_id"]:
        return {"error": "GOOGLE_DRIVE_FOLDER_ID not set."}
    service = authenticate(config)
    files = list_drive_files(service, config["folder_id"])
    return sorted(files)[:count]


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SONGER → Google Drive sync")
    parser.add_argument("action", choices=["sync", "list-local", "list-remote", "auth"],
                        help="Action to perform")
    parser.add_argument("-n", "--count", type=int, help="Number of recent files")
    parser.add_argument("-f", "--files", nargs="+", help="Specific files to upload")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")

    args = parser.parse_args()

    if args.action == "auth":
        config = _load_env()
        service = authenticate(config)
        print("Auth OK!")

    elif args.action == "sync":
        result = sync(count=args.count, files=args.files, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "list-local":
        config = _load_env()
        files = list_local_music(config["music_path"], count=args.count or 20)
        for f in files:
            print(f"  {f.name}")

    elif args.action == "list-remote":
        files = list_remote(count=args.count or 20)
        for f in files:
            print(f"  {f}")
