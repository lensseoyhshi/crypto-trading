"""
Webhook security utilities for signature verification
"""
import hmac
import hashlib
from typing import Optional

from fastapi import HTTPException, status
from loguru import logger

from ..core.config import get_settings


class WebhookSecurity:
    """Webhook security manager"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or get_settings().security.webhook_secret
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        try:
            if not self.secret_key:
                logger.warning("Webhook secret not configured, skipping signature verification")
                return True
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Remove any prefix (like "sha256=")
            if "=" in signature:
                signature = signature.split("=", 1)[1]
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False
    
    def generate_signature(self, payload: bytes) -> str:
        """Generate signature for payload"""
        try:
            signature = hmac.new(
                self.secret_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return f"sha256={signature}"
        except Exception as e:
            logger.error(f"Failed to generate signature: {e}")
            raise


# Global webhook security instance
_webhook_security = None


def get_webhook_security() -> WebhookSecurity:
    """Get global webhook security instance"""
    global _webhook_security
    if _webhook_security is None:
        _webhook_security = WebhookSecurity()
    return _webhook_security


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature"""
    webhook_security = get_webhook_security()
    return webhook_security.verify_signature(payload, signature)


def require_webhook_signature(payload: bytes, signature: Optional[str]):
    """Require valid webhook signature or raise HTTPException"""
    settings = get_settings()
    
    if not settings.webhooks.verify_signature:
        return  # Skip verification if disabled
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature"
        )
    
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
