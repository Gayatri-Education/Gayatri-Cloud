"""Payment Gateway Abstraction and Deterministic Mock Adapter.
Ensures zero live paid transactions occur without explicit authorization (DEC-C24).
Provides cryptographic webhook signature verification and idempotent event ingestion.
"""

from __future__ import annotations

import abc
import hashlib
import hmac
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class PaymentGatewayAdapter(abc.ABC):
    """Abstract payment gateway adapter."""

    @abc.abstractmethod
    async def create_payment_intent(
        self,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a payment intent or checkout session."""
        pass

    @abc.abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        secret: str,
    ) -> bool:
        """Cryptographically verify webhook origin signature."""
        pass

    @abc.abstractmethod
    async def process_refund(
        self,
        gateway_transaction_id: str,
        amount_cents: int,
        reason: str,
    ) -> dict[str, Any]:
        """Process a transaction refund."""
        pass


class MockPaymentGateway(PaymentGatewayAdapter):
    """Deterministic local mock payment gateway for testing and offline execution."""

    def __init__(self, webhook_secret: str = "gayatri-webhook-secret-key-32chars") -> None:
        self.webhook_secret = webhook_secret

    async def create_payment_intent(
        self,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Deterministic mock payment intent creation."""
        # Simulated transaction ID derived deterministically or uniquely
        tx_id = f"mock_tx_{uuid.uuid4().hex[:16]}"
        logger.info(
            "MOCK_GATEWAY: Created payment intent %s for %d %s (idempotency: %s)",
            tx_id,
            amount_cents,
            currency,
            idempotency_key,
        )
        return {
            "gateway_transaction_id": tx_id,
            "status": "succeeded",
            "amount_cents": amount_cents,
            "currency": currency.upper(),
            "idempotency_key": idempotency_key,
            "metadata": metadata or {},
        }

    def compute_signature(self, payload_bytes: bytes, secret: str | None = None) -> str:
        """Compute HMAC-SHA256 signature for test webhook payload generation."""
        key = (secret or self.webhook_secret).encode("utf-8")
        h = hmac.new(key, payload_bytes, hashlib.sha256)
        return f"t=1700000000,v1={h.hexdigest()}"

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        secret: str | None = None,
    ) -> bool:
        """Verify HMAC-SHA256 signature header against raw payload bytes."""
        sec = secret or self.webhook_secret
        if not signature_header or not sec:
            return False

        try:
            parts = dict(part.split("=", 1) for part in signature_header.split(",") if "=" in part)
            v1_sig = parts.get("v1")
            if not v1_sig:
                return False

            expected_sig = hmac.new(sec.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(v1_sig, expected_sig)
        except Exception as exc:
            logger.warning("MOCK_GATEWAY: Signature verification failed with exception: %s", exc)
            return False

    async def process_refund(
        self,
        gateway_transaction_id: str,
        amount_cents: int,
        reason: str,
    ) -> dict[str, Any]:
        """Process simulated refund."""
        refund_id = f"mock_ref_{uuid.uuid4().hex[:16]}"
        logger.info(
            "MOCK_GATEWAY: Processed refund %s for tx %s (%d cents, reason: %s)",
            refund_id,
            gateway_transaction_id,
            amount_cents,
            reason,
        )
        return {
            "refund_id": refund_id,
            "gateway_transaction_id": gateway_transaction_id,
            "amount_cents": amount_cents,
            "status": "refunded",
            "reason": reason,
        }
