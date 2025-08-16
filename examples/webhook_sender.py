#!/usr/bin/env python3
"""
Webhook发送器示例 - 模拟TradingView或其他平台发送交易信号
"""
import asyncio
import aiohttp
import json
import hmac
import hashlib
from datetime import datetime


class WebhookSender:
    """Webhook信号发送器"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", 
                 webhook_secret: str = "your-webhook-secret"):
        self.base_url = base_url
        self.webhook_secret = webhook_secret
    
    def _generate_signature(self, payload: dict) -> str:
        """生成Webhook签名"""
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def send_webhook(self, endpoint: str, payload: dict) -> dict:
        """发送Webhook请求"""
        url = f"{self.base_url}/webhooks/{endpoint}"
        signature = self._generate_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = {
                    "status_code": resp.status,
                    "response": await resp.json() if resp.content_type == "application/json" else await resp.text()
                }
                return result
    
    async def send_open_signal(self, account_id: int, symbol: str, side: str, 
                              amount: str, order_type: str = "market", 
                              price: str = None) -> dict:
        """发送开仓信号"""
        payload = {
            "action": "open",
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "order_type": order_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "source": "webhook_sender_example",
                "strategy": "demo_strategy"
            }
        }
        
        if price:
            payload["price"] = price
        
        print(f"📤 发送开仓信号: {symbol} {side} {amount}")
        return await self.send_webhook("open-position", payload)
    
    async def send_close_signal(self, account_id: int, symbol: str, side: str,
                               amount: str = None) -> dict:
        """发送平仓信号"""
        payload = {
            "action": "close",
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "source": "webhook_sender_example",
                "strategy": "demo_strategy"
            }
        }
        
        if amount:
            payload["amount"] = amount
        
        print(f"📤 发送平仓信号: {symbol} {side}")
        return await self.send_webhook("close-position", payload)
    
    async def send_generic_trade_signal(self, action: str, account_id: int, 
                                       symbol: str, side: str, amount: str,
                                       order_type: str = "market") -> dict:
        """发送通用交易信号"""
        payload = {
            "action": action,
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "order_type": order_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "source": "webhook_sender_example",
                "strategy": "demo_strategy"
            }
        }
        
        print(f"📤 发送{action}信号: {symbol} {side} {amount}")
        return await self.send_webhook("trade", payload)


async def demo_trading_signals():
    """演示交易信号发送"""
    sender = WebhookSender()
    
    # 假设账户ID为1（需要先创建账户）
    account_id = 1
    symbol = "BTCUSDT"
    
    print("🤖 开始发送演示交易信号\n")
    
    try:
        # 1. 发送买入开仓信号
        print("1. 📈 发送买入开仓信号")
        result = await sender.send_open_signal(
            account_id=account_id,
            symbol=symbol,
            side="buy",
            amount="0.001",
            order_type="market"
        )
        print(f"   结果: {result['status_code']} - {result['response']}")
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 2. 发送限价买入信号
        print("\n2. 📊 发送限价买入信号")
        result = await sender.send_open_signal(
            account_id=account_id,
            symbol=symbol,
            side="buy",
            amount="0.001",
            order_type="limit",
            price="45000.0"
        )
        print(f"   结果: {result['status_code']} - {result['response']}")
        
        await asyncio.sleep(2)
        
        # 3. 发送平仓信号
        print("\n3. 📉 发送平仓信号")
        result = await sender.send_close_signal(
            account_id=account_id,
            symbol=symbol,
            side="sell"  # 平多仓
        )
        print(f"   结果: {result['status_code']} - {result['response']}")
        
        await asyncio.sleep(2)
        
        # 4. 发送通用交易信号
        print("\n4. 🔄 发送通用交易信号")
        result = await sender.send_generic_trade_signal(
            action="open",
            account_id=account_id,
            symbol="ETHUSDT",
            side="buy",
            amount="0.01"
        )
        print(f"   结果: {result['status_code']} - {result['response']}")
        
        print("\n✅ 演示信号发送完成!")
        
    except Exception as e:
        print(f"❌ 发送信号时出错: {e}")


async def simulate_tradingview_alerts():
    """模拟TradingView告警信号"""
    sender = WebhookSender()
    account_id = 1
    
    print("📺 模拟TradingView告警信号\n")
    
    # 模拟不同的交易策略信号
    strategies = [
        {
            "name": "MA交叉策略",
            "signals": [
                {"action": "open", "symbol": "BTCUSDT", "side": "buy", "amount": "0.001"},
                {"action": "close", "symbol": "BTCUSDT", "side": "sell"}
            ]
        },
        {
            "name": "RSI超买超卖策略", 
            "signals": [
                {"action": "open", "symbol": "ETHUSDT", "side": "sell", "amount": "0.01"},
                {"action": "close", "symbol": "ETHUSDT", "side": "buy"}
            ]
        }
    ]
    
    for strategy in strategies:
        print(f"🎯 执行策略: {strategy['name']}")
        
        for signal in strategy['signals']:
            result = await sender.send_generic_trade_signal(
                action=signal['action'],
                account_id=account_id,
                symbol=signal['symbol'],
                side=signal['side'],
                amount=signal['amount']
            )
            print(f"   信号: {signal} -> {result['status_code']}")
            await asyncio.sleep(1)
        
        print()


def main():
    """主函数"""
    print("Webhook发送器示例")
    print("=" * 50)
    print("1. demo - 演示基本交易信号")
    print("2. tradingview - 模拟TradingView信号")
    print("3. custom - 自定义信号")
    
    choice = input("\n请选择模式 (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(demo_trading_signals())
    elif choice == "2":
        asyncio.run(simulate_tradingview_alerts())
    elif choice == "3":
        # 自定义信号示例
        async def custom_signal():
            sender = WebhookSender()
            
            account_id = int(input("请输入账户ID: "))
            symbol = input("请输入交易对 (如 BTCUSDT): ").upper()
            action = input("请输入操作 (open/close): ").lower()
            side = input("请输入方向 (buy/sell): ").lower()
            amount = input("请输入数量: ")
            
            if action == "open":
                result = await sender.send_open_signal(account_id, symbol, side, amount)
            else:
                result = await sender.send_close_signal(account_id, symbol, side, amount)
            
            print(f"\n结果: {result}")
        
        asyncio.run(custom_signal())
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
