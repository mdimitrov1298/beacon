config["log_level"] = "DEBUG"
config["database_echo"] = True

config["debug"] = True
config["allowed_origins"] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"]

config["database_url"] = "sqlite:///./beacon_dev.db"

config["cache_ttl"] = 1

config["rate_limit_default"] = "1000/minute"
config["rate_limit_search"] = "100/minute"
