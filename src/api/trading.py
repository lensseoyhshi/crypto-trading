"""
Trading API endpoints
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import (
    OrderCreate, OrderResponse, PositionResponse, OrderStatus, PositionSide,
    MarketData, Kline
)
from ..services.trading_service import TradingService
from .dependencies import get_database, get_trading_service

router = APIRouter(prefix="/trading", tags=["trading"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Create a new trading order"""
    try:
        return await trading_service.create_order(db, order_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get list of trading orders"""
    try:
        return await trading_service.get_orders(db, account_id, symbol, status, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get order by ID"""
    try:
        order = await trading_service.get_order(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}"
        )


@router.delete("/orders/{order_id}", response_model=dict)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Cancel an order"""
    try:
        success = await trading_service.cancel_order(db, order_id)
        return {"success": success, "message": "Order cancelled successfully" if success else "Failed to cancel order"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get list of positions"""
    try:
        return await trading_service.get_positions(db, account_id, symbol, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.post("/positions/close", response_model=OrderResponse)
async def close_position(
    account_id: int,
    symbol: str,
    side: PositionSide,
    amount: Optional[Decimal] = None,
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Close a position"""
    try:
        return await trading_service.close_position(db, account_id, symbol, side, amount)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to close position: {str(e)}"
        )


@router.get("/market/{symbol}", response_model=MarketData)
async def get_market_data(
    symbol: str,
    account_id: int = Query(..., description="Account ID to use for exchange access"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get market data for a symbol"""
    try:
        return await trading_service.get_market_data(db, account_id, symbol)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market data: {str(e)}"
        )


@router.get("/klines/{symbol}", response_model=List[Kline])
async def get_klines(
    symbol: str,
    account_id: int = Query(..., description="Account ID to use for exchange access"),
    interval: str = Query("1h", description="Kline interval (1m, 5m, 1h, 1d, etc.)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of klines to return"),
    start_time: Optional[datetime] = Query(None, description="Start time for klines"),
    end_time: Optional[datetime] = Query(None, description="End time for klines"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get kline/candlestick data for a symbol"""
    try:
        return await trading_service.get_klines(db, account_id, symbol, interval, limit, start_time, end_time)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get klines: {str(e)}"
        )


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Update order status from exchange"""
    try:
        order = await trading_service.update_order_status(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order status: {str(e)}"
        )
