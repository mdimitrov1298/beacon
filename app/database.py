import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text

from .config import DATABASE_URL, DATABASE_ECHO, DATABASE_POOL_SIZE, DATABASE_MAX_OVERFLOW, DATABASE_POOL_PRE_PING
from .exceptions import DatabaseError, ServiceUnavailableError
from .models import Base, User

logger = logging.getLogger(__name__)

if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_pre_ping=DATABASE_POOL_PRE_PING
    )

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise DatabaseError("session_operation", str(e))
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise DatabaseError("session_operation", str(e))
        finally:
            await session.close()


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
        await _create_default_users()
        
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise DatabaseError("initialization", str(e))
    except Exception as e:
        logger.error(f"Unexpected error initializing database: {e}")
        raise


async def _create_default_users():
    try:
        async with get_db_context() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM users"))
            existing_users = result.scalar()
            
            if existing_users == 0:
                logger.info("No default users created - API keys not configured")
            else:
                logger.info("Default users already exist")
                
    except SQLAlchemyError as e:
        logger.error(f"Error checking default users: {e}")
        raise DatabaseError("user_creation", str(e))


async def health_check() -> bool:
    try:
        async with get_db_context() as db:
            await db.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def close_db():
    await engine.dispose()
    logger.info("Database connections closed")


async def execute_query(query: str, params: Optional[dict] = None) -> list:
    try:
        async with get_db_context() as db:
            result = await db.execute(text(query), params or {})
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Query execution failed: {e}")
        raise DatabaseError("query_execution", str(e))


async def execute_update(query: str, params: Optional[dict] = None) -> int:
    try:
        async with get_db_context() as db:
            result = await db.execute(text(query), params or {})
            await db.commit()
            return result.rowcount
    except SQLAlchemyError as e:
        logger.error(f"Update execution failed: {e}")
        raise DatabaseError("update_execution", str(e))
