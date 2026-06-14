"""Stub vendor plugins for vendors without documented public APIs.

These plugins return mock/empty data and serve as templates for when
actual API documentation becomes available. Each includes config_fields()
describing what configuration is needed.
"""

from app.plugins.base import PlanType, PollResult, VendorPlugin
from app.plugins.registry import register_plugin


class StubPlugin(VendorPlugin):
    """Base stub plugin for vendors without public APIs."""

    _slug: str = ""
    _display_name: str = ""
    _plan_types: list[PlanType] = [PlanType.SUBSCRIPTION, PlanType.TOKEN_CREDITS]
    _config_fields: list[dict] = []

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def supported_plan_types(self) -> list[PlanType]:
        return self._plan_types

    def config_fields(self) -> list[dict]:
        return self._config_fields

    async def poll(self, plan_config: dict) -> PollResult:
        """Stub: returns empty result. Implement when API is available."""
        return PollResult(
            raw_response={"status": "stub", "message": f"No API integration for {self._display_name} yet"},
        )


@register_plugin
class CodebuddyPlugin(StubPlugin):
    _slug = "codebuddy"
    _display_name = "Codebuddy"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "Codebuddy API Key"},
    ]


@register_plugin
class QoderPlugin(StubPlugin):
    _slug = "qoder"
    _display_name = "Qoder"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "Qoder API Key"},
    ]


@register_plugin
class TraeCNPlugin(StubPlugin):
    _slug = "traecn"
    _display_name = "TraeCN"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "TraeCN API Key"},
    ]


@register_plugin
class QoderWorkPlugin(StubPlugin):
    _slug = "qoderwork"
    _display_name = "QoderWork"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "QoderWork API Key"},
    ]


@register_plugin
class QoderCNPlugin(StubPlugin):
    _slug = "qodercn"
    _display_name = "QoderCN"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "QoderCN API Key"},
    ]


@register_plugin
class QoderWorkCNPlugin(StubPlugin):
    _slug = "qoderworkcn"
    _display_name = "QoderWorkCN"
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "QoderWorkCN API Key"},
    ]


@register_plugin
class VoceEnginePlugin(StubPlugin):
    _slug = "voce_engine"
    _display_name = "VoceEngine"
    _plan_types = [PlanType.SUBSCRIPTION]
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "VoceEngine API Key"},
        {"key": "team_id", "label": "Team ID", "type": "text", "placeholder": "", "help": "VoceEngine Team ID"},
    ]


@register_plugin
class AstronPlugin(StubPlugin):
    _slug = "astron"
    _display_name = "Astron Coding Plan"
    _plan_types = [PlanType.SUBSCRIPTION]
    _config_fields = [
        {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "", "help": "Astron Coding Plan API Key"},
    ]
