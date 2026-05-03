"""
Analytics Processor — background async service.

Tick loop (default 1 Hz):
  1. Load all active cameras + their analytics configs from DB.
  2. For each (camera, analytics) pair, fetch latest detections.
  3. Evaluate the analytics rule against current detections.
  4. Persist AnalyticsEvents for any state changes.

Supported analytics types (from constants.analytics.AnalyticsType):
  LINE_CROSS_COUNT / ENTRANCE  →  line crossing IN / OUT counts
  PEOPLE_COUNTING_BY_ZONE      →  zone occupancy snapshot
  DWELL_TIME_BY_ZONE           →  dwell-time tracking + threshold alert
  PEOPLE_COUNTING              →  whole-camera headcount snapshot

Coordinate contract:
  Analytics config stores line/zone coords in normalised [0,1] space
  (as drawn on the canvas relative to the camera preview).
  Detection bboxes arrive in absolute pixels; the adapter normalises
  centroids to [0,1] using camera.video_info width/height (default 1920×1080).
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.db.crud.analytics_event import bulk_create
from app.db.models.camera import Camera
from app.db.models.analytics import Analytics
from app.db.schemas.analytics_event import AnalyticsEventCreate
from app.geometry_utils import detect_line_crossing, point_in_polygon, should_count_crossing
from app.services.detection_adapter import Detection, DetectionAdapter

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Per-analytic in-memory state
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class _TrackEntry:
    """State for a single tracked person within one analytics rule."""
    last_cx: Optional[float] = None
    last_cy: Optional[float] = None
    zone_entry_ts: Optional[float] = None   # wall-clock seconds, set when enters zone
    last_seen_ts: float = field(default_factory=time.time)
    dwell_alerted: bool = False             # True once dwell_alert has been emitted


@dataclass
class _AnalyticsState:
    """Accumulated state for one (camera_id, analytics_id) pair."""
    line_in: int = 0
    line_out: int = 0
    tracks: Dict[int, _TrackEntry] = field(default_factory=dict)
    tracks_in_zone: Set[int] = field(default_factory=set)

    def get_track(self, tid: int) -> _TrackEntry:
        if tid not in self.tracks:
            self.tracks[tid] = _TrackEntry()
        return self.tracks[tid]

    def evict_stale(self, max_age: float = 15.0) -> None:
        now = time.time()
        gone = [t for t, s in self.tracks.items() if now - s.last_seen_ts > max_age]
        for t in gone:
            self.tracks_in_zone.discard(t)
            del self.tracks[t]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _img_dims(camera: Camera) -> Tuple[int, int]:
    """Return (width, height) from camera.video_info, defaulting to 1920×1080."""
    info = camera.video_info or {}
    return int(info.get("width", 1920)), int(info.get("height", 1080))


def _line_cfg(config: dict) -> Optional[dict]:
    """Extract {x1,y1,x2,y2} line dict from analytics config, or None."""
    line = config.get("line") or {}
    keys = ("x1", "y1", "x2", "y2")
    if all(k in line for k in keys):
        return {k: float(line[k]) for k in keys}
    return None


def _zone_polygon(config: dict) -> Optional[list]:
    """Extract polygon [[x,y], ...] from analytics config, or None."""
    poly = config.get("zone_polygon") or config.get("zone") or []
    if len(poly) >= 3:
        return poly
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Rule evaluators — each returns a (possibly empty) list of AnalyticsEventCreate
# ──────────────────────────────────────────────────────────────────────────────

def _eval_line_crossing(
    camera_id: int,
    analytics_id: int,
    detections: List[Detection],
    config: dict,
    state: _AnalyticsState,
) -> List[AnalyticsEventCreate]:
    line = _line_cfg(config)
    if line is None:
        return []

    events: List[AnalyticsEventCreate] = []
    now = time.time()

    for det in detections:
        tid = det.track_id
        tr = state.get_track(tid)
        tr.last_seen_ts = now

        if tr.last_cx is not None:
            prev = {"x": tr.last_cx, "y": tr.last_cy}
            curr = {"x": det.cx, "y": det.cy}
            direction = detect_line_crossing(prev, curr, line)
            if direction and should_count_crossing(tid, direction, now):
                if direction == "IN":
                    state.line_in += 1
                    etype = "line_cross_in"
                else:
                    state.line_out += 1
                    etype = "line_cross_out"
                events.append(AnalyticsEventCreate(
                    camera_id=camera_id,
                    analytics_id=analytics_id,
                    event_type=etype,
                    value={
                        "track_id": tid,
                        "count_in": state.line_in,
                        "count_out": state.line_out,
                    },
                ))

        tr.last_cx = det.cx
        tr.last_cy = det.cy

    return events


def _eval_zone_occupancy(
    camera_id: int,
    analytics_id: int,
    detections: List[Detection],
    config: dict,
    state: _AnalyticsState,
) -> List[AnalyticsEventCreate]:
    poly = _zone_polygon(config)
    if poly is None:
        return []

    events: List[AnalyticsEventCreate] = []
    now = time.time()
    prev_in_zone = set(state.tracks_in_zone)
    current_in_zone: Set[int] = set()

    for det in detections:
        tid = det.track_id
        tr = state.get_track(tid)
        tr.last_seen_ts = now
        tr.last_cx, tr.last_cy = det.cx, det.cy
        if point_in_polygon(det.cx, det.cy, poly):
            current_in_zone.add(tid)

    # Emit enter events for newly-arrived tracks
    for tid in current_in_zone - prev_in_zone:
        events.append(AnalyticsEventCreate(
            camera_id=camera_id,
            analytics_id=analytics_id,
            event_type="zone_enter",
            value={"track_id": tid, "zone_count": len(current_in_zone)},
        ))

    # Emit exit events for departed tracks
    for tid in prev_in_zone - current_in_zone:
        events.append(AnalyticsEventCreate(
            camera_id=camera_id,
            analytics_id=analytics_id,
            event_type="zone_exit",
            value={"track_id": tid, "zone_count": len(current_in_zone)},
        ))

    state.tracks_in_zone = current_in_zone
    return events


def _eval_dwell_time(
    camera_id: int,
    analytics_id: int,
    detections: List[Detection],
    config: dict,
    state: _AnalyticsState,
) -> List[AnalyticsEventCreate]:
    poly = _zone_polygon(config)
    if poly is None:
        return []

    dwell_threshold = float(config.get("min_dwell_time", 30))
    events: List[AnalyticsEventCreate] = []
    now = time.time()
    active_tids: Set[int] = set()

    for det in detections:
        tid = det.track_id
        tr = state.get_track(tid)
        tr.last_seen_ts = now
        tr.last_cx, tr.last_cy = det.cx, det.cy

        if point_in_polygon(det.cx, det.cy, poly):
            active_tids.add(tid)
            if tr.zone_entry_ts is None:
                tr.zone_entry_ts = now
            dwell = now - tr.zone_entry_ts
            if dwell >= dwell_threshold and not tr.dwell_alerted:
                tr.dwell_alerted = True
                events.append(AnalyticsEventCreate(
                    camera_id=camera_id,
                    analytics_id=analytics_id,
                    event_type="dwell_alert",
                    value={"track_id": tid, "dwell_s": round(dwell, 1)},
                ))
        else:
            # Left zone — reset
            tr.zone_entry_ts = None
            tr.dwell_alerted = False

    state.tracks_in_zone = active_tids
    return events


def _eval_people_count(
    camera_id: int,
    analytics_id: int,
    detections: List[Detection],
    config: dict,
    state: _AnalyticsState,
) -> List[AnalyticsEventCreate]:
    """Emit a periodic headcount snapshot (person-class only)."""
    count = sum(1 for d in detections if d.class_name == "person")
    now = time.time()
    # Only emit if count changed or 60 s have passed (to avoid flooding)
    last_count = getattr(state, "_last_count", None)
    last_emit = getattr(state, "_last_count_emit", 0.0)
    if count != last_count or (now - last_emit) >= 60.0:
        state._last_count = count  # type: ignore[attr-defined]
        state._last_count_emit = now  # type: ignore[attr-defined]
        return [AnalyticsEventCreate(
            camera_id=camera_id,
            analytics_id=analytics_id,
            event_type="people_count_snapshot",
            value={"count": count},
        )]
    return []


# Map analytics type → evaluator function
_EVALUATORS = {
    "line_cross_count": _eval_line_crossing,
    "entrance": _eval_line_crossing,
    "people_counting_by_zone": _eval_zone_occupancy,
    "dwell_time_by_zone": _eval_dwell_time,
    "people_counting": _eval_people_count,
}


# ──────────────────────────────────────────────────────────────────────────────
# AnalyticsProcessor
# ──────────────────────────────────────────────────────────────────────────────

class AnalyticsProcessor:
    """
    Long-running async service.  Start with ``await processor.start()``,
    stop with ``await processor.stop()``.
    """

    def __init__(
        self,
        db_factory,
        detection_service_url: str,
        poll_interval: float = 1.0,
    ):
        self._db_factory = db_factory
        self._adapter = DetectionAdapter(detection_service_url)
        self._interval = poll_interval
        self._task: Optional[asyncio.Task] = None
        # Keyed by (camera_id: int, analytics_id: int)
        self._state: Dict[Tuple[int, int], _AnalyticsState] = {}

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="analytics_processor")
        logger.info("Analytics processor started (poll_interval=%.1fs)", self._interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._adapter.close()
        logger.info("Analytics processor stopped")

    # ── internal loop ─────────────────────────────────────────────────────────

    async def _run(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception:
                logger.exception("Analytics processor tick error")
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        db: Session = self._db_factory()
        try:
            cameras: List[Camera] = (
                db.query(Camera).filter(Camera.is_active == True).all()
            )
            if not cameras:
                return

            pending_events: List[AnalyticsEventCreate] = []

            for cam in cameras:
                cam_analytics: List[Analytics] = (
                    db.query(Analytics)
                    .join(Analytics.cameras)
                    .filter(
                        Camera.id == cam.id,
                        Analytics.is_active == True,
                    )
                    .all()
                )
                if not cam_analytics:
                    continue

                img_w, img_h = _img_dims(cam)
                detections = await self._adapter.fetch(
                    str(cam.id), img_w=img_w, img_h=img_h
                )
                if detections is None:
                    continue

                for anal in cam_analytics:
                    key = (cam.id, anal.id)
                    if key not in self._state:
                        self._state[key] = _AnalyticsState()
                    state = self._state[key]
                    state.evict_stale()

                    evaluator = _EVALUATORS.get(anal.type)
                    if evaluator is None:
                        continue

                    cfg: dict = anal.config or {}
                    try:
                        new_events = evaluator(cam.id, anal.id, detections, cfg, state)
                        pending_events.extend(new_events)
                    except Exception:
                        logger.exception(
                            "Evaluator error cam=%s analytics=%s type=%s",
                            cam.id, anal.id, anal.type,
                        )

            if pending_events:
                bulk_create(db, pending_events)
                logger.debug("Stored %d analytics events", len(pending_events))

        finally:
            db.close()

    # ── public read helpers (for routes / WebSocket future use) ───────────────

    def current_line_counts(self, camera_id: int, analytics_id: int) -> Dict[str, int]:
        state = self._state.get((camera_id, analytics_id))
        if state is None:
            return {"in": 0, "out": 0}
        return {"in": state.line_in, "out": state.line_out}

    def current_zone_count(self, camera_id: int, analytics_id: int) -> int:
        state = self._state.get((camera_id, analytics_id))
        return len(state.tracks_in_zone) if state else 0

    def live_summary(self) -> List[Dict[str, Any]]:
        """Snapshot of all active analytics states — useful for a status endpoint."""
        result = []
        for (cam_id, anal_id), state in self._state.items():
            result.append({
                "camera_id": cam_id,
                "analytics_id": anal_id,
                "line_in": state.line_in,
                "line_out": state.line_out,
                "zone_count": len(state.tracks_in_zone),
                "active_tracks": len(state.tracks),
            })
        return result
