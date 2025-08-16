"""
Configuration management for the crypto trading framework
"""
import os
from typing import Optional, Dict, Any
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database configuration"""
    url: str = Field(default="sqlite+aiosqlite:///./trading.db")
    echo: bool = Field(default=False)


class ServerSettings(BaseModel):
    """Server configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)


class SecuritySettings(BaseModel):
    """Security configuration"""
    secret_key: str = Field(default="your-secret-key-change-this")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    webhook_secret: str = Field(default="your-webhook-secret")


class ExchangeConfig(BaseModel):
    """Individual exchange configuration"""
    api_key: str = ""
    secret_key: str = ""
    passphrase: Optional[str] = None
    sandbox: bool = True


class ExchangeSettings(BaseModel):
    """Exchange configuration"""
    binance: ExchangeConfig = ExchangeConfig()
    okx: ExchangeConfig = ExchangeConfig()
    gateio: ExchangeConfig = ExchangeConfig()
    rate_limits: Dict[str, int] = Field(default_factory=lambda: {
        "default": 10,
        "binance": 20,
        "okx": 20,
        "gateio": 10
    })


class TradingSettings(BaseModel):
    """Trading configuration"""
    max_positions_per_account: int = Field(default=10)
    default_leverage: int = Field(default=1)
    max_position_size: float = Field(default=0.1)  # 10% of account balance
    stop_loss_percentage: float = Field(default=0.05)  # 5%
    take_profit_percentage: float = Field(default=0.1)  # 10%


class WebhookSettings(BaseModel):
    """Webhook configuration"""
    timeout: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    verify_signature: bool = Field(default=True)


class LoggingSettings(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO")
    format: str = Field(default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}")
    file: str = Field(default="logs/trading.log")
    rotation: str = Field(default="100 MB")
    retention: str = Field(default="30 days")


class Settings(BaseSettings):
    """Main application settings"""
    
    # Basic app info
    app_name: str = Field(default="Crypto Trading Framework")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=True)
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    exchanges: ExchangeSettings = Field(default_factory=ExchangeSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    webhooks: WebhookSettings = Field(default_factory=WebhookSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, yaml_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML file with environment variable override"""
        config_data = {}
        
        # Load from YAML if exists
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    config_data.update(yaml_data)
        
        # Create settings instance (will also load from env vars)
        settings = cls(**config_data)
        
        # Override with environment variables for exchanges
        settings._load_exchange_env_vars()
        
        return settings
    
    def _load_exchange_env_vars(self):
        """Load exchange API keys from environment variables"""
        # Binance
        if os.getenv("BINANCE_API_KEY"):
            self.exchanges.binance.api_key = os.getenv("BINANCE_API_KEY", "")
        if os.getenv("BINANCE_SECRET_KEY"):
            self.exchanges.binance.secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        if os.getenv("BINANCE_SANDBOX"):
            self.exchanges.binance.sandbox = os.getenv("BINANCE_SANDBOX", "true").lower() == "true"
        
        # OKX
        if os.getenv("OKX_API_KEY"):
            self.exchanges.okx.api_key = os.getenv("OKX_API_KEY", "")
        if os.getenv("OKX_SECRET_KEY"):
            self.exchanges.okx.secret_key = os.getenv("OKX_SECRET_KEY", "")
        if os.getenv("OKX_PASSPHRASE"):
            self.exchanges.okx.passphrase = os.getenv("OKX_PASSPHRASE")
        if os.getenv("OKX_SANDBOX"):
            self.exchanges.okx.sandbox = os.getenv("OKX_SANDBOX", "true").lower() == "true"
        
        # Gate.io
        if os.getenv("GATEIO_API_KEY"):
            self.exchanges.gateio.api_key = os.getenv("GATEIO_API_KEY", "")
        if os.getenv("GATEIO_SECRET_KEY"):
            self.exchanges.gateio.secret_key = os.getenv("GATEIO_SECRET_KEY", "")
        if os.getenv("GATEIO_SANDBOX"):
            self.exchanges.gateio.sandbox = os.getenv("GATEIO_SANDBOX", "true").lower() == "true"
        
        # Override other settings from env
        if os.getenv("DATABASE_URL"):
            self.database.url = os.getenv("DATABASE_URL")
        if os.getenv("API_HOST"):
            self.server.host = os.getenv("API_HOST")
        if os.getenv("API_PORT"):
            self.server.port = int(os.getenv("API_PORT"))
        if os.getenv("SECRET_KEY"):
            self.security.secret_key = os.getenv("SECRET_KEY")
        if os.getenv("WEBHOOK_SECRET"):
            self.security.webhook_secret = os.getenv("WEBHOOK_SECRET")
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")


# Global settings instance
settings = Settings.load_from_yaml()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def reload_settings():
    """Reload settings from files and environment"""
    global settings
    settings = Settings.load_from_yaml()
    return settings
