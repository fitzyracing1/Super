"""Stripe usage-based (metered) billing.

After a tool call is authorized and executed successfully, the agent reports a
Stripe meter event so it can be sold per-action. This uses Stripe's v2 billing
meter events API via the official ``stripe`` SDK.

Billing is strictly best-effort: it must never block or fail a tool call. If the
SDK is missing, no key is configured, or Stripe returns an error, the failure is
logged and the tool result is returned unchanged (annotated ``billed: false``).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from .config import StripeConfig

logger = logging.getLogger("superuser.billing")


@dataclass
class BillingResult:
    billed: bool
    value: int = 0
    identifier: str | None = None
    detail: str | None = None


class StripeMeter:
    def __init__(self, config: StripeConfig) -> None:
        self.config = config
        self._client = None
        self._available = self._probe_sdk()
        if config.enabled and not self._available:
            logger.warning(
                "Stripe SDK not installed; usage will not be metered. "
                "Install with: pip install 'superuser[billing]'"
            )

    @staticmethod
    def _probe_sdk() -> bool:
        try:
            import stripe  # noqa: F401
        except Exception:
            return False
        return True

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not (self._available and self.config.can_bill):
            return None
        import stripe

        self._client = stripe.StripeClient(self.config.api_key)
        return self._client

    def record(self, tool_name: str) -> BillingResult:
        if not self.config.enabled:
            return BillingResult(billed=False, detail="billing disabled")
        client = self._get_client()
        if client is None:
            return BillingResult(billed=False, detail="billing not configured")

        value = self.config.value_for(tool_name)
        identifier = f"{tool_name}:{uuid.uuid4()}"
        try:
            client.v2.billing.meter_events.create({
                "event_name": self.config.event_name,
                "identifier": identifier,
                "payload": {
                    "stripe_customer_id": self.config.customer_id,
                    "value": str(value),
                    "tool": tool_name,
                },
            })
            return BillingResult(billed=True, value=value, identifier=identifier)
        except Exception as exc:  # billing must never break the tool call
            logger.error("Stripe meter event failed for %s: %s", tool_name, exc)
            return BillingResult(billed=False, value=value, detail=str(exc))

    @property
    def status(self) -> dict:
        return {
            "sdk_installed": self._available,
            "enabled": self.config.enabled,
            "configured": bool(self.config.can_bill),
            "event_name": self.config.event_name,
        }
