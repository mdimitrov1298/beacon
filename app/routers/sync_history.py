"""
Sync history management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..models import SyncHistoryResponse, SyncHistoryCreate
from ..services import get_sync_history_service, get_log_service
from ..database import get_db
from ..auth import get_current_user
from ..exceptions import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sync-history", response_model=List[SyncHistoryResponse])
async def get_sync_history(
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    sync_type: Optional[str] = Query(None, description="Filter by sync type"),
    status: Optional[str] = Query(None, description="Filter by sync status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get sync history records with optional filtering"""
    try:
        sync_history_service = await get_sync_history_service(db)
        
        records = await sync_history_service.get_recent_sync_history(limit=limit)
        
        if sync_type:
            records = [r for r in records if r.sync_type == sync_type]
        
        if status:
            records = [r for r in records if r.status == status]
        
        log_service = await get_log_service(db)
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "sync_history_view", 
            f"Viewed sync history (limit: {limit}, type: {sync_type}, status: {status})", 
            current_user['id']
        )
        
        return records
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync history")


@router.get("/sync-history/{sync_date}", response_model=SyncHistoryResponse)
async def get_sync_record(
    sync_date: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get sync history record for a specific date"""
    try:
        sync_history_service = await get_sync_history_service(db)
        record = await sync_history_service.get_sync_record(sync_date)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Sync record not found for date {sync_date}")
        
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "sync_record_view", 
            f"Viewed sync record for {sync_date}", 
            current_user['id']
        )
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync record for {sync_date}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync record")


@router.get("/sync-history/status/{sync_date}")
async def get_sync_status(
    sync_date: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check if a specific date has been synced"""
    try:
        sync_history_service = await get_sync_history_service(db)
        is_synced = await sync_history_service.is_date_synced(sync_date)
        
        return {
            "sync_date": sync_date,
            "is_synced": is_synced,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking sync status for {sync_date}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check sync status")


@router.get("/sync-history/failed")
async def get_failed_syncs(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get failed sync records from the last N days"""
    try:
        sync_history_service = await get_sync_history_service(db)
        failed_syncs = await sync_history_service.get_failed_syncs(days_back=days_back)
        
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "failed_syncs_view", 
            f"Viewed failed syncs for last {days_back} days", 
            current_user['id']
        )
        
        return {
            "days_back": days_back,
            "failed_count": len(failed_syncs),
            "failed_syncs": failed_syncs
        }
        
    except Exception as e:
        logger.error(f"Error getting failed syncs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get failed syncs")


@router.post("/sync-history/trigger")
async def trigger_manual_sync(
    sync_date: str,
    sync_type: str = "manual",
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Manually trigger a sync for a specific date"""
    try:
        from datetime import datetime
        try:
            datetime.strptime(sync_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        sync_history_service = await get_sync_history_service(db)
        
        if await sync_history_service.is_date_synced(sync_date):
            return {
                "message": f"Date {sync_date} has already been synced",
                "sync_date": sync_date,
                "status": "already_synced"
            }
        
        sync_id = await sync_history_service.create_sync_record(sync_date, sync_type)
        
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "manual_sync_trigger", 
            f"Manually triggered sync for {sync_date} (type: {sync_type})", 
            current_user['id']
        )
        
        return {
            "message": f"Manual sync triggered for {sync_date}",
            "sync_id": sync_id,
            "sync_date": sync_date,
            "sync_type": sync_type,
            "status": "queued"
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering manual sync for {sync_date}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger sync")


@router.get("/sync-history/stats")
async def get_sync_stats(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get sync statistics for the last N days"""
    try:
        sync_history_service = await get_sync_history_service(db)
        
        records = await sync_history_service.get_recent_sync_history(limit=1000)
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        recent_records = [r for r in records if r.sync_date >= cutoff_date]
        
        total_syncs = len(recent_records)
        successful_syncs = len([r for r in recent_records if r.is_successful])
        failed_syncs = len([r for r in recent_records if r.status == "failed"])
        
        total_companies_processed = sum(r.companies_processed for r in recent_records)
        total_companies_updated = sum(r.companies_updated for r in recent_records)
        total_companies_created = sum(r.companies_created for r in recent_records)
        
        success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
        
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "sync_stats_view", 
            f"Viewed sync stats for last {days_back} days", 
            current_user['id']
        )
        
        return {
            "period_days": days_back,
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": round(success_rate, 2),
            "total_companies_processed": total_companies_processed,
            "total_companies_updated": total_companies_updated,
            "total_companies_created": total_companies_created,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting sync stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync stats")
