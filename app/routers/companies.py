from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..models import CompanyResponse, CompanySearchResult, NameSearchRequest
from ..services import get_company_service, get_log_service
from ..database import get_db
from ..cache import get_cache
from ..auth import get_current_user
from ..exceptions import CompanyNotFound
from ..enrichment import enrich_company_if_needed

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/companies/{uid}", response_model=CompanyResponse)
async def get_company(
    uid: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    cache = Depends(get_cache)
):
    try:
        company = await enrich_company_if_needed(uid)
        if not company:
            company_service = await get_company_service(db, cache)
            company = await company_service.get_company(uid)
        
        log_service = await get_log_service(db)
        await log_service.add_log_entry(
            "company_retrieval", 
            f"Company retrieved by UID: {uid}", 
            current_user['id'],
            uid
        )
        
        return company
        
    except CompanyNotFound:
        raise HTTPException(status_code=404, detail=f"Company with UID {uid} not found")
    except Exception as e:
        logger.error(f"Unexpected error getting company {uid}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/companies/search", response_model=List[CompanySearchResult])
async def search_companies(
    request: NameSearchRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    cache = Depends(get_cache)
):
    try:
        company_service = await get_company_service(db, cache)
        companies = await company_service.search_companies(
            request.name.strip(), 
            request.limit or 25,
            request.include_inactive
        )
        
        search_results = [
            CompanySearchResult(
                uid=company['uid'], 
                name=company['name'],
                legal_form=company.get('legal_form'),
                status=company.get('status')
            ) 
            for company in companies
        ]
        
        log_service = await get_log_service(db)
        search_details = f"Name search: '{request.name}', results={len(search_results)}"
        await log_service.add_log_entry(
            "name_search", 
            search_details, 
            current_user['id']
        )
        
        logger.info(f"User {current_user['username']} searched for '{request.name}', found {len(search_results)} results")
        
        return search_results
        
    except Exception as e:
        logger.error(f"Error in company search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")









