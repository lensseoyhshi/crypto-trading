#!/usr/bin/env python3
"""
Startup script for the crypto trading framework
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from src.core.config import get_settings
from src.main import app


def main():
    """Main startup function"""
    settings = get_settings()
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 Server: http://{settings.server.host}:{settings.server.port}")
    print(f"📚 API Docs: http://{settings.server.host}:{settings.server.port}/docs")
    print(f"🔄 Reload: {settings.server.reload}")
    print(f"🐛 Debug: {settings.debug}")
    
    # Run the server
    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.logging.level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
