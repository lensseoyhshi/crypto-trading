"""
Database configuration and session management
"""
import os
from typing import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from .config import get_settings
from .models import Base


class Database:
    """Database manager class"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.async_session = None
        
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create database directory if using SQLite
            if "sqlite" in self.settings.database.url:
                db_path = self.settings.database.url.split("///")[-1]
                db_dir = Path(db_path).parent
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create async engine
            self.engine = create_async_engine(
                self.settings.database.url,
                echo=self.settings.database.echo,
                future=True
            )
            
            # Create session factory
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info(f"Database initialized successfully: {self.settings.database.url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if not self.async_session:
            await self.initialize()
            
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()


# Global database instance
database = Database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async for session in database.get_session():
        yield session


async def init_db():
    """Initialize database"""
    await database.initialize()


async def close_db():
    """Close database"""
    await database.close()
