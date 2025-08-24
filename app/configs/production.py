import os

config["debug"] = False
config["database_echo"] = False

config["rate_limit_default"] = "100/minute"
config["rate_limit_search"] = "10/minute"

config["cache_ttl"] = 24

config["database_url"] = os.getenv("DATABASE_URL", "sqlite:///./beacon_prod.db")

if not config["secret_key"]:
    raise ValueError("SECRET_KEY is required in production")

if config["allowed_origins"] == ["http://localhost:3000"]:
    raise ValueError("ALLOWED_ORIGINS must be configured for production")
