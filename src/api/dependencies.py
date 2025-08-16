"""
API dependencies
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.account_service import AccountService
from ..services.trading_service import TradingService
from ..utils.encryption import get_encryption_manager


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency"""
    async for db in get_db():
        yield db


def get_account_service() -> AccountService:
    """Account service dependency"""
    encryption_manager = get_encryption_manager()
    return AccountService(encryption_manager)


def get_trading_service() -> TradingService:
    """Trading service dependency"""
    account_service = get_account_service()
    return TradingService(account_service)
