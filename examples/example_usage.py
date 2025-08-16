#!/usr/bin/env python3
"""
示例：如何使用量化交易框架的API
"""
import asyncio
import aiohttp
import json
from decimal import Decimal

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


async def create_account_example():
    """创建交易账户示例"""
    async with aiohttp.ClientSession() as session:
        account_data = {
            "name": "测试币安账户",
            "exchange": "binance",
            "api_key": "your_binance_api_key",
            "secret_key": "your_binance_secret_key",
            "is_sandbox": True,
            "is_active": True
        }
        
        async with session.post(f"{BASE_URL}/accounts", json=account_data) as resp:
            if resp.status == 201:
                account = await resp.json()
                print(f"✅ 账户创建成功: {account['name']} (ID: {account['id']})")
                return account['id']
            else:
                error = await resp.text()
                print(f"❌ 账户创建失败: {error}")
                return None


async def get_account_info_example(account_id: int):
    """获取账户信息示例"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/accounts/{account_id}/info") as resp:
            if resp.status == 200:
                info = await resp.json()
                print(f"📊 账户信息:")
                print(f"   交易所: {info['exchange']}")
                print(f"   总权益: {info.get('total_equity', 'N/A')}")
                print(f"   余额数量: {len(info['balances'])}")
                print(f"   仓位数量: {len(info['positions'])}")
                return info
            else:
                error = await resp.text()
                print(f"❌ 获取账户信息失败: {error}")
                return None


async def create_order_example(account_id: int):
    """创建订单示例"""
    async with aiohttp.ClientSession() as session:
        order_data = {
            "account_id": account_id,
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "market",
            "amount": "0.001"
        }
        
        async with session.post(f"{BASE_URL}/trading/orders", json=order_data) as resp:
            if resp.status == 201:
                order = await resp.json()
                print(f"✅ 订单创建成功:")
                print(f"   订单ID: {order['id']}")
                print(f"   交易所订单ID: {order['exchange_order_id']}")
                print(f"   交易对: {order['symbol']}")
                print(f"   方向: {order['side']}")
                print(f"   数量: {order['amount']}")
                print(f"   状态: {order['status']}")
                return order['id']
            else:
                error = await resp.text()
                print(f"❌ 订单创建失败: {error}")
                return None


async def get_market_data_example(account_id: int, symbol: str = "BTCUSDT"):
    """获取市场数据示例"""
    async with aiohttp.ClientSession() as session:
        params = {"account_id": account_id}
        async with session.get(f"{BASE_URL}/trading/market/{symbol}", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"📈 {symbol} 市场数据:")
                print(f"   当前价格: {data['price']}")
                print(f"   买一价: {data.get('bid', 'N/A')}")
                print(f"   卖一价: {data.get('ask', 'N/A')}")
                print(f"   24h成交量: {data.get('volume', 'N/A')}")
                return data
            else:
                error = await resp.text()
                print(f"❌ 获取市场数据失败: {error}")
                return None


async def get_klines_example(account_id: int, symbol: str = "BTCUSDT"):
    """获取K线数据示例"""
    async with aiohttp.ClientSession() as session:
        params = {
            "account_id": account_id,
            "interval": "1h",
            "limit": 5
        }
        async with session.get(f"{BASE_URL}/trading/klines/{symbol}", params=params) as resp:
            if resp.status == 200:
                klines = await resp.json()
                print(f"📊 {symbol} K线数据 (最近5根1小时K线):")
                for kline in klines:
                    print(f"   {kline['open_time']}: O={kline['open_price']} H={kline['high_price']} L={kline['low_price']} C={kline['close_price']} V={kline['volume']}")
                return klines
            else:
                error = await resp.text()
                print(f"❌ 获取K线数据失败: {error}")
                return None


async def webhook_test_example():
    """Webhook测试示例"""
    async with aiohttp.ClientSession() as session:
        # 模拟开仓信号
        webhook_payload = {
            "action": "open",
            "account_id": 1,  # 假设账户ID为1
            "symbol": "BTCUSDT",
            "side": "buy",
            "amount": "0.001",
            "order_type": "market"
        }
        
        # 注意：实际使用时需要正确的签名
        headers = {
            "Content-Type": "application/json",
            # "X-Signature": "sha256=your_computed_signature"
        }
        
        async with session.post(f"{BASE_URL}/webhooks/open-position", 
                              json=webhook_payload, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Webhook开仓信号处理成功:")
                print(f"   订单ID: {result.get('order_id')}")
                print(f"   交易所订单ID: {result.get('exchange_order_id')}")
            else:
                error = await resp.text()
                print(f"❌ Webhook处理失败: {error}")


async def main():
    """主函数 - 运行所有示例"""
    print("🚀 量化交易框架 API 使用示例\n")
    
    try:
        # 1. 创建账户
        print("1. 创建交易账户")
        account_id = await create_account_example()
        if not account_id:
            print("无法继续，账户创建失败")
            return
        
        print("\n" + "="*50 + "\n")
        
        # 2. 获取账户信息
        print("2. 获取账户信息")
        await get_account_info_example(account_id)
        
        print("\n" + "="*50 + "\n")
        
        # 3. 获取市场数据
        print("3. 获取市场数据")
        await get_market_data_example(account_id)
        
        print("\n" + "="*50 + "\n")
        
        # 4. 获取K线数据
        print("4. 获取K线数据")
        await get_klines_example(account_id)
        
        print("\n" + "="*50 + "\n")
        
        # 5. 创建订单
        print("5. 创建交易订单")
        order_id = await create_order_example(account_id)
        
        print("\n" + "="*50 + "\n")
        
        # 6. Webhook测试
        print("6. Webhook功能测试")
        await webhook_test_example()
        
        print("\n✅ 所有示例执行完成!")
        
    except Exception as e:
        print(f"❌ 示例执行出错: {e}")


if __name__ == "__main__":
    print("请确保交易框架服务正在运行 (python start.py)")
    print("然后运行此示例: python examples/example_usage.py\n")
    
    # 运行示例
    asyncio.run(main())
