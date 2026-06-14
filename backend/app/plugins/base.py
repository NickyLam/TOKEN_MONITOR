"""Base class for all vendor plugins."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PlanType(str, Enum):
    SUBSCRIPTION = "subscription"
    TOKEN_CREDITS = "token_credits"
    FREE_TIER = "free_tier"


@dataclass
class QuotaSnapshot:
    """Current quota state for a subscription plan."""
    used: float
    total: float
    unit: str  # "requests", "credits", "dollars"
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TokenUsageEntry:
    """A single token-usage record from API usage."""
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    request_count: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PollResult:
    """What a plugin returns from poll()."""
    quota: Optional[QuotaSnapshot] = None
    token_entries: list[TokenUsageEntry] = field(default_factory=list)
    total_cost_usd: Optional[float] = None
    raw_response: dict = field(default_factory=dict)


class VendorPlugin(ABC):
    """Base class every vendor adapter must implement."""

    @property
    @abstractmethod
    def slug(self) -> str:
        """Unique vendor identifier."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""

    @property
    @abstractmethod
    def supported_plan_types(self) -> list[PlanType]:
        """Which plan types this vendor supports."""

    @abstractmethod
    async def poll(self, plan_config: dict) -> PollResult:
        """Fetch current usage from the vendor API."""

    async def validate_credentials(self, config: dict) -> bool:
        """Test whether the provided API credentials are valid."""
        try:
            await self.poll(config)
            return True
        except Exception:
            return False

    def config_fields(self) -> list[dict]:
        """Return list of config fields this vendor requires.

        Each field: {"key": str, "label": str, "type": str, "placeholder": str, "help": str}
        """
        return []

    def default_poll_interval_minutes(self) -> int:
        """How often to poll this vendor."""
        return 60
