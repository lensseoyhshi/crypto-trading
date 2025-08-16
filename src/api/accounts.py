"""
Account management API endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import AccountCreate, AccountUpdate, AccountResponse, AccountInfo
from ..services.account_service import AccountService
from .dependencies import get_database, get_account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Create a new trading account"""
    try:
        return await account_service.create_account(db, account_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create account: {str(e)}"
        )


@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Get list of trading accounts"""
    try:
        return await account_service.get_accounts(db, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accounts: {str(e)}"
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Get account by ID"""
    try:
        account = await account_service.get_account(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account: {str(e)}"
        )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Update account"""
    try:
        account = await account_service.update_account(db, account_id, account_data)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update account: {str(e)}"
        )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Delete account"""
    try:
        success = await account_service.delete_account(db, account_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.get("/{account_id}/info", response_model=AccountInfo)
async def get_account_info(
    account_id: int,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Get account information from exchange"""
    try:
        account_info = await account_service.get_account_info(db, account_id)
        if not account_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or inactive"
            )
        return account_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account info: {str(e)}"
        )


@router.post("/{account_id}/test", response_model=dict)
async def test_account_connection(
    account_id: int,
    db: AsyncSession = Depends(get_database),
    account_service: AccountService = Depends(get_account_service)
):
    """Test account connection to exchange"""
    try:
        account = await account_service.get_account(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Get the Account model for testing
        from ..core.models import Account
        from sqlalchemy.future import select
        
        result = await db.execute(select(Account).where(Account.id == account_id))
        account_model = result.scalar_one_or_none()
        
        if not account_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        success = await account_service.test_account_connection(account_model)
        return {"success": success, "message": "Connection successful" if success else "Connection failed"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )
