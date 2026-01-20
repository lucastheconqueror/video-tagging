"""CLI entry point for VideoTagger."""

import json
import sys

from dotenv import load_dotenv
from pydantic import ValidationError

from videotagger.config import Settings, mask_credential
from videotagger.exceptions import LLMError, VideoProcessingError
from videotagger.logging_config import setup_logging
from videotagger.pipeline import process_video

# Global debug flag
DEBUG = False


def validate_config() -> int:
    """Validate configuration and display status.

    Returns:
        Exit code: 0 for success, 1 for validation errors.
    """
    # Load .env file
    load_dotenv()

    try:
        settings = Settings()
    except ValidationError as e:
        print("Configuration validation failed!\n")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            print(f"  - {field}: {msg}")
        print("\nPlease check your .env file or environment variables.")
        return 1

    print("Configuration validated successfully!\n")

    # Display masked credentials
    print("Synology NAS:")
    print(f"  Host: {settings.synology.host}")
    print(f"  User: {settings.synology.user}")
    print(f"  Password: {mask_credential(settings.synology.password)}")
    print(f"  Video Path: {settings.synology.video_path}")

    print("\nAirtable:")
    print(f"  API Key: {mask_credential(settings.airtable.api_key)}")
    print(f"  Base ID: {settings.airtable.base_id}")
    print(f"  Table ID: {settings.airtable.table_id}")

    print("\nRunPod S3:")
    print(f"  Endpoint: {settings.runpod_s3.endpoint}")
    print(f"  Bucket: {settings.runpod_s3.bucket}")
    print(f"  Access Key: {mask_credential(settings.runpod_s3.access_key)}")
    print(f"  Secret Key: {mask_credential(settings.runpod_s3.secret_key)}")

    print("\nRunPod SSH:")
    print(f"  Host: {settings.runpod_ssh.host}")
    print(f"  User: {settings.runpod_ssh.user}")
    print(f"  Key Path: {settings.runpod_ssh.key_path}")
    print(f"  Pod ID: {settings.runpod_ssh.pod_id}")

    return 0


def process_video_command(video_path: str) -> int:
    """Process a video file and output tags as JSON.

    Args:
        video_path: Path to the video file.

    Returns:
        Exit code: 0 for success, 1 for errors.
    """
    load_dotenv()

    try:
        print(f"Processing video: {video_path}")
        tags = process_video(video_path)
        print("\nExtracted tags:")
        print(json.dumps(tags, indent=2, ensure_ascii=False))
        return 0

    except VideoProcessingError as e:
        print(f"Video processing error: {e}")
        return 1

    except LLMError as e:
        print(f"LLM error: {e}")
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def run_tui() -> int:
    """Run the TUI application.

    Returns:
        Exit code: 0 for success.
    """
    load_dotenv()

    from videotagger.tui.app import run_tui as start_tui

    start_tui()
    return 0


def main() -> None:
    """Main CLI entry point."""
    # Default to TUI if no command given
    if len(sys.argv) < 2:
        sys.exit(run_tui())

    command = sys.argv[1]

    if command == "tui":
        sys.exit(run_tui())
    elif command == "validate-config":
        sys.exit(validate_config())
    elif command == "process":
        if len(sys.argv) < 3:
            print("Usage: python -m videotagger process <video_path>")
            sys.exit(1)
        sys.exit(process_video_command(sys.argv[2]))
    elif command in ["--help", "-h"]:
        print("Usage: python -m videotagger [command] [args]")
        print("\nCommands:")
        print("  tui                   Launch interactive TUI (default)")
        print("  validate-config       Validate configuration and display status")
        print("  process <video_path>  Process a video and extract tags")
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: tui, validate-config, process")
        print("Run with --help for more information")
        sys.exit(1)


if __name__ == "__main__":
    main()
