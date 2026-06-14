"""Anthropic vendor plugin.

API Docs: https://docs.anthropic.com
Base URL: https://api.anthropic.com
Auth: x-api-key header + anthropic-version: 2023-06-01
Key endpoints:
  - /v1/organizations/usage_report/claude_code  (Claude Code analytics)
  - Organization Usage & Cost API (Platform plans)
  - Analytics API (Enterprise plans)
"""

from datetime import datetime, timedelta

import httpx

from app.plugins.base import PlanType, PollResult, TokenUsageEntry, VendorPlugin
from app.plugins.registry import register_plugin


@register_plugin
class AnthropicPlugin(VendorPlugin):
    BASE_URL = "https://api.anthropic.com"

    @property
    def slug(self) -> str:
        return "anthropic"

    @property
    def display_name(self) -> str:
        return "Anthropic"

    @property
    def supported_plan_types(self) -> list[PlanType]:
        return [PlanType.TOKEN_CREDITS, PlanType.SUBSCRIPTION]

    def default_poll_interval_minutes(self) -> int:
        return 30

    def config_fields(self) -> list[dict]:
        return [
            {"key": "api_key", "label": "API Key / Admin Key", "type": "password", "placeholder": "sk-ant-xxx...", "help": "API key from console.anthropic.com or Admin key from organization settings"},
            {"key": "organization_id", "label": "Organization ID", "type": "text", "placeholder": "org_xxx", "help": "Your Anthropic organization ID (optional)"},
        ]

    async def poll(self, plan_config: dict) -> PollResult:
        """Poll Anthropic usage API for token consumption."""
        api_key = plan_config.get("api_key", "")
        extra = plan_config.get("extra_config", {})
        org_id = extra.get("organization_id", "")

        if not api_key:
            return PollResult(raw_response={"error": "No API key configured"})

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # Try Claude Code usage report endpoint
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            params = {"starting_at": start_date, "limit": 100}
            if org_id:
                params["organization_id"] = org_id

            resp = await client.get(
                f"{self.BASE_URL}/v1/organizations/usage_report/claude_code",
                headers=headers,
                params=params,
            )

            if resp.status_code == 404:
                # Fallback: try general usage endpoint
                resp = await client.get(
                    f"{self.BASE_URL}/v1/usage",
                    headers=headers,
                    params={"start_date": start_date},
                )

            resp.raise_for_status()
            data = resp.json()

        token_entries = []
        total_cost = 0.0

        for item in data.get("data", []):
            model = item.get("model", "unknown")
            usage = item.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)
            cache_write = usage.get("cache_creation_input_tokens", 0)
            cost = item.get("cost_usd", 0.0)
            total_cost += cost

            token_entries.append(TokenUsageEntry(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                cost_usd=cost,
            ))

        return PollResult(
            token_entries=token_entries,
            total_cost_usd=total_cost,
            raw_response=data,
        )
