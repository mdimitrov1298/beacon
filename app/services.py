from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, update, delete
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from .models import Company, User, CompanyResponse, UserResponse, ActivityLog, ActivityLogResponse, SyncHistory
from .exceptions import (
    CompanyNotFound, DuplicateCompanyError, DatabaseError, 
    ValidationError, ExternalServiceError
)
from .cache import CacheService

logger = logging.getLogger(__name__)


class CompanyService:
    
    def __init__(self, db: AsyncSession, cache: CacheService):
        self.db = db
        self.cache = cache
    
    async def get_company(self, uid: str) -> Company:
        cache_key = f"company:{uid}"
        if cached := await self.cache.get(cache_key):
            logger.debug(f"Cache hit for company {uid}")
            return CompanyResponse.model_validate(cached)
        
        try:
            result = await self.db.execute(
                select(Company).where(Company.uid == uid)
            )
            company = result.scalar_one_or_none()
            
            if not company:
                raise CompanyNotFound(uid)
            
            company_dict = {
                'uid': company.uid,
                'name': company.name,
                'manager': company.manager,
                'address': company.address,
                'legal_form': company.legal_form,
                'status': company.status,
                'registration_date': company.registration_date,
                'capital': company.capital,
                'main_activity': company.main_activity,
                'phone': company.phone,
                'email': company.email,
                'website': company.website,
                'created_at': company.created_at,
                'updated_at': company.updated_at
            }
            
            if isinstance(company_dict['created_at'], str):
                try:
                    company_dict['created_at'] = datetime.strptime(company_dict['created_at'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    company_dict['created_at'] = None
            
            if isinstance(company_dict['updated_at'], str):
                try:
                    company_dict['updated_at'] = datetime.strptime(company_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    company_dict['updated_at'] = None
            
            await self.cache.set(cache_key, company_dict, ttl=3600)
            
            return CompanyResponse.model_validate(company_dict)
            
        except CompanyNotFound:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error getting company {uid}: {e}")
            raise DatabaseError("company_retrieval", str(e))
    
    async def get_company_by_uid(self, uid: str) -> Company:
        return await self.get_company(uid)
    
    async def search_companies(self, name: str, limit: int = 25, include_inactive: bool = False) -> List[Dict[str, Any]]:
        try:
            query = select(Company.uid, Company.name, Company.legal_form, Company.status)
            query = query.where(Company.name.ilike(f"%{name}%"))
            
            if not include_inactive:
                query = query.where(Company.status.in_(["active", "Active", "Активен", "активен"]))
            
            query = query.order_by(Company.name).limit(limit)
            
            result = await self.db.execute(query)
            companies = result.fetchall()
            
            return [
                {
                    "uid": company[0],
                    "name": company[1],
                    "legal_form": company[2],
                    "status": company[3]
                }
                for company in companies
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching companies: {e}")
            raise DatabaseError("company_search", str(e))
    
    async def search_companies_by_uid(self, uid: str, limit: int = 25) -> List[Dict[str, Any]]:
        try:
            query = select(Company.uid, Company.name, Company.legal_form, Company.status)
            query = query.where(Company.uid.ilike(f"%{uid}%"))
            query = query.order_by(Company.uid).limit(limit)
            
            result = await self.db.execute(query)
            companies = result.fetchall()
            
            return [
                {
                    "uid": company[0],
                    "name": company[1],
                    "legal_form": company[2],
                    "status": company[3]
                }
                for company in companies
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching companies by UID: {e}")
            raise DatabaseError("company_search", str(e))
    
    async def search_companies_by_name(self, name: str, limit: int = 25, include_inactive: bool = False) -> List[Dict[str, Any]]:
        try:
            query = select(Company.uid, Company.name, Company.legal_form, Company.status)
            query = query.where(Company.name.ilike(f"%{name}%"))
            
            if not include_inactive:
                query = query.where(Company.status.in_(["active", "Active", "Активен", "активен"]))
            
            query = query.order_by(Company.name).limit(limit)
            
            result = await self.db.execute(query)
            companies = result.fetchall()
            
            return [
                {
                    "uid": company[0],
                    "name": company[1],
                    "legal_form": company[2],
                    "status": company[3]
                }
                for company in companies
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching companies by name: {e}")
            raise DatabaseError("company_search", str(e))

    async def get_all_companies(self, limit: int = 100, offset: int = 0) -> List[Company]:
        try:
            query = select(Company).order_by(Company.name).limit(limit).offset(offset)
            result = await self.db.execute(query)
            scalars = await result.scalars()
            return scalars.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all companies: {e}")
            raise DatabaseError("company_listing", str(e))
    
    async def create_company(self, company_data: Dict[str, Any]) -> Company:
        try:
            company = Company(**company_data)
            self.db.add(company)
            await self.db.commit()
            await self.db.refresh(company)
            
            cache_key = f"company:{company.uid}"
            await self.cache.delete(cache_key)
            
            return company
            
        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateCompanyError(company_data.get('uid', 'unknown'))
            raise DatabaseError("company_creation", str(e))
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating company: {e}")
            raise DatabaseError("company_creation", str(e))
    
    async def update_company(self, uid: str, update_data: Dict[str, Any]) -> Company:
        try:
            company = await self.get_company(uid)
            
            stmt = update(Company).where(Company.uid == uid).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            
            cache_key = f"company:{uid}"
            await self.cache.delete(cache_key)
            
            return await self.get_company(uid)
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating company {uid}: {e}")
            raise DatabaseError("company_update", str(e))
    
    async def delete_company(self, uid: str) -> bool:
        try:
            company = await self.get_company(uid)
            
            stmt = delete(Company).where(Company.uid == uid)
            await self.db.execute(stmt)
            await self.db.commit()
            
            cache_key = f"company:{uid}"
            await self.cache.delete(cache_key)
            
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting company {uid}: {e}")
            raise DatabaseError("company_deletion", str(e))
    
    async def update_company_enrichment(self, uid: str, enrichment_data: Dict[str, Any]) -> Company:
        try:
            company = await self.get_company(uid)
            
            stmt = update(Company).where(Company.uid == uid).values(**enrichment_data)
            await self.db.execute(stmt)
            await self.db.commit()
            
            cache_key = f"company:{uid}"
            await self.cache.delete(cache_key)
            
            return await self.get_company(uid)
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating company enrichment {uid}: {e}")
            raise DatabaseError("company_enrichment_update", str(e))
    
    async def import_companies(self, companies_data: List[Dict[str, Any]]) -> Dict[str, int]:
        try:
            imported = 0
            updated = 0
            failed = 0
            
            for company_data in companies_data:
                try:
                    try:
                        existing = await self.get_company(company_data['uid'])
                        stmt = update(Company).where(Company.uid == company_data['uid']).values(**company_data)
                        await self.db.execute(stmt)
                        updated += 1
                    except CompanyNotFound:
                        company = Company(**company_data)
                        self.db.add(company)
                        imported += 1
                        
                    cache_key = f"company:{company_data['uid']}"
                    await self.cache.delete(cache_key)
                    
                except Exception as e:
                    logger.error(f"Error importing company {company_data.get('uid', 'unknown')}: {e}")
                    failed += 1
            
            await self.db.commit()
            
            return {
                "imported": imported,
                "updated": updated,
                "errors": failed,
                "total": len(companies_data)
            }
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error during company import: {e}")
            raise DatabaseError("company_import", str(e))


class UserService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return await result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user {user_id}: {e}")
            raise DatabaseError("user_retrieval", str(e))
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return await result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by username {username}: {e}")
            raise DatabaseError("user_retrieval", str(e))
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        try:
            result = await self.db.execute(
                select(User).where(User.api_key == api_key)
            )
            return await result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by API key: {e}")
            raise DatabaseError("user_retrieval", str(e))
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        try:
            user = User(**user_data)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
            
        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateCompanyError("username" if "username" in str(e) else "api_key")
            raise DatabaseError("user_creation", str(e))
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating user: {e}")
            raise DatabaseError("user_creation", str(e))
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> User:
        try:
            stmt = update(User).where(User.id == user_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            
            return await self.get_user_by_id(user_id)
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating user {user_id}: {e}")
            raise DatabaseError("user_update", str(e))
    
    async def delete_user(self, user_id: int) -> bool:
        try:
            stmt = delete(User).where(User.id == user_id)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting user {user_id}: {e}")
            raise DatabaseError("user_deletion", str(e))


class LogService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_log_entry(self, action: str, details: str, user_id: int, company_uid: Optional[str] = None) -> bool:
        try:
            log_entry = ActivityLog(
                action=action,
                details=details,
                user_id=user_id,
                company_uid=company_uid
            )
            self.db.add(log_entry)
            await self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error adding log entry: {e}")
            return False
    
    async def get_user_activity(self, user_id: int, limit: int = 50) -> List[ActivityLog]:
        try:
            query = select(ActivityLog).where(ActivityLog.user_id == user_id)
            query = query.order_by(ActivityLog.timestamp.desc()).limit(limit)
            
            result = await self.db.execute(query)
            scalars = await result.scalars()
            return scalars.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user activity {user_id}: {e}")
            raise DatabaseError("activity_retrieval", str(e))
    
    async def get_company_activity(self, company_uid: str, limit: int = 50) -> List[ActivityLog]:
        try:
            query = select(ActivityLog).where(ActivityLog.company_uid == company_uid)
            query = query.order_by(ActivityLog.timestamp.desc()).limit(limit)
            
            result = await self.db.execute(query)
            scalars = await result.scalars()
            return scalars.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting company activity {company_uid}: {e}")
            raise DatabaseError("activity_retrieval", str(e))
    
    async def get_recent_activity(self, limit: int = 50) -> List[ActivityLog]:
        try:
            query = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit)
            result = await self.db.execute(query)
            scalars = await result.scalars()
            return scalars.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent activity: {e}")
            raise DatabaseError("activity_retrieval", str(e))


class SyncService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def start_sync(self, sync_type: str) -> SyncHistory:
        try:
            sync_record = SyncHistory(sync_type=sync_type, status="running")
            self.db.add(sync_record)
            await self.db.commit()
            await self.db.refresh(sync_record)
            return sync_record
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error starting sync: {e}")
            raise DatabaseError("sync_start", str(e))
    
    async def update_sync_progress(self, sync_id: int, **kwargs) -> bool:
        try:
            stmt = update(SyncHistory).where(SyncHistory.id == sync_id).values(**kwargs)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating sync progress {sync_id}: {e}")
            return False
    
    async def complete_sync(self, sync_id: int, status: str = "completed", error_message: Optional[str] = None) -> bool:
        try:
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow()
            }
            if error_message:
                update_data["error_message"] = error_message
            
            stmt = update(SyncHistory).where(SyncHistory.id == sync_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error completing sync {sync_id}: {e}")
            return False
    
    async def is_date_synced(self, date: str) -> bool:
        """Check if a specific date has already been synced"""
        try:
            result = await self.db.execute(
                select(SyncHistory).where(
                    SyncHistory.sync_type == "daily",
                    SyncHistory.status == "completed",
                    SyncHistory.started_at >= datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0),
                    SyncHistory.started_at < datetime.strptime(date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                )
            )
            return await result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking sync status for {date}: {e}")
            return False
    
    async def create_sync_record(self, date: str, sync_type: str = "daily") -> int:
        """Create a new sync record and return its ID"""
        try:
            sync_record = SyncHistory(
                sync_date=datetime.strptime(date, "%Y-%m-%d").date(),
                sync_type=sync_type,
                status="running",
                started_at=datetime.utcnow()
            )
            self.db.add(sync_record)
            await self.db.commit()
            await self.db.refresh(sync_record)
            return sync_record.id
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating sync record for {date}: {e}")
            raise DatabaseError("sync_record_creation", str(e))
    
    async def update_sync_record(self, date: str, **kwargs) -> bool:
        """Update sync record for a specific date"""
        try:

            result = await self.db.execute(
                select(SyncHistory).where(
                    SyncHistory.sync_type == "daily",
                    SyncHistory.started_at >= datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0),
                    SyncHistory.started_at < datetime.strptime(date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                ).order_by(SyncHistory.started_at.desc())
            )
            sync_record = await result.scalar_one_or_none()
            
            if sync_record:
                stmt = update(SyncHistory).where(SyncHistory.id == sync_record.id).values(**kwargs)
                await self.db.execute(stmt)
                await self.db.commit()
                return True
            else:
                logger.warning(f"No sync record found for date {date}")
                return False
                
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating sync record for {date}: {e}")
            return False


async def get_company_service(db: AsyncSession, cache: CacheService) -> CompanyService:
    return CompanyService(db, cache)


async def get_user_service(db: AsyncSession) -> UserService:
    return UserService(db)


async def get_log_service(db: AsyncSession) -> LogService:
    return LogService(db)


async def get_sync_service(db: AsyncSession) -> SyncService:
    return SyncService(db)


async def get_sync_history_service(db: AsyncSession) -> SyncService:
    return SyncService(db)
