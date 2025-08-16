# 安装指南

## 问题解决

如果您遇到 `cryptography==41.0.8` 版本不存在的错误，这是因为指定的确切版本号不可用。以下是解决方案：

### 方案一：使用修复后的requirements.txt

我们已经修复了 `requirements.txt` 文件，移除了不兼容的版本号：

```bash
pip install -r requirements.txt
```

### 方案二：使用最小化依赖

如果上述方法仍有问题，请使用最小化依赖：

```bash
pip install -r requirements-minimal.txt
```

### 方案三：手动安装核心依赖

```bash
# 核心依赖
pip install fastapi uvicorn sqlalchemy aiosqlite
pip install cryptography pydantic python-dotenv loguru
pip install ccxt httpx

# 可选依赖（可以后续安装）
pip install pytest black isort flake8
```

### 方案四：使用虚拟环境

建议使用虚拟环境来避免版本冲突：

```bash
# 创建虚拟环境
python -m venv trading_env

# 激活虚拟环境
# macOS/Linux:
source trading_env/bin/activate
# Windows:
# trading_env\Scripts\activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

## 常见错误解决

### 1. cryptography安装失败

```bash
# 如果cryptography安装失败，尝试：
pip install --upgrade pip setuptools wheel
pip install cryptography

# 或者安装特定版本：
pip install "cryptography>=3.4.0,<42.0.0"
```

### 2. ccxt安装失败

```bash
# 如果ccxt安装失败：
pip install ccxt --no-cache-dir
```

### 3. SQLAlchemy版本问题

```bash
# 如果SQLAlchemy有版本问题：
pip install "sqlalchemy>=1.4.0,<3.0.0"
```

### 4. 完全重新安装

如果遇到严重的依赖冲突：

```bash
# 清理pip缓存
pip cache purge

# 卸载所有相关包
pip uninstall -y fastapi uvicorn sqlalchemy cryptography ccxt pydantic

# 重新安装
pip install -r requirements-minimal.txt
```

## 验证安装

安装完成后，可以运行以下命令验证：

```bash
python -c "import fastapi, sqlalchemy, ccxt, cryptography; print('所有核心依赖安装成功!')"
```

## 启动应用

```bash
# 方法1：使用启动脚本
python start.py

# 方法2：直接使用uvicorn
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 方法3：使用Python模块
cd src && python -m main
```

## 系统要求

- Python 3.8+
- 操作系统：Windows/macOS/Linux
- 内存：至少512MB
- 网络：需要访问交易所API

## 环境配置

1. 复制环境变量文件：
```bash
cp env.example .env
```

2. 编辑 `.env` 文件，填入您的API密钥

3. 确保logs目录存在：
```bash
mkdir -p logs
```

## Docker部署（推荐）

如果依赖安装仍有问题，推荐使用Docker：

```bash
# 构建镜像
docker build -t crypto-trading-framework .

# 运行容器
docker run -p 8000:8000 crypto-trading-framework
```

或使用docker-compose：

```bash
docker-compose up -d
```

## 技术支持

如果仍然遇到问题：

1. 检查Python版本：`python --version`
2. 更新pip：`pip install --upgrade pip`
3. 查看详细错误信息：`pip install -v -r requirements.txt`
4. 检查系统日志：查看 `logs/trading.log`

## 常用命令备忘

```bash
# 查看已安装的包
pip list

# 查看特定包信息
pip show cryptography

# 检查依赖冲突
pip check

# 生成当前环境的requirements
pip freeze > current-requirements.txt
```
