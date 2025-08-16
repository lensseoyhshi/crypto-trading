"""
Core data models for the crypto trading framework
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ExchangeType(str, Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    OKX = "okx"
    GATEIO = "gateio"


class OrderSide(str, Enum):
    """Order side types"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status types"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionSide(str, Enum):
    """Position side types"""
    LONG = "long"
    SHORT = "short"


# Database Models
class Account(Base):
    """Account model for database"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    exchange = Column(SQLEnum(ExchangeType), nullable=False)
    api_key = Column(String(255), nullable=False)
    secret_key = Column(String(255), nullable=False)
    passphrase = Column(String(255), nullable=True)  # For OKX
    is_sandbox = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="account")
    positions = relationship("Position", back_populates="account")


class Order(Base):
    """Order model for database"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    exchange_order_id = Column(String(100), nullable=True)  # Exchange's order ID
    symbol = Column(String(50), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    type = Column(SQLEnum(OrderType), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=True)
    stop_price = Column(Numeric(20, 8), nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    filled_amount = Column(Numeric(20, 8), default=0)
    filled_price = Column(Numeric(20, 8), nullable=True)
    fee = Column(Numeric(20, 8), default=0)
    fee_currency = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    webhook_data = Column(Text, nullable=True)  # Store original webhook data

    # Relationships
    account = relationship("Account", back_populates="orders")


class Position(Base):
    """Position model for database"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(SQLEnum(PositionSide), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    mark_price = Column(Numeric(20, 8), nullable=True)
    unrealized_pnl = Column(Numeric(20, 8), default=0)
    realized_pnl = Column(Numeric(20, 8), default=0)
    leverage = Column(Integer, default=1)
    margin = Column(Numeric(20, 8), nullable=True)
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="positions")


# Pydantic Models for API
class AccountBase(BaseModel):
    """Base account schema"""
    name: str
    exchange: ExchangeType
    is_sandbox: bool = True
    is_active: bool = True


class AccountCreate(AccountBase):
    """Account creation schema"""
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None


class AccountUpdate(BaseModel):
    """Account update schema"""
    name: Optional[str] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """Account response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class OrderBase(BaseModel):
    """Base order schema"""
    symbol: str
    side: OrderSide
    type: OrderType
    amount: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None


class OrderCreate(OrderBase):
    """Order creation schema"""
    account_id: int


class OrderResponse(OrderBase):
    """Order response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    exchange_order_id: Optional[str] = None
    status: OrderStatus
    filled_amount: Decimal = Decimal('0')
    filled_price: Optional[Decimal] = None
    fee: Decimal = Decimal('0')
    fee_currency: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PositionResponse(BaseModel):
    """Position response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    symbol: str
    side: PositionSide
    size: Decimal
    entry_price: Decimal
    mark_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    leverage: int = 1
    margin: Optional[Decimal] = None
    is_open: bool = True
    created_at: datetime
    updated_at: datetime


class WebhookPayload(BaseModel):
    """Webhook payload schema"""
    action: str  # 'open' or 'close'
    account_id: int
    symbol: str
    side: OrderSide
    amount: Decimal
    price: Optional[Decimal] = None
    order_type: OrderType = OrderType.MARKET
    stop_price: Optional[Decimal] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MarketData(BaseModel):
    """Market data schema"""
    symbol: str
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    timestamp: datetime


class Kline(BaseModel):
    """Kline/Candlestick data schema"""
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    trade_count: Optional[int] = None


class BalanceInfo(BaseModel):
    """Account balance information"""
    currency: str
    total: Decimal
    available: Decimal
    frozen: Decimal = Decimal('0')
    
    
class AccountInfo(BaseModel):
    """Complete account information"""
    account_id: int
    exchange: ExchangeType
    balances: List[BalanceInfo]
    positions: List[PositionResponse]
    total_equity: Optional[Decimal] = None
    margin_ratio: Optional[Decimal] = None
