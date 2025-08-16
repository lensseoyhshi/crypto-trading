"""
Gate.io exchange implementation
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

import ccxt
from loguru import logger

from ..core.models import (
    ExchangeType, OrderSide, OrderType, OrderStatus, PositionSide,
    OrderResponse, PositionResponse, MarketData, Kline, BalanceInfo, AccountInfo
)
from .base import BaseExchange


class GateIOExchange(BaseExchange):
    """Gate.io exchange implementation"""
    
    def _initialize_exchange(self):
        """Initialize Gate.io exchange client"""
        try:
            self.exchange = ccxt.gateio({
                'apiKey': self.api_key,
                'secret': self.secret_key,
                'sandbox': self.sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',  # Use perpetual swaps by default
                }
            })
            logger.info(f"Gate.io exchange initialized (sandbox: {self.sandbox})")
        except Exception as e:
            logger.error(f"Failed to initialize Gate.io exchange: {e}")
            raise
    
    @property
    def exchange_type(self) -> ExchangeType:
        return ExchangeType.GATEIO
    
    async def get_account_info(self) -> AccountInfo:
        """Get Gate.io account information"""
        try:
            # Get balance
            balance = await self.exchange.fetch_balance()
            balances = self._parse_ccxt_balance(balance)
            
            # Get positions
            positions = await self.get_positions()
            
            # Calculate total equity
            total_equity = sum(b.total for b in balances if b.currency == 'USDT')
            
            return AccountInfo(
                account_id=0,
                exchange=self.exchange_type,
                balances=balances,
                positions=positions,
                total_equity=total_equity
            )
        except Exception as e:
            logger.error(f"Failed to get Gate.io account info: {e}")
            raise
    
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                          amount: Decimal, price: Optional[Decimal] = None,
                          stop_price: Optional[Decimal] = None,
                          **kwargs) -> OrderResponse:
        """Create order on Gate.io"""
        try:
            symbol = self._normalize_symbol(symbol)
            
            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'side': side.value,
                'type': order_type.value,
                'amount': float(amount),
            }
            
            if price:
                order_params['price'] = float(price)
            
            if stop_price:
                order_params['stopPrice'] = float(stop_price)
            
            # Add reduce-only for position closing
            if kwargs.get('reduce_only'):
                order_params['reduceOnly'] = True
            
            # Create order
            order = await self.exchange.create_order(**order_params)
            
            # Parse and return order response
            order_response = self._parse_ccxt_order(order)
            logger.info(f"Gate.io order created: {order_response.exchange_order_id}")
            
            return order_response
            
        except Exception as e:
            logger.error(f"Failed to create Gate.io order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel order on Gate.io"""
        try:
            symbol = self._normalize_symbol(symbol)
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Gate.io order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Gate.io order {order_id}: {e}")
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order details from Gate.io"""
        try:
            symbol = self._normalize_symbol(symbol)
            order = await self.exchange.fetch_order(order_id, symbol)
            return self._parse_ccxt_order(order)
        except Exception as e:
            logger.error(f"Failed to get Gate.io order {order_id}: {e}")
            raise
    
    async def get_orders(self, symbol: Optional[str] = None,
                        status: Optional[OrderStatus] = None,
                        limit: int = 100) -> List[OrderResponse]:
        """Get orders from Gate.io"""
        try:
            if symbol:
                symbol = self._normalize_symbol(symbol)
                orders = await self.exchange.fetch_orders(symbol, limit=limit)
            else:
                orders = await self.exchange.fetch_orders(limit=limit)
            
            order_responses = [self._parse_ccxt_order(order) for order in orders]
            
            # Filter by status if specified
            if status:
                order_responses = [o for o in order_responses if o.status == status]
            
            return order_responses
        except Exception as e:
            logger.error(f"Failed to get Gate.io orders: {e}")
            raise
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[PositionResponse]:
        """Get positions from Gate.io"""
        try:
            positions_data = await self.exchange.fetch_positions(symbol)
            positions = []
            
            for pos_data in positions_data:
                if float(pos_data.get('size', 0)) == 0:
                    continue  # Skip empty positions
                
                position = PositionResponse(
                    id=0,
                    account_id=0,
                    symbol=pos_data.get('symbol', ''),
                    side=PositionSide.LONG if pos_data.get('side') == 'long' else PositionSide.SHORT,
                    size=Decimal(str(pos_data.get('size', 0))),
                    entry_price=Decimal(str(pos_data.get('entryPrice', 0))),
                    mark_price=Decimal(str(pos_data.get('markPrice', 0))),
                    unrealized_pnl=Decimal(str(pos_data.get('unrealizedPnl', 0))),
                    leverage=int(pos_data.get('leverage', 1)),
                    margin=Decimal(str(pos_data.get('initialMargin', 0))),
                    is_open=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                positions.append(position)
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get Gate.io positions: {e}")
            raise
    
    async def close_position(self, symbol: str, side: PositionSide,
                           amount: Optional[Decimal] = None) -> OrderResponse:
        """Close position on Gate.io"""
        try:
            # Get current position to determine amount if not specified
            positions = await self.get_positions(symbol)
            position = next((p for p in positions if p.side == side), None)
            
            if not position:
                raise ValueError(f"No {side} position found for {symbol}")
            
            if not amount:
                amount = abs(position.size)
            
            # Create opposite order to close position
            close_side = OrderSide.SELL if side == PositionSide.LONG else OrderSide.BUY
            
            return await self.create_order(
                symbol=symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                amount=amount,
                reduce_only=True
            )
        except Exception as e:
            logger.error(f"Failed to close Gate.io position: {e}")
            raise
    
    async def get_ticker(self, symbol: str) -> MarketData:
        """Get ticker data from Gate.io"""
        try:
            symbol = self._normalize_symbol(symbol)
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return MarketData(
                symbol=symbol,
                price=Decimal(str(ticker.get('last', 0))),
                bid=Decimal(str(ticker.get('bid', 0))),
                ask=Decimal(str(ticker.get('ask', 0))),
                volume=Decimal(str(ticker.get('baseVolume', 0))),
                timestamp=datetime.fromtimestamp(ticker.get('timestamp', 0) / 1000)
            )
        except Exception as e:
            logger.error(f"Failed to get Gate.io ticker for {symbol}: {e}")
            raise
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Kline]:
        """Get kline data from Gate.io"""
        try:
            symbol = self._normalize_symbol(symbol)
            
            # Convert interval to Gate.io format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
                '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
            }
            gateio_interval = interval_map.get(interval, '1h')
            
            # Prepare parameters
            params = {}
            if start_time:
                params['since'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['until'] = int(end_time.timestamp() * 1000)
            
            # Fetch OHLCV data
            ohlcv = await self.exchange.fetch_ohlcv(symbol, gateio_interval, limit=limit, **params)
            
            klines = []
            for data in ohlcv:
                kline = Kline(
                    symbol=symbol,
                    interval=interval,
                    open_time=datetime.fromtimestamp(data[0] / 1000),
                    close_time=datetime.fromtimestamp(data[0] / 1000),
                    open_price=Decimal(str(data[1])),
                    high_price=Decimal(str(data[2])),
                    low_price=Decimal(str(data[3])),
                    close_price=Decimal(str(data[4])),
                    volume=Decimal(str(data[5]))
                )
                klines.append(kline)
            
            return klines
        except Exception as e:
            logger.error(f"Failed to get Gate.io klines for {symbol}: {e}")
            raise
