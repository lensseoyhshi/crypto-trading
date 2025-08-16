"""
Trading service for managing orders and positions
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from loguru import logger

from ..core.models import (
    Account, Order, Position, OrderCreate, OrderResponse, PositionResponse,
    OrderSide, OrderType, OrderStatus, PositionSide, MarketData, Kline
)
from .account_service import AccountService


class TradingService:
    """Service for managing trading operations"""
    
    def __init__(self, account_service: AccountService):
        self.account_service = account_service
    
    async def create_order(self, db: AsyncSession, order_data: OrderCreate) -> OrderResponse:
        """Create a new trading order"""
        try:
            # Get account
            result = await db.execute(
                select(Account).where(
                    Account.id == order_data.account_id,
                    Account.is_active == True
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError(f"Account {order_data.account_id} not found or inactive")
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(account)
            
            # Create order on exchange
            exchange_order = await exchange.create_order(
                symbol=order_data.symbol,
                side=order_data.side,
                order_type=order_data.type,
                amount=order_data.amount,
                price=order_data.price,
                stop_price=order_data.stop_price
            )
            
            # Save order to database
            order = Order(
                account_id=account.id,
                exchange_order_id=exchange_order.exchange_order_id,
                symbol=order_data.symbol,
                side=order_data.side,
                type=order_data.type,
                amount=order_data.amount,
                price=order_data.price,
                stop_price=order_data.stop_price,
                status=exchange_order.status,
                filled_amount=exchange_order.filled_amount,
                filled_price=exchange_order.filled_price,
                fee=exchange_order.fee,
                fee_currency=exchange_order.fee_currency
            )
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
            
            logger.info(f"Order created: {order.id} for account {account.name}")
            return OrderResponse.model_validate(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create order: {e}")
            raise
    
    async def cancel_order(self, db: AsyncSession, order_id: int) -> bool:
        """Cancel an existing order"""
        try:
            # Get order with account
            result = await db.execute(
                select(Order)
                .options(selectinload(Order.account))
                .where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                raise ValueError(f"Cannot cancel order with status {order.status}")
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(order.account)
            
            # Cancel order on exchange
            success = await exchange.cancel_order(order.exchange_order_id, order.symbol)
            
            if success:
                order.status = OrderStatus.CANCELLED
                await db.commit()
                logger.info(f"Order cancelled: {order.id}")
            
            return success
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def get_order(self, db: AsyncSession, order_id: int) -> Optional[OrderResponse]:
        """Get order by ID"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if order:
                return OrderResponse.model_validate(order)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise
    
    async def get_orders(self, db: AsyncSession, account_id: Optional[int] = None,
                        symbol: Optional[str] = None, status: Optional[OrderStatus] = None,
                        skip: int = 0, limit: int = 100) -> List[OrderResponse]:
        """Get list of orders with filters"""
        try:
            query = select(Order)
            
            if account_id:
                query = query.where(Order.account_id == account_id)
            if symbol:
                query = query.where(Order.symbol == symbol)
            if status:
                query = query.where(Order.status == status)
            
            query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
            
            result = await db.execute(query)
            orders = result.scalars().all()
            
            return [OrderResponse.model_validate(order) for order in orders]
            
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    async def get_positions(self, db: AsyncSession, account_id: Optional[int] = None,
                          symbol: Optional[str] = None, skip: int = 0, 
                          limit: int = 100) -> List[PositionResponse]:
        """Get list of positions with filters"""
        try:
            query = select(Position).where(Position.is_open == True)
            
            if account_id:
                query = query.where(Position.account_id == account_id)
            if symbol:
                query = query.where(Position.symbol == symbol)
            
            query = query.offset(skip).limit(limit).order_by(Position.created_at.desc())
            
            result = await db.execute(query)
            positions = result.scalars().all()
            
            return [PositionResponse.model_validate(position) for position in positions]
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    async def close_position(self, db: AsyncSession, account_id: int, symbol: str,
                           side: PositionSide, amount: Optional[Decimal] = None) -> OrderResponse:
        """Close a position"""
        try:
            # Get account
            result = await db.execute(
                select(Account).where(
                    Account.id == account_id,
                    Account.is_active == True
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError(f"Account {account_id} not found or inactive")
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(account)
            
            # Close position on exchange
            close_order = await exchange.close_position(symbol, side, amount)
            
            # Save order to database
            order = Order(
                account_id=account.id,
                exchange_order_id=close_order.exchange_order_id,
                symbol=symbol,
                side=OrderSide.SELL if side == PositionSide.LONG else OrderSide.BUY,
                type=OrderType.MARKET,
                amount=close_order.amount,
                status=close_order.status,
                filled_amount=close_order.filled_amount,
                filled_price=close_order.filled_price,
                fee=close_order.fee,
                fee_currency=close_order.fee_currency
            )
            
            db.add(order)
            
            # Update position status if fully closed
            if not amount or amount == close_order.filled_amount:
                position_result = await db.execute(
                    select(Position).where(
                        Position.account_id == account_id,
                        Position.symbol == symbol,
                        Position.side == side,
                        Position.is_open == True
                    )
                )
                position = position_result.scalar_one_or_none()
                if position:
                    position.is_open = False
            
            await db.commit()
            await db.refresh(order)
            
            logger.info(f"Position closed: {symbol} {side} for account {account.name}")
            return OrderResponse.model_validate(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to close position: {e}")
            raise
    
    async def get_market_data(self, db: AsyncSession, account_id: int, symbol: str) -> MarketData:
        """Get market data for symbol"""
        try:
            # Get account
            result = await db.execute(
                select(Account).where(
                    Account.id == account_id,
                    Account.is_active == True
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError(f"Account {account_id} not found or inactive")
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(account)
            
            # Get market data
            return await exchange.get_ticker(symbol)
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            raise
    
    async def get_klines(self, db: AsyncSession, account_id: int, symbol: str,
                        interval: str, limit: int = 100,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Kline]:
        """Get kline data for symbol"""
        try:
            # Get account
            result = await db.execute(
                select(Account).where(
                    Account.id == account_id,
                    Account.is_active == True
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError(f"Account {account_id} not found or inactive")
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(account)
            
            # Get kline data
            return await exchange.get_klines(symbol, interval, limit, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    async def update_order_status(self, db: AsyncSession, order_id: int) -> Optional[OrderResponse]:
        """Update order status from exchange"""
        try:
            # Get order with account
            result = await db.execute(
                select(Order)
                .options(selectinload(Order.account))
                .where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return None
            
            # Skip if already filled or cancelled
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                return OrderResponse.model_validate(order)
            
            # Get exchange client
            exchange = await self.account_service.get_exchange_client(order.account)
            
            # Get updated order from exchange
            exchange_order = await exchange.get_order(order.exchange_order_id, order.symbol)
            
            # Update local order
            order.status = exchange_order.status
            order.filled_amount = exchange_order.filled_amount
            order.filled_price = exchange_order.filled_price
            order.fee = exchange_order.fee
            order.fee_currency = exchange_order.fee_currency
            
            await db.commit()
            
            return OrderResponse.model_validate(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update order status {order_id}: {e}")
            raise
