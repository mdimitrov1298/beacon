from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    api_key = credentials.credentials
    
    try:
        if not api_key or api_key.strip() == "":
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    except HTTPException:
        raise
    except Exception:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


def require_api_key(api_key: str = Depends(get_api_key)) -> str:
    return api_key


async def get_current_user(api_key: str = Depends(get_api_key)):
    try:
        user = {
            "username": "testuser",
            "id": 1,
            "is_active": True,
            "api_key": api_key
        }
        
        if not user:
            logger.error(f"User not found for API key: {api_key[:8]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        logger.info(f"User authenticated: {user['username']} (ID: {user['id']})")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "ApiKey"},
        )
