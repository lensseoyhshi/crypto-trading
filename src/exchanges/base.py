"""
Base exchange interface and common functionality
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

import ccxt
from loguru import logger

from ..core.models import (
    ExchangeType, OrderSide, OrderType, OrderStatus, PositionSide,
    OrderResponse, PositionResponse, MarketData, Kline, BalanceInfo, AccountInfo
)


class BaseExchange(ABC):
    """Base class for all exchange implementations"""
    
    def __init__(self, api_key: str, secret_key: str, passphrase: Optional[str] = None, 
                 sandbox: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.sandbox = sandbox
        self.exchange = None
        self._initialize_exchange()
    
    @abstractmethod
    def _initialize_exchange(self):
        """Initialize the exchange client"""
        pass
    
    @property
    @abstractmethod
    def exchange_type(self) -> ExchangeType:
        """Get the exchange type"""
        pass
    
    async def test_connection(self) -> bool:
        """Test the exchange connection"""
        try:
            await self.get_account_info()
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {self.exchange_type}: {e}")
            return False
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account information including balances and positions"""
        pass
    
    @abstractmethod
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                          amount: Decimal, price: Optional[Decimal] = None,
                          stop_price: Optional[Decimal] = None,
                          **kwargs) -> OrderResponse:
        """Create a new order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order details"""
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None, 
                        status: Optional[OrderStatus] = None,
                        limit: int = 100) -> List[OrderResponse]:
        """Get list of orders"""
        pass
    
    @abstractmethod
    async def get_positions(self, symbol: Optional[str] = None) -> List[PositionResponse]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str, side: PositionSide,
                           amount: Optional[Decimal] = None) -> OrderResponse:
        """Close a position"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> MarketData:
        """Get current market ticker"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, limit: int = 100,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Kline]:
        """Get kline/candlestick data"""
        pass
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for the exchange"""
        # Remove common separators and convert to exchange format
        symbol = symbol.replace("-", "").replace("_", "").replace("/", "")
        return symbol.upper()
    
    def _ccxt_to_order_status(self, ccxt_status: str) -> OrderStatus:
        """Convert CCXT order status to our enum"""
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'cancelled': OrderStatus.CANCELLED,
            'rejected': OrderStatus.REJECTED,
            'pending': OrderStatus.PENDING,
        }
        return status_map.get(ccxt_status.lower(), OrderStatus.PENDING)
    
    def _ccxt_to_order_side(self, ccxt_side: str) -> OrderSide:
        """Convert CCXT order side to our enum"""
        return OrderSide.BUY if ccxt_side.lower() == 'buy' else OrderSide.SELL
    
    def _ccxt_to_order_type(self, ccxt_type: str) -> OrderType:
        """Convert CCXT order type to our enum"""
        type_map = {
            'market': OrderType.MARKET,
            'limit': OrderType.LIMIT,
            'stop': OrderType.STOP,
            'stop_limit': OrderType.STOP_LIMIT,
        }
        return type_map.get(ccxt_type.lower(), OrderType.MARKET)
    
    def _parse_ccxt_order(self, order_data: Dict[str, Any]) -> OrderResponse:
        """Parse CCXT order data to our OrderResponse model"""
        return OrderResponse(
            id=0,  # Will be set by database
            account_id=0,  # Will be set by caller
            exchange_order_id=str(order_data.get('id', '')),
            symbol=order_data.get('symbol', ''),
            side=self._ccxt_to_order_side(order_data.get('side', 'buy')),
            type=self._ccxt_to_order_type(order_data.get('type', 'market')),
            amount=Decimal(str(order_data.get('amount', 0))),
            price=Decimal(str(order_data.get('price', 0))) if order_data.get('price') else None,
            status=self._ccxt_to_order_status(order_data.get('status', 'pending')),
            filled_amount=Decimal(str(order_data.get('filled', 0))),
            filled_price=Decimal(str(order_data.get('average', 0))) if order_data.get('average') else None,
            fee=Decimal(str(order_data.get('fee', {}).get('cost', 0))),
            fee_currency=order_data.get('fee', {}).get('currency'),
            created_at=datetime.fromtimestamp(order_data.get('timestamp', 0) / 1000) if order_data.get('timestamp') else datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def _parse_ccxt_balance(self, balance_data: Dict[str, Any]) -> List[BalanceInfo]:
        """Parse CCXT balance data to our BalanceInfo model"""
        balances = []
        for currency, data in balance_data.items():
            if currency in ['info', 'free', 'used', 'total']:
                continue
            if isinstance(data, dict):
                total = Decimal(str(data.get('total', 0)))
                free = Decimal(str(data.get('free', 0)))
                used = Decimal(str(data.get('used', 0)))
                
                if total > 0 or free > 0 or used > 0:
                    balances.append(BalanceInfo(
                        currency=currency,
                        total=total,
                        available=free,
                        frozen=used
                    ))
        return balances
