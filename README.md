# 量化交易框架 (Crypto Trading Framework)

一个专业的多交易所量化交易Python Web框架，支持币安(Binance)、OKX、Gate.io等主流交易所的API交互，具备完整的账户管理、订单管理、仓位管理和Webhook回调功能。

## 🚀 主要功能

### 交易所支持
- **币安 (Binance)** - 全球领先的加密货币交易所
- **OKX** - 专业的数字资产交易平台
- **Gate.io** - 多元化的区块链资产交易平台

### 核心功能
- ✅ **多账户管理** - 支持管理多个交易所账户的API密钥
- ✅ **订单管理** - 支持市价单、限价单、止损单等多种订单类型
- ✅ **仓位管理** - 实时查看和管理交易仓位
- ✅ **K线数据** - 获取各时间周期的K线/蜡烛图数据
- ✅ **行情数据** - 实时获取市场行情和价格信息
- ✅ **Webhook回调** - 支持开仓、平仓的Webhook信号接收
- ✅ **安全加密** - API密钥安全加密存储
- ✅ **日志监控** - 完整的日志记录和监控

### 技术特点
- 🔧 **FastAPI** - 现代化的异步Web框架
- 🗄️ **SQLAlchemy** - 强大的ORM数据库管理
- 🔒 **加密安全** - Fernet加密保护敏感数据
- 📊 **CCXT集成** - 统一的交易所API接口
- 🐳 **异步处理** - 高性能异步操作
- 📝 **完整文档** - 自动生成的API文档

## 📦 安装与配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd crypto-trading-framework
```

### 2. 安装依赖

**方法一：标准安装**
```bash
pip install -r requirements.txt
```

**方法二：如果遇到版本冲突，使用最小化依赖**
```bash
pip install -r requirements-minimal.txt
```

**方法三：手动安装核心依赖**
```bash
pip install fastapi uvicorn sqlalchemy aiosqlite cryptography pydantic python-dotenv loguru ccxt httpx
```

**推荐：使用虚拟环境**
```bash
python -m venv trading_env
source trading_env/bin/activate  # Linux/macOS
# 或 trading_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

⚠️ **如果遇到cryptography安装错误**，请参考 [INSTALL.md](INSTALL.md) 文件中的详细解决方案。

### 3. 配置环境变量
复制环境变量模板并配置：
```bash
cp env.example .env
```

编辑 `.env` 文件，添加你的交易所API密钥：
```env
# 币安配置
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_SANDBOX=true

# OKX配置
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase
OKX_SANDBOX=true

# Gate.io配置
GATEIO_API_KEY=your_gateio_api_key
GATEIO_SECRET_KEY=your_gateio_secret_key
GATEIO_SANDBOX=true

# 安全配置
SECRET_KEY=your-super-secret-key-change-this
WEBHOOK_SECRET=your-webhook-secret-for-signature-verification
```

### 4. 启动服务

**方法一：使用简化启动脚本（推荐）**
```bash
python run.py
```

**方法二：使用原始启动脚本**
```bash
python start.py
```

**方法三：直接使用uvicorn**
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**服务启动后访问：**
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 主页：http://localhost:8000

## 🔧 API 使用指南

### 账户管理

#### 创建交易账户
```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的币安账户",
    "exchange": "binance",
    "api_key": "your_api_key",
    "secret_key": "your_secret_key",
    "is_sandbox": true
  }'
```

#### 获取账户信息
```bash
curl -X GET "http://localhost:8000/api/v1/accounts/1/info"
```

### 交易操作

#### 创建订单（开仓）
```bash
curl -X POST "http://localhost:8000/api/v1/trading/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "market",
    "amount": "0.001"
  }'
```

#### 平仓
```bash
curl -X POST "http://localhost:8000/api/v1/trading/positions/close" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "symbol": "BTCUSDT",
    "side": "long"
  }'
```

#### 获取K线数据
```bash
curl -X GET "http://localhost:8000/api/v1/trading/klines/BTCUSDT?account_id=1&interval=1h&limit=100"
```

### Webhook 回调

#### 开仓信号
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/open-position" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=your_signature" \
  -d '{
    "action": "open",
    "account_id": 1,
    "symbol": "BTCUSDT",
    "side": "buy",
    "amount": "0.001",
    "order_type": "market"
  }'
```

#### 平仓信号
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/close-position" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=your_signature" \
  -d '{
    "action": "close",
    "account_id": 1,
    "symbol": "BTCUSDT",
    "side": "sell"
  }'
```

## 📋 Webhook 载荷格式

### 标准Webhook载荷
```json
{
  "action": "open",          // "open" 或 "close"
  "account_id": 1,           // 账户ID
  "symbol": "BTCUSDT",       // 交易对
  "side": "buy",             // "buy" 或 "sell"
  "amount": "0.001",         // 交易数量
  "order_type": "market",    // "market", "limit", "stop", "stop_limit"
  "price": "50000.0",        // 价格（限价单需要）
  "stop_price": "49000.0",   // 止损价格（止损单需要）
  "timestamp": "2024-01-01T00:00:00Z",  // 时间戳（可选）
  "metadata": {              // 额外元数据（可选）
    "source": "tradingview",
    "strategy": "ma_cross"
  }
}
```

### Webhook签名验证
为了安全，建议启用Webhook签名验证：

1. 设置环境变量 `WEBHOOK_SECRET`
2. 使用HMAC-SHA256计算签名
3. 在HTTP头中包含签名：`X-Signature: sha256=computed_signature`

Python签名生成示例：
```python
import hmac
import hashlib
import json

def generate_signature(payload, secret):
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

## 🗄️ 数据库结构

### 账户表 (accounts)
- 存储交易所账户信息和加密的API密钥
- 支持多交易所、多账户管理

### 订单表 (orders)
- 记录所有交易订单的详细信息
- 包含订单状态、成交信息、手续费等

### 仓位表 (positions)
- 跟踪当前持有的交易仓位
- 包含盈亏信息、保证金等

## 🔒 安全建议

1. **API密钥安全**
   - 使用只读或交易权限的API密钥
   - 定期轮换API密钥
   - 在生产环境中使用环境变量

2. **Webhook安全**
   - 启用签名验证
   - 使用HTTPS传输
   - 设置强密码的webhook密钥

3. **服务器安全**
   - 使用防火墙限制访问
   - 定期更新依赖包
   - 启用日志监控

## 📊 监控与日志

系统提供完整的日志记录：
- 交易操作日志
- API调用日志
- 错误和异常日志
- 性能监控日志

日志文件位置：`logs/trading.log`

## 🚨 风险提示

1. **测试环境**：建议先在沙盒环境中充分测试
2. **资金管理**：设置合理的仓位大小和风险控制
3. **监控系统**：建立实时监控和告警机制
4. **备份策略**：定期备份重要数据和配置

## 🤝 贡献指南

欢迎提交问题和改进建议：

1. Fork 项目
2. 创建功能分支
3. 提交代码变更
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

如有问题或建议，请：
- 提交 GitHub Issue
- 查看 API 文档：http://localhost:8000/docs
- 检查日志文件：`logs/trading.log`

---

**免责声明**：本框架仅供学习和研究使用。加密货币交易存在高风险，请谨慎操作并自行承担风险。
