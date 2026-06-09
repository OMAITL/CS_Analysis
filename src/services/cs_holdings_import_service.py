# -*- coding: utf-8 -*-
"""CS holdings import preview sessions: Vision/manual/CSV -> Draft -> Commit."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

from src.repositories.cs_holding_import_repo import CSHoldingImportRepository
from src.repositories.cs_holdings_repo import CSHoldingsRepository
from src.services.cs_holdings_dedup import attach_dedup_fields, compute_dedup_key, reconcile_item_name_and_wear
from src.services.cs_holdings_match_engine import MatchResult, match_holding_item, rematch_with_manual_good_id
from src.services.image_cs_holdings_extractor import extract_cs_holdings_from_image

logger = logging.getLogger(__name__)

ImportSource = Literal["manual", "vision", "csv"]
_SESSION_TTL_SECONDS = 3600
_sessions_lock = threading.Lock()
_sessions: Dict[str, Dict[str, Any]] = {}


@dataclass
class CSHoldingDraft:
    draft_id: str
    source: ImportSource
    item_name: str
    wear: str = ""
    float_value: Optional[float] = None
    platform: str = "yyyp"
    quantity: int = 1
    purchase_price: float = 0.0
    market_price: Optional[float] = None
    good_id: Optional[int] = None
    market_hash_name: str = ""
    match_tier: str = "none"
    match_confidence: str = "low"
    match_score: float = 0.0
    vision_confidence: str = "medium"
    dedup_key: str = ""
    duplicate_of: Optional[int] = None
    checked: bool = True
    candidates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _cleanup_sessions() -> None:
    now = time.time()
    expired = [
        sid for sid, payload in _sessions.items()
        if now - float(payload.get("updated_at") or payload.get("created_at") or 0) > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _sessions.pop(sid, None)


def _apply_match_to_draft(draft: CSHoldingDraft, match: MatchResult) -> CSHoldingDraft:
    draft.good_id = match.good_id
    if match.item_name:
        draft.item_name = match.item_name
    item_name, wear = reconcile_item_name_and_wear(draft.item_name, draft.wear)
    draft.item_name = item_name
    draft.wear = wear
    draft.market_hash_name = match.market_hash_name or draft.market_hash_name
    draft.match_tier = match.match_tier
    draft.match_confidence = match.match_confidence
    draft.match_score = match.match_score
    draft.candidates = match.candidates
    draft.dedup_key = compute_dedup_key(
        item_name=draft.item_name,
        wear=draft.wear,
        float_value=draft.float_value,
        platform=draft.platform,
    )
    return draft


class CSHoldingsImportService:
    def __init__(
        self,
        holdings_repo: Optional[CSHoldingsRepository] = None,
        import_repo: Optional[CSHoldingImportRepository] = None,
    ):
        self.holdings_repo = holdings_repo or CSHoldingsRepository()
        self.import_repo = import_repo or CSHoldingImportRepository()

    def _attach_duplicate_flags(self, drafts: List[CSHoldingDraft]) -> List[CSHoldingDraft]:
        keys = [d.dedup_key for d in drafts if d.dedup_key]
        existing = self.holdings_repo.find_by_dedup_keys(keys)
        by_key = {row.dedup_key: row.id for row in existing if row.dedup_key}
        for draft in drafts:
            draft.duplicate_of = by_key.get(draft.dedup_key)
        return drafts

    def _build_draft(
        self,
        *,
        source: ImportSource,
        raw: Dict[str, Any],
    ) -> CSHoldingDraft:
        draft = CSHoldingDraft(
            draft_id=str(uuid.uuid4()),
            source=source,
            item_name=str(raw.get("item_name") or "").strip(),
            wear=str(raw.get("wear") or "").strip(),
            float_value=raw.get("float_value"),
            platform=str(raw.get("platform") or "yyyp").strip().lower() or "yyyp",
            quantity=max(1, int(raw.get("quantity") or 1)),
            purchase_price=float(raw.get("purchase_price") or 0),
            market_price=raw.get("market_price"),
            good_id=raw.get("good_id"),
            vision_confidence=str(raw.get("confidence") or raw.get("vision_confidence") or "medium"),
            checked=str(raw.get("confidence") or raw.get("vision_confidence") or "medium").lower() != "low",
        )
        if draft.item_name:
            match = match_holding_item(
                item_name=draft.item_name,
                wear=draft.wear,
                good_id=draft.good_id,
            )
            _apply_match_to_draft(draft, match)
            if draft.match_confidence == "low" or draft.vision_confidence == "low":
                draft.match_confidence = "low"
        else:
            draft.dedup_key = compute_dedup_key(
                item_name=draft.item_name,
                wear=draft.wear,
                float_value=draft.float_value,
                platform=draft.platform,
            )
        return draft

    def preview_from_items(
        self,
        *,
        source: ImportSource,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        with _sessions_lock:
            _cleanup_sessions()

        drafts = [self._build_draft(source=source, raw=raw) for raw in items if str(raw.get("item_name") or "").strip()]
        drafts = self._attach_duplicate_flags(drafts)
        session_id = str(uuid.uuid4())
        now = time.time()
        payload = {
            "session_id": session_id,
            "source": source,
            "drafts": [d.to_dict() for d in drafts],
            "created_at": now,
            "updated_at": now,
        }
        with _sessions_lock:
            _sessions[session_id] = payload
        return {
            "session_id": session_id,
            "source": source,
            "summary": self._summarize_drafts(drafts),
            "drafts": [d.to_dict() for d in drafts],
        }

    def preview_from_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        parsed, _raw_text = extract_cs_holdings_from_image(image_bytes, mime_type)
        items = list(parsed.get("items") or [])
        result = self.preview_from_items(source="vision", items=items)
        result["vision_summary"] = parsed.get("summary") or {}
        return result

    def update_session_drafts(
        self,
        session_id: str,
        drafts: List[Dict[str, Any]],
        *,
        rematch: bool = True,
    ) -> Dict[str, Any]:
        with _sessions_lock:
            session = _sessions.get(session_id)
            if session is None:
                raise ValueError("import session not found or expired")

        updated: List[CSHoldingDraft] = []
        for raw in drafts:
            draft = CSHoldingDraft(
                draft_id=str(raw.get("draft_id") or uuid.uuid4()),
                source=str(raw.get("source") or session.get("source") or "manual"),  # type: ignore[arg-type]
                item_name=str(raw.get("item_name") or "").strip(),
                wear=str(raw.get("wear") or "").strip(),
                float_value=raw.get("float_value"),
                platform=str(raw.get("platform") or "yyyp").strip().lower() or "yyyp",
                quantity=max(1, int(raw.get("quantity") or 1)),
                purchase_price=float(raw.get("purchase_price") or 0),
                market_price=raw.get("market_price"),
                good_id=raw.get("good_id"),
                market_hash_name=str(raw.get("market_hash_name") or ""),
                vision_confidence=str(raw.get("vision_confidence") or "medium"),
                checked=bool(raw.get("checked", True)),
                match_tier=str(raw.get("match_tier") or "none"),
                match_confidence=str(raw.get("match_confidence") or "low"),
                match_score=float(raw.get("match_score") or 0),
                candidates=list(raw.get("candidates") or []),
            )
            if rematch and draft.item_name:
                if draft.good_id is not None and raw.get("manual_good_id"):
                    match = rematch_with_manual_good_id(
                        item_name=draft.item_name,
                        wear=draft.wear,
                        good_id=int(draft.good_id),
                        candidate_name=str(raw.get("matched_name") or draft.item_name),
                        candidate_mhn=draft.market_hash_name,
                    )
                else:
                    match = match_holding_item(
                        item_name=draft.item_name,
                        wear=draft.wear,
                        good_id=draft.good_id,
                    )
                _apply_match_to_draft(draft, match)
            else:
                draft.dedup_key = compute_dedup_key(
                    item_name=draft.item_name,
                    wear=draft.wear,
                    float_value=draft.float_value,
                    platform=draft.platform,
                )
            updated.append(draft)

        updated = self._attach_duplicate_flags(updated)
        with _sessions_lock:
            session = _sessions.get(session_id)
            if session is None:
                raise ValueError("import session not found or expired")
            session["drafts"] = [d.to_dict() for d in updated]
            session["updated_at"] = time.time()

        return {
            "session_id": session_id,
            "source": str(session.get("source") or "manual"),
            "summary": self._summarize_drafts(updated),
            "drafts": [d.to_dict() for d in updated],
        }

    def commit_session(
        self,
        session_id: str,
        *,
        draft_ids: Optional[List[str]] = None,
        skip_duplicates: bool = False,
    ) -> Dict[str, Any]:
        with _sessions_lock:
            session = _sessions.get(session_id)
        if session is None:
            raise ValueError("import session not found or expired")

        all_drafts = [CSHoldingDraft(**raw) for raw in session.get("drafts") or []]
        if draft_ids:
            wanted = set(draft_ids)
            selected = [d for d in all_drafts if d.draft_id in wanted]
        else:
            selected = [d for d in all_drafts if d.checked]

        to_create: List[Dict[str, Any]] = []
        skipped_duplicates = 0
        for draft in selected:
            if not draft.item_name.strip():
                continue
            if skip_duplicates and draft.duplicate_of is not None:
                skipped_duplicates += 1
                continue
            to_create.append(
                attach_dedup_fields(
                    {
                        "good_id": draft.good_id,
                        "item_name": draft.item_name,
                        "market_hash_name": draft.market_hash_name,
                        "wear": draft.wear,
                        "float_value": draft.float_value,
                        "platform": draft.platform,
                        "quantity": draft.quantity,
                        "purchase_price": draft.purchase_price,
                        "market_price": draft.market_price,
                        "note": "",
                    }
                )
            )

        if not to_create:
            with _sessions_lock:
                _sessions.pop(session_id, None)
            from src.services.cs_holdings_service import CSHoldingsService

            snapshot = CSHoldingsService(repo=self.holdings_repo).get_snapshot(refresh_prices=False)
            return {
                "batch_id": "",
                "imported_count": 0,
                "skipped_duplicates": skipped_duplicates,
                **snapshot,
            }

        batch_id = str(uuid.uuid4())
        self.import_repo.create_batch(
            {
                "id": batch_id,
                "source": str(session.get("source") or "manual"),
                "item_count": len(to_create),
                "status": "pending",
                "snapshot_json": json.dumps([d.to_dict() for d in selected], ensure_ascii=False),
            }
        )

        for payload in to_create:
            payload["import_batch_id"] = batch_id
        rows = self.holdings_repo.bulk_create(to_create)
        self.import_repo.mark_committed(batch_id, item_count=len(rows))

        with _sessions_lock:
            _sessions.pop(session_id, None)

        from src.services.cs_holdings_service import CSHoldingsService

        snapshot = CSHoldingsService(repo=self.holdings_repo).get_snapshot(refresh_prices=True)
        from src.services.cs_auto_alerts_service import maybe_sync_cs_auto_alerts

        maybe_sync_cs_auto_alerts()
        return {
            "batch_id": batch_id,
            "imported_count": len(rows),
            "skipped_duplicates": skipped_duplicates,
            **snapshot,
        }

    def _summarize_drafts(self, drafts: List[CSHoldingDraft]) -> Dict[str, Any]:
        duplicate_count = sum(1 for d in drafts if d.duplicate_of is not None)
        low_confidence = sum(1 for d in drafts if d.match_confidence == "low" or not d.good_id)
        return {
            "draft_count": len(drafts),
            "duplicate_count": duplicate_count,
            "low_confidence_count": low_confidence,
            "checked_count": sum(1 for d in drafts if d.checked),
        }
