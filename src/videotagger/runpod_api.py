"""RunPod API client for pod management.

Manages GPU pods for running vLLM inference on uploaded videos.
"""

import logging
from dataclasses import dataclass

import runpod

from videotagger.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PodStatus:
    """Status of a RunPod pod."""

    pod_id: str
    name: str
    status: str  # RUNNING, STOPPED, etc.
    gpu_type: str
    uptime_seconds: int | None = None
    cost_per_hour: float | None = None


def init_runpod() -> None:
    """Initialize RunPod SDK with API key from settings."""
    config = get_settings().runpod_api
    runpod.api_key = config.api_key
    logger.debug("RunPod API initialized")


def get_pods() -> list[PodStatus]:
    """Get list of all pods.

    Returns:
        List of PodStatus objects.
    """
    init_runpod()

    try:
        pods = runpod.get_pods()
        result = []

        for pod in pods:
            # Determine status from desiredStatus or runtime
            desired = pod.get("desiredStatus", "").upper()
            runtime = pod.get("runtime")

            if desired == "RUNNING" or (runtime and runtime.get("uptimeInSeconds", 0) > 0):
                status = "RUNNING"
                uptime = runtime.get("uptimeInSeconds") if runtime else None
            elif desired == "EXITED" or desired == "STOPPED":
                status = "STOPPED"
                uptime = None
            else:
                status = desired or "UNKNOWN"
                uptime = None

            result.append(
                PodStatus(
                    pod_id=pod["id"],
                    name=pod.get("name", "Unknown"),
                    status=status,
                    gpu_type=pod.get("machine", {}).get("gpuDisplayName", "Unknown"),
                    uptime_seconds=uptime,
                    cost_per_hour=pod.get("costPerHr"),
                )
            )

        logger.info(f"Found {len(result)} pods")
        return result

    except Exception as e:
        logger.error(f"Failed to get pods: {e}")
        return []


def get_pod(pod_id: str) -> PodStatus | None:
    """Get status of a specific pod.

    Args:
        pod_id: The pod ID to query.

    Returns:
        PodStatus or None if not found.
    """
    pods = get_pods()
    for pod in pods:
        if pod.pod_id == pod_id:
            return pod
    return None


def start_pod(pod_id: str) -> bool:
    """Start/resume a stopped pod.

    Args:
        pod_id: The pod ID to start.

    Returns:
        True if successful, False otherwise.
    """
    init_runpod()

    try:
        runpod.resume_pod(pod_id, gpu_count=1)
        logger.info(f"Started pod: {pod_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to start pod {pod_id}: {e}")
        return False


def stop_pod(pod_id: str) -> bool:
    """Stop a running pod.

    Args:
        pod_id: The pod ID to stop.

    Returns:
        True if successful, False otherwise.
    """
    init_runpod()

    try:
        runpod.stop_pod(pod_id)
        logger.info(f"Stopped pod: {pod_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to stop pod {pod_id}: {e}")
        return False


def get_configured_pod_status() -> PodStatus | None:
    """Get status of the pod configured in settings.

    Returns:
        PodStatus of configured pod, or None if not found.
    """
    pod_id = get_settings().runpod_ssh.pod_id
    return get_pod(pod_id)


def ensure_pod_running() -> tuple[bool, str]:
    """Ensure the configured pod is running.

    Returns:
        Tuple of (success, message).
    """
    pod_id = get_settings().runpod_ssh.pod_id
    pod = get_pod(pod_id)

    if pod is None:
        return False, f"Pod {pod_id} not found"

    if pod.status == "RUNNING":
        return True, f"Pod {pod.name} is already running"

    logger.info(f"Starting pod {pod.name}...")
    if start_pod(pod_id):
        return True, f"Started pod {pod.name}"
    else:
        return False, f"Failed to start pod {pod.name}"
