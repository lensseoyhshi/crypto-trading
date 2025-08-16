"""
基础测试用例
"""
import pytest
import asyncio
from decimal import Decimal

from src.core.models import ExchangeType, OrderSide, OrderType
from src.core.config import get_settings
from src.utils.encryption import EncryptionManager


def test_settings_loading():
    """测试配置加载"""
    settings = get_settings()
    assert settings.app_name == "Crypto Trading Framework"
    assert settings.app_version == "1.0.0"


def test_encryption_manager():
    """测试加密管理器"""
    encryption_manager = EncryptionManager("test-secret-key")
    
    # 测试加密解密
    original_data = "test-api-key-12345"
    encrypted_data = encryption_manager.encrypt(original_data)
    decrypted_data = encryption_manager.decrypt(encrypted_data)
    
    assert decrypted_data == original_data
    assert encrypted_data != original_data


def test_model_enums():
    """测试模型枚举"""
    # 测试交易所类型
    assert ExchangeType.BINANCE == "binance"
    assert ExchangeType.OKX == "okx"
    assert ExchangeType.GATEIO == "gateio"
    
    # 测试订单方向
    assert OrderSide.BUY == "buy"
    assert OrderSide.SELL == "sell"
    
    # 测试订单类型
    assert OrderType.MARKET == "market"
    assert OrderType.LIMIT == "limit"


def test_decimal_handling():
    """测试Decimal处理"""
    amount = Decimal("0.001")
    price = Decimal("50000.50")
    
    assert isinstance(amount, Decimal)
    assert isinstance(price, Decimal)
    assert amount * price == Decimal("50.00050")


@pytest.mark.asyncio
async def test_async_functionality():
    """测试异步功能"""
    async def dummy_async_function():
        await asyncio.sleep(0.01)
        return "success"
    
    result = await dummy_async_function()
    assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__])
