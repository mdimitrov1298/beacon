config = {
    "database_url": "sqlite:///./beacon_test.db",
    "database_echo": False,
    "database_pool_size": 5,
    "database_max_overflow": 10,
    "database_pool_pre_ping": True,
    
    "redis_url": "redis://localhost:6379",
    "cache_ttl": 300,
    
    "secret_key": "test-secret-key-not-for-production",
    "debug": False,
    "log_level": "DEBUG",
    
    "api_title": "Beacon Commercial Register API - Testing",
    "api_version": "1.0.0",
    "api_description": "Testing environment for Beacon Commercial Register API",
    
    "allowed_origins": ["*"],
    "rate_limits": {
        "requests_per_minute": 1000,
        "requests_per_hour": 10000
    },
    
    "registry_api_url": "https://api.registry.test",
    "registry_api_timeout": 30,
    
    "search_limits": {
        "max_results": 100,
        "default_limit": 25
    }
}
