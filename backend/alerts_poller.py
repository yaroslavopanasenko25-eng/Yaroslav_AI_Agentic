"""Background polling for alerts.in.ua — keeps cache warm and builds local history."""

from __future__ import annotations

import asyncio
import logging

from alert_store import upsert_alerts
from alerts_service import get_alerts_service
from config import get_settings
from data_loader import transform_alerts
from database import upsert_rows
from regions_data import API_OBLAST_UID_TO_SLUG


async def alerts_poll_loop() -> None:
    """Poll active alerts and gradually backfill regional history."""
    svc = get_alerts_service()
    history_cursor = 0

    while True:
        settings = get_settings()
        interval = settings.alerts_poll_interval_seconds

        try:
            changed_iot = await asyncio.to_thread(svc.refresh_oblast_iot, force=True)
            changed_active = await asyncio.to_thread(svc.refresh_active, force=True)
            alerts = svc.get_alerts()

            if alerts:
                records = transform_alerts(alerts)
                # Statistics: store finished alerts + ongoing for tracking
                stored = await asyncio.to_thread(upsert_alerts, records)
                if stored:
                    logger.info("Stored %d alert record(s) locally", stored)

                if "your-project" not in settings.supabase_url:
                    try:
                        await asyncio.to_thread(upsert_rows, "alerts", records)
                    except RuntimeError as exc:
                        logger.debug("Supabase upsert skipped: %s", exc)

            if changed_active or changed_iot:
                logger.info(
                    "Alerts refreshed (active=%d, iot=%s)",
                    len(alerts),
                    "yes" if changed_iot else "cached",
                )

            # Slow history backfill using official oblast API UIDs
            api_oblast_uids = list(API_OBLAST_UID_TO_SLUG.keys())
            if api_oblast_uids and svc.get_source() == "live":
                uid = api_oblast_uids[history_cursor % len(api_oblast_uids)]
                history_cursor += 1
                raw_history = await asyncio.to_thread(svc.fetch_region_history, uid, "month_ago")
                if raw_history:
                    hist_records = transform_alerts(raw_history)
                    added = await asyncio.to_thread(upsert_alerts, hist_records)
                    if added:
                        logger.info("History sync uid=%s: %d record(s)", uid, added)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Alerts poll loop error: %s", exc)

        await asyncio.sleep(interval)
