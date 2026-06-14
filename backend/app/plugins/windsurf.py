"""Windsurf / Codeium vendor plugin.

API Docs: https://docs.codeium.com
Base URL: https://server.codeium.com/api/v1
Auth: Service key in request body: {"service_key": "your_key"}
Key creation: windsurf.com/team/settings > Service Keys section
Availability: Enterprise plans only
"""

import httpx

from app.plugins.base import PlanType, PollResult, QuotaSnapshot, VendorPlugin
from app.plugins.registry import register_plugin


@register_plugin
class WindsurfPlugin(VendorPlugin):
    BASE_URL = "https://server.codeium.com/api/v1"

    @property
    def slug(self) -> str:
        return "windsurf"

    @property
    def display_name(self) -> str:
        return "Windsurf"

    @property
    def supported_plan_types(self) -> list[PlanType]:
        return [PlanType.SUBSCRIPTION]

    def default_poll_interval_minutes(self) -> int:
        return 120

    def config_fields(self) -> list[dict]:
        return [
            {"key": "service_key", "label": "Service Key", "type": "password", "placeholder": "", "help": "Service key from windsurf.com/team/settings > Service Keys"},
        ]

    async def poll(self, plan_config: dict) -> PollResult:
        """Poll Windsurf/Codeium API for usage data."""
        service_key = plan_config.get("api_key", "") or plan_config.get("extra_config", {}).get("service_key", "")

        if not service_key:
            return PollResult(raw_response={"error": "No service key configured"})

        async with httpx.AsyncClient(timeout=30) as client:
            # Get team credit balance
            balance_resp = await client.post(
                f"{self.BASE_URL}/GetTeamCreditBalance",
                json={"service_key": service_key},
            )
            balance_resp.raise_for_status()
            balance_data = balance_resp.json()

            # Get analytics
            analytics_resp = await client.post(
                f"{self.BASE_URL}/Analytics",
                json={
                    "service_key": service_key,
                    "query_data_sources": [
                        "QUERY_DATA_SOURCE_CHAT_DATA",
                        "QUERY_DATA_SOURCE_USER_DATA",
                    ],
                },
            )
            analytics_resp.raise_for_status()
            analytics_data = analytics_resp.json()

        # Parse credit balance
        credits_used = balance_data.get("credits_used", 0)
        credits_total = balance_data.get("credits_total", 0)

        return PollResult(
            quota=QuotaSnapshot(
                used=float(credits_used),
                total=float(credits_total),
                unit="credits",
            ) if credits_total > 0 else None,
            raw_response={"balance": balance_data, "analytics": analytics_data},
        )
