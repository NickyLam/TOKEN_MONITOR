"""OpenAI vendor plugin.

API Docs: https://platform.openai.com/docs/api-reference
Base URL: https://api.openai.com
Auth: Authorization: Bearer $OPENAI_ADMIN_KEY (Admin API key, NOT regular API key)
Optional header: OpenAI-Organization: org_xxx
Key endpoints:
  - GET /v1/organization/usage/completions  (token usage by model)
  - GET /v1/organization/costs              (daily spend in USD)
Required params: start_time (Unix seconds, inclusive)
"""

import time
from datetime import datetime, timedelta

import httpx

from app.plugins.base import PlanType, PollResult, TokenUsageEntry, VendorPlugin
from app.plugins.registry import register_plugin


@register_plugin
class OpenAIPlugin(VendorPlugin):
    BASE_URL = "https://api.openai.com"

    @property
    def slug(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI"

    @property
    def supported_plan_types(self) -> list[PlanType]:
        return [PlanType.TOKEN_CREDITS, PlanType.SUBSCRIPTION]

    def default_poll_interval_minutes(self) -> int:
        return 30

    def config_fields(self) -> list[dict]:
        return [
            {"key": "api_key", "label": "Admin API Key", "type": "password", "placeholder": "sk-admin-xxx...", "help": "Admin API key from platform.openai.com > Settings > Admin Keys (NOT a regular API key)"},
            {"key": "org_id", "label": "Organization ID", "type": "text", "placeholder": "org-xxx", "help": "Organization ID from platform.openai.com > Settings > Organization (optional)"},
        ]

    async def poll(self, plan_config: dict) -> PollResult:
        """Poll OpenAI organization usage API."""
        api_key = plan_config.get("api_key", "")
        extra = plan_config.get("extra_config", {})
        org_id = extra.get("org_id", "")

        if not api_key:
            return PollResult(raw_response={"error": "No API key configured"})

        headers = {"Authorization": f"Bearer {api_key}"}
        if org_id:
            headers["OpenAI-Organization"] = org_id

        # start_time: 30 days ago in Unix seconds
        start_time = int((datetime.utcnow() - timedelta(days=30)).timestamp())
        end_time = int(time.time())

        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Get completions usage
            completions_resp = await client.get(
                f"{self.BASE_URL}/v1/organization/usage/completions",
                headers=headers,
                params={
                    "start_time": start_time,
                    "end_time": end_time,
                    "bucket_width": "1d",
                    "group_by[]": "model",
                    "limit": 31,
                },
            )
            completions_resp.raise_for_status()
            completions_data = completions_resp.json()

            # 2. Get costs
            costs_resp = await client.get(
                f"{self.BASE_URL}/v1/organization/costs",
                headers=headers,
                params={
                    "start_time": start_time,
                    "end_time": end_time,
                    "bucket_width": "1d",
                    "group_by[]": "model",
                    "limit": 31,
                },
            )
            costs_resp.raise_for_status()
            costs_data = costs_resp.json()

        # Parse completions data
        token_entries = []
        model_totals: dict[str, dict] = {}

        for bucket in completions_data.get("data", []):
            result = bucket.get("result", {})
            items = result.get("items", []) if isinstance(result, dict) else []
            for item in items:
                model = item.get("model", "unknown")
                input_tokens = item.get("input_tokens", 0)
                output_tokens = item.get("output_tokens", 0)

                if model not in model_totals:
                    model_totals[model] = {"input": 0, "output": 0}
                model_totals[model]["input"] += input_tokens
                model_totals[model]["output"] += output_tokens

        # Parse cost data
        total_cost = 0.0
        model_costs: dict[str, float] = {}
        for bucket in costs_data.get("data", []):
            result = bucket.get("result", {})
            items = result.get("items", []) if isinstance(result, dict) else []
            for item in items:
                model = item.get("model", "unknown")
                cost = item.get("amount", 0.0)
                total_cost += cost
                model_costs[model] = model_costs.get(model, 0) + cost

        # Merge into token entries
        for model, totals in model_totals.items():
            token_entries.append(TokenUsageEntry(
                model=model,
                input_tokens=totals["input"],
                output_tokens=totals["output"],
                cost_usd=model_costs.get(model, 0.0),
            ))

        return PollResult(
            token_entries=token_entries,
            total_cost_usd=total_cost,
            raw_response={"completions": completions_data, "costs": costs_data},
        )
