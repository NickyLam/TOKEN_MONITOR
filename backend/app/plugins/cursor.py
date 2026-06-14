"""Cursor vendor plugin.

API Docs: https://docs.cursor.com/account/admin-api
Base URL: https://api.cursor.com
Auth: Basic Auth (API key as username, empty password)
Key format: crsr_xxx... (created in cursor.com/dashboard > Settings > Advanced > Admin API Keys)
Availability: Enterprise teams only
Rate limits: 20 req/min per team
"""

import base64
from datetime import datetime, timedelta

import httpx

from app.plugins.base import PlanType, PollResult, QuotaSnapshot, TokenUsageEntry, VendorPlugin
from app.plugins.registry import register_plugin


@register_plugin
class CursorPlugin(VendorPlugin):
    BASE_URL = "https://api.cursor.com"

    @property
    def slug(self) -> str:
        return "cursor"

    @property
    def display_name(self) -> str:
        return "Cursor"

    @property
    def supported_plan_types(self) -> list[PlanType]:
        return [PlanType.SUBSCRIPTION]

    def default_poll_interval_minutes(self) -> int:
        return 60

    def config_fields(self) -> list[dict]:
        """Required config fields for this vendor."""
        return [
            {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "crsr_xxx...", "help": "Admin API Key from Cursor Dashboard > Settings > Advanced"},
            {"key": "team_id", "label": "Team ID", "type": "text", "placeholder": "", "help": "Your Cursor team ID (found in team settings URL)"},
        ]

    def _auth_header(self, api_key: str) -> str:
        """Basic Auth: base64(api_key:)"""
        return "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()

    async def poll(self, plan_config: dict) -> PollResult:
        """Poll Cursor admin API for usage data."""
        api_key = plan_config.get("api_key", "")
        extra = plan_config.get("extra_config", {})

        if not api_key:
            return PollResult(raw_response={"error": "No API key configured"})

        headers = {"Authorization": self._auth_header(api_key), "Content-Type": "application/json"}

        now = datetime.utcnow()
        start_epoch_ms = int((now - timedelta(days=30)).timestamp() * 1000)
        end_epoch_ms = int(now.timestamp() * 1000)

        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Get spend data
            spend_resp = await client.post(
                f"{self.BASE_URL}/teams/spend",
                headers=headers,
                json={"page": 1, "pageSize": 100},
            )
            spend_resp.raise_for_status()
            spend_data = spend_resp.json()

            overall_spend_cents = spend_data.get("overallSpendCents", 0)
            fast_premium_requests = 0
            for item in spend_data.get("data", []):
                fast_premium_requests += item.get("fastPremiumRequests", 0)

            # 2. Get filtered usage events for token details
            events_resp = await client.post(
                f"{self.BASE_URL}/teams/filtered-usage-events",
                headers=headers,
                json={
                    "startDate": start_epoch_ms,
                    "endDate": end_epoch_ms,
                    "page": 1,
                    "pageSize": 200,
                },
            )
            events_resp.raise_for_status()
            events_data = events_resp.json()

        events = events_data.get("events", [])
        token_entries = []
        for event in events:
            if event.get("isTokenBasedCall") and event.get("tokenUsage"):
                tu = event["tokenUsage"]
                token_entries.append(TokenUsageEntry(
                    model=event.get("model", "unknown"),
                    input_tokens=tu.get("inputTokens", 0),
                    output_tokens=tu.get("outputTokens", 0),
                    cache_read_tokens=tu.get("cacheReadTokens", 0),
                    cache_write_tokens=tu.get("cacheWriteTokens", 0),
                    cost_usd=tu.get("totalCents", 0) / 100.0,
                ))

        quota_total = plan_config.get("extra_config", {}).get("quota_limit", 500)

        return PollResult(
            quota=QuotaSnapshot(
                used=fast_premium_requests,
                total=float(quota_total),
                unit="requests",
            ),
            token_entries=token_entries,
            total_cost_usd=overall_spend_cents / 100.0,
            raw_response={"spend": spend_data, "events": events_data},
        )
