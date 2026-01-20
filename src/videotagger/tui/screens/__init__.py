"""TUI screens for VideoTagger."""

from videotagger.tui.screens.batch_review import BatchReviewScreen
from videotagger.tui.screens.json_preview import JSONPreviewScreen
from videotagger.tui.screens.local_video import LocalVideoScreen
from videotagger.tui.screens.main_menu import MainMenuScreen
from videotagger.tui.screens.runpod_process import RunPodProcessScreen
from videotagger.tui.screens.runpod_sync import RunPodSyncScreen
from videotagger.tui.screens.synology_browser import SynologyBrowserScreen

__all__ = [
    "MainMenuScreen",
    "LocalVideoScreen",
    "JSONPreviewScreen",
    "SynologyBrowserScreen",
    "RunPodSyncScreen",
    "RunPodProcessScreen",
    "BatchReviewScreen",
]
