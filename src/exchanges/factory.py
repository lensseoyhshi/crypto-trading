"""
Exchange factory for creating exchange instances
"""
from typing import Optional

from ..core.models import ExchangeType
from .base import BaseExchange
from .binance import BinanceExchange
from .okx import OKXExchange
from .gateio import GateIOExchange


class ExchangeFactory:
    """Factory for creating exchange instances"""
    
    @staticmethod
    def create_exchange(
        exchange_type: ExchangeType,
        api_key: str,
        secret_key: str,
        passphrase: Optional[str] = None,
        sandbox: bool = True
    ) -> BaseExchange:
        """Create an exchange instance based on type"""
        
        if exchange_type == ExchangeType.BINANCE:
            return BinanceExchange(api_key, secret_key, passphrase, sandbox)
        elif exchange_type == ExchangeType.OKX:
            return OKXExchange(api_key, secret_key, passphrase, sandbox)
        elif exchange_type == ExchangeType.GATEIO:
            return GateIOExchange(api_key, secret_key, passphrase, sandbox)
        else:
            raise ValueError(f"Unsupported exchange type: {exchange_type}")
    
    @staticmethod
    def get_supported_exchanges() -> list[ExchangeType]:
        """Get list of supported exchanges"""
        return [ExchangeType.BINANCE, ExchangeType.OKX, ExchangeType.GATEIO]
