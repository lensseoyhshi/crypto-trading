"""
Account management service
"""
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from loguru import logger
# from cryptography.fernet import Fernet  # 已在EncryptionManager中处理

from ..core.models import (
    Account, AccountCreate, AccountUpdate, AccountResponse,
    ExchangeType, AccountInfo
)
from ..exchanges.factory import ExchangeFactory
from ..utils.encryption import EncryptionManager


class AccountService:
    """Service for managing trading accounts"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
    
    async def create_account(self, db: AsyncSession, account_data: AccountCreate) -> AccountResponse:
        """Create a new trading account"""
        try:
            # Encrypt sensitive data
            encrypted_api_key = self.encryption_manager.encrypt(account_data.api_key)
            encrypted_secret_key = self.encryption_manager.encrypt(account_data.secret_key)
            encrypted_passphrase = None
            if account_data.passphrase:
                encrypted_passphrase = self.encryption_manager.encrypt(account_data.passphrase)
            
            # Create account record
            account = Account(
                name=account_data.name,
                exchange=account_data.exchange,
                api_key=encrypted_api_key,
                secret_key=encrypted_secret_key,
                passphrase=encrypted_passphrase,
                is_sandbox=account_data.is_sandbox,
                is_active=account_data.is_active
            )
            
            db.add(account)
            await db.commit()
            await db.refresh(account)
            
            # Test the connection
            await self.test_account_connection(account)
            
            logger.info(f"Account created: {account.name} ({account.exchange})")
            return AccountResponse.model_validate(account)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create account: {e}")
            raise
    
    async def get_account(self, db: AsyncSession, account_id: int) -> Optional[AccountResponse]:
        """Get account by ID"""
        try:
            result = await db.execute(
                select(Account).where(Account.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account:
                return AccountResponse.model_validate(account)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get account {account_id}: {e}")
            raise
    
    async def get_accounts(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AccountResponse]:
        """Get list of accounts"""
        try:
            result = await db.execute(
                select(Account)
                .offset(skip)
                .limit(limit)
                .order_by(Account.created_at.desc())
            )
            accounts = result.scalars().all()
            
            return [AccountResponse.model_validate(account) for account in accounts]
            
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            raise
    
    async def update_account(self, db: AsyncSession, account_id: int, 
                           account_data: AccountUpdate) -> Optional[AccountResponse]:
        """Update account"""
        try:
            result = await db.execute(
                select(Account).where(Account.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                return None
            
            # Update fields
            if account_data.name is not None:
                account.name = account_data.name
            if account_data.is_active is not None:
                account.is_active = account_data.is_active
            
            await db.commit()
            await db.refresh(account)
            
            logger.info(f"Account updated: {account.name}")
            return AccountResponse.model_validate(account)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update account {account_id}: {e}")
            raise
    
    async def delete_account(self, db: AsyncSession, account_id: int) -> bool:
        """Delete account"""
        try:
            result = await db.execute(
                select(Account).where(Account.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                return False
            
            await db.delete(account)
            await db.commit()
            
            logger.info(f"Account deleted: {account.name}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete account {account_id}: {e}")
            raise
    
    async def get_exchange_client(self, account: Account):
        """Get exchange client for account"""
        try:
            # Decrypt credentials
            api_key = self.encryption_manager.decrypt(account.api_key)
            secret_key = self.encryption_manager.decrypt(account.secret_key)
            passphrase = None
            if account.passphrase:
                passphrase = self.encryption_manager.decrypt(account.passphrase)
            
            # Create exchange client
            exchange = ExchangeFactory.create_exchange(
                exchange_type=account.exchange,
                api_key=api_key,
                secret_key=secret_key,
                passphrase=passphrase,
                sandbox=account.is_sandbox
            )
            
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to create exchange client for account {account.id}: {e}")
            raise
    
    async def test_account_connection(self, account: Account) -> bool:
        """Test account connection to exchange"""
        try:
            exchange = await self.get_exchange_client(account)
            return await exchange.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for account {account.id}: {e}")
            return False
    
    async def get_account_info(self, db: AsyncSession, account_id: int) -> Optional[AccountInfo]:
        """Get account information from exchange"""
        try:
            result = await db.execute(
                select(Account).where(Account.id == account_id, Account.is_active == True)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                return None
            
            exchange = await self.get_exchange_client(account)
            account_info = await exchange.get_account_info()
            account_info.account_id = account_id
            
            return account_info
            
        except Exception as e:
            logger.error(f"Failed to get account info for {account_id}: {e}")
            raise
    
    async def get_active_accounts_by_exchange(self, db: AsyncSession, 
                                            exchange_type: ExchangeType) -> List[Account]:
        """Get active accounts for specific exchange"""
        try:
            result = await db.execute(
                select(Account).where(
                    Account.exchange == exchange_type,
                    Account.is_active == True
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active accounts for {exchange_type}: {e}")
            raise
