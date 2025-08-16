#!/usr/bin/env python3
"""
简化的启动脚本 - 处理各种安装情况
"""
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查核心依赖是否安装"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'sqlalchemy',
        'pydantic',
        'loguru'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n或者:")
        print("pip install -r requirements.txt")
        print("pip install -r requirements-minimal.txt")
        return False
    
    print("✅ 核心依赖检查通过")
    return True

def setup_environment():
    """设置环境"""
    # 添加src到Python路径
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 创建必要的目录
    (Path(__file__).parent / "logs").mkdir(exist_ok=True)
    
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(src_path))

def main():
    """主函数"""
    print("🚀 量化交易框架启动脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 尝试导入和启动应用
    try:
        import uvicorn
        from src.main import app
        from src.core.config import get_settings
        
        settings = get_settings()
        
        print(f"📍 启动地址: http://{settings.server.host}:{settings.server.port}")
        print(f"📚 API文档: http://{settings.server.host}:{settings.server.port}/docs")
        print(f"🔧 配置文件: config.yaml")
        print("=" * 50)
        
        # 启动服务器
        uvicorn.run(
            app,
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload,
            log_level=settings.logging.level.lower()
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请检查依赖安装，参考 INSTALL.md 文件")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查配置文件和日志文件")
        sys.exit(1)

if __name__ == "__main__":
    main()
