"""
Detection adapter — normalised interface to fetch latest per-camera detections
from any configured inference service (DeepStream, standard AI, OpenVINO, RK3588).

All backends expose:
  GET {service_url}/shared/cameras/{camera_id}/detections/latest
  → {"camera_id": str, "detections": [...], "detection_count": int}

Each detection dict has these keys (after translation by each service):
  camera_id, track_id, bbox [x1,y1,x2,y2] in pixels, class_name, confidence, timestamp
"""

import logging
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


class Detection:
    """Normalised detection with a computed centroid."""

    __slots__ = ("camera_id", "track_id", "class_name", "confidence",
                 "bbox", "cx", "cy", "ts")

    def __init__(self, raw: dict, img_w: int = 1920, img_h: int = 1080):
        self.camera_id: str = str(raw.get("camera_id", ""))
        self.track_id: int = int(raw.get("track_id") or 0)
        self.class_name: str = raw.get("class_name", "person")
        self.confidence: float = float(raw.get("confidence", 0.0))
        self.ts: int = int(raw.get("timestamp", 0))

        bbox = raw.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = (float(v) for v in bbox[:4])
        self.bbox: Tuple[float, float, float, float] = (x1, y1, x2, y2)

        # Normalised centroid in [0, 1] × [0, 1]
        self.cx: float = ((x1 + x2) / 2.0) / max(img_w, 1)
        self.cy: float = ((y1 + y2) / 2.0) / max(img_h, 1)


class DetectionAdapter:
    """
    Polls the configured inference service for latest per-camera detections.
    Stateless — create once at startup and share across the processor.
    """

    def __init__(self, service_url: str):
        self._url = service_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(3.0))

    async def fetch(
        self,
        camera_id: str,
        img_w: int = 1920,
        img_h: int = 1080,
        object_filter: str = "person",
    ) -> Optional[List[Detection]]:
        """
        Return normalised detections for *camera_id*, or None if the service
        is unavailable or returns no data.
        """
        try:
            url = f"{self._url}/shared/cameras/{camera_id}/detections/latest"
            params: Dict = {}
            if object_filter:
                params["object_filter"] = object_filter
            r = await self._client.get(url, params=params)
            if r.status_code == 200:
                data = r.json()
                raws = data.get("detections") or []
                return [Detection(d, img_w, img_h) for d in raws]
            if r.status_code not in (404, 503):
                logger.debug("fetch %s → HTTP %s", camera_id, r.status_code)
        except httpx.TimeoutException:
            logger.debug("fetch %s timed out", camera_id)
        except Exception as exc:
            logger.debug("fetch %s error: %s", camera_id, exc)
        return None

    async def close(self) -> None:
        await self._client.aclose()
