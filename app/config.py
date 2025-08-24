import os
from typing import Dict, Any

ENV = os.getenv("ENVIRONMENT", "development").lower()

config: Dict[str, Any] = {
    "database_url": "sqlite+aiosqlite:///./beacon.db",
    "database_echo": False,
    "database_pool_size": 10,
    "database_max_overflow": 20,
    "database_pool_pre_ping": True,
    
    "redis_url": "redis://localhost:6379",
    "cache_ttl": 600,
    
    "secret_key": "dev-secret-key-change-in-production",
    "debug": True,
    "log_level": "INFO",
    
    "api_title": "Beacon Commercial Register API",
    "api_version": "1.0.0",
    "api_description": "API for managing commercial register data",
    
    "allowed_origins": ["http://localhost:3000", "http://localhost:8080"],
    "rate_limits": {
        "requests_per_minute": 100,
        "requests_per_hour": 1000
    },
    
    "registry_api_url": "https://portal.registryagency.bg/CR/api/Deeds",
    "registry_api_timeout": 30,
    
    "search_limits": {
        "max_results": 100,
        "default_limit": 25
    }
}

if ENV in ["development", "production", "testing"]:
    try:
        local_config = {}
        
        exec(open(f"app/configs/{ENV}.py").read(), {"config": local_config})
        
        config.update(local_config.get("config", {}))
        
    except FileNotFoundError:
        print(f"Warning: Environment config file 'app/configs/{ENV}.py' not found")
    except Exception as e:
        print(f"Error loading environment config: {e}")

if ENV == "testing":
    if not config["database_url"].endswith("beacon_test"):
        config["database_url"] = config["database_url"].replace(
            "beacon_dev", "beacon_test"
        ).replace(
            "beacon.db", "beacon_test.db"
        )
    
    config["debug"] = True
    config["log_level"] = "DEBUG"
    config["cache_ttl"] = 60

if ENV == "production":
    if config["secret_key"] == "dev-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be set in production")
    if config["debug"]:
        raise ValueError("DEBUG must be False in production")
    if "localhost" in config["allowed_origins"]:
        raise ValueError("localhost origins not allowed in production")

DATABASE_URL = config["database_url"]
DATABASE_ECHO = config["database_echo"]
DATABASE_POOL_SIZE = config["database_pool_size"]
DATABASE_MAX_OVERFLOW = config["database_max_overflow"]
DATABASE_POOL_PRE_PING = config["database_pool_pre_ping"]

REDIS_URL = config["redis_url"]
CACHE_TTL = config["cache_ttl"]

SECRET_KEY = config["secret_key"]
DEBUG = config["debug"]
LOG_LEVEL = config["log_level"]

API_TITLE = config["api_title"]
API_VERSION = config["api_version"]
API_DESCRIPTION = config["api_description"]

ALLOWED_ORIGINS = config["allowed_origins"]
RATE_LIMITS = config["rate_limits"]

REGISTRY_API_URL = config["registry_api_url"]
REGISTRY_API_TIMEOUT = config["registry_api_timeout"]

SEARCH_LIMITS = config["search_limits"]
