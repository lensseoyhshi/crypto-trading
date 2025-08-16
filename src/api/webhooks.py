"""
Webhook API endpoints for trading signals
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..core.models import WebhookPayload, OrderCreate, OrderType, OrderSide
from ..services.trading_service import TradingService
from ..utils.webhook_security import require_webhook_signature
from .dependencies import get_database, get_trading_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/open-position")
async def webhook_open_position(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Webhook endpoint for opening positions"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature (try both header names)
        signature = x_signature or x_webhook_signature
        require_webhook_signature(body, signature)
        
        # Parse payload
        try:
            payload_data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )
        
        # Validate payload
        try:
            webhook_payload = WebhookPayload(**payload_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        
        # Ensure it's an open action
        if webhook_payload.action.lower() != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint only accepts 'open' actions"
            )
        
        # Create order
        order_data = OrderCreate(
            account_id=webhook_payload.account_id,
            symbol=webhook_payload.symbol,
            side=webhook_payload.side,
            type=webhook_payload.order_type,
            amount=webhook_payload.amount,
            price=webhook_payload.price,
            stop_price=webhook_payload.stop_price
        )
        
        order = await trading_service.create_order(db, order_data)
        
        logger.info(f"Position opened via webhook: {order.id} - {order.symbol} {order.side} {order.amount}")
        
        return {
            "success": True,
            "message": "Position opened successfully",
            "order_id": order.id,
            "exchange_order_id": order.exchange_order_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook open position failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.post("/close-position")
async def webhook_close_position(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Webhook endpoint for closing positions"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature
        signature = x_signature or x_webhook_signature
        require_webhook_signature(body, signature)
        
        # Parse payload
        try:
            payload_data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )
        
        # Validate payload
        try:
            webhook_payload = WebhookPayload(**payload_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        
        # Ensure it's a close action
        if webhook_payload.action.lower() != "close":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint only accepts 'close' actions"
            )
        
        # Determine position side to close based on order side
        # If webhook says BUY to close, we're closing a SHORT position
        # If webhook says SELL to close, we're closing a LONG position
        from ..core.models import PositionSide
        if webhook_payload.side == OrderSide.BUY:
            position_side = PositionSide.SHORT
        else:
            position_side = PositionSide.LONG
        
        order = await trading_service.close_position(
            db=db,
            account_id=webhook_payload.account_id,
            symbol=webhook_payload.symbol,
            side=position_side,
            amount=webhook_payload.amount
        )
        
        logger.info(f"Position closed via webhook: {order.id} - {order.symbol} {position_side} {order.amount}")
        
        return {
            "success": True,
            "message": "Position closed successfully",
            "order_id": order.id,
            "exchange_order_id": order.exchange_order_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook close position failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.post("/trade")
async def webhook_trade(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_database),
    trading_service: TradingService = Depends(get_trading_service)
):
    """Generic webhook endpoint for trading actions"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature
        signature = x_signature or x_webhook_signature
        require_webhook_signature(body, signature)
        
        # Parse payload
        try:
            payload_data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )
        
        # Validate payload
        try:
            webhook_payload = WebhookPayload(**payload_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        
        action = webhook_payload.action.lower()
        
        if action == "open":
            # Create new order
            order_data = OrderCreate(
                account_id=webhook_payload.account_id,
                symbol=webhook_payload.symbol,
                side=webhook_payload.side,
                type=webhook_payload.order_type,
                amount=webhook_payload.amount,
                price=webhook_payload.price,
                stop_price=webhook_payload.stop_price
            )
            
            order = await trading_service.create_order(db, order_data)
            
            logger.info(f"Order created via webhook: {order.id} - {order.symbol} {order.side} {order.amount}")
            
            return {
                "success": True,
                "action": "open",
                "message": "Order created successfully",
                "order_id": order.id,
                "exchange_order_id": order.exchange_order_id
            }
            
        elif action == "close":
            # Close position
            from ..core.models import PositionSide
            
            # Determine position side to close
            if webhook_payload.side == OrderSide.BUY:
                position_side = PositionSide.SHORT
            else:
                position_side = PositionSide.LONG
            
            order = await trading_service.close_position(
                db=db,
                account_id=webhook_payload.account_id,
                symbol=webhook_payload.symbol,
                side=position_side,
                amount=webhook_payload.amount
            )
            
            logger.info(f"Position closed via webhook: {order.id} - {order.symbol} {position_side} {order.amount}")
            
            return {
                "success": True,
                "action": "close",
                "message": "Position closed successfully",
                "order_id": order.id,
                "exchange_order_id": order.exchange_order_id
            }
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {action}. Supported actions: 'open', 'close'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook trade failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.get("/test")
async def webhook_test():
    """Test webhook endpoint"""
    return {
        "success": True,
        "message": "Webhook service is running",
        "endpoints": {
            "open_position": "/webhooks/open-position",
            "close_position": "/webhooks/close-position",
            "generic_trade": "/webhooks/trade"
        },
        "payload_example": {
            "action": "open",  # or "close"
            "account_id": 1,
            "symbol": "BTCUSDT",
            "side": "buy",  # or "sell"
            "amount": "0.001",
            "order_type": "market",  # or "limit"
            "price": "50000.0",  # optional for limit orders
            "metadata": {}  # optional additional data
        }
    }
