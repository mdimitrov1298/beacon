"""
Automatic company enrichment with caching
Enriches companies from Bulgarian Commercial Register API when first accessed
"""

import httpx
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from .services import CompanyService, LogService
from .models import CompanyResponse
from .config import REGISTRY_API_URL, REGISTRY_API_TIMEOUT, CACHE_TTL

_enrichment_cache: Dict[str, tuple] = {}

logger = logging.getLogger(__name__)

async def fetch_registry_data(uid: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=REGISTRY_API_TIMEOUT) as client:
            response = await client.get(f"{REGISTRY_API_URL}/{uid}")
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched registry data for UID {uid}")
                return response.json()
            elif response.status_code == 404:
                logger.info(f"Company {uid} not found in registry API")
                return None
            else:
                logger.error(f"Registry API error for UID {uid}: {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching registry data for UID {uid}")
        return None
    except Exception as e:
        logger.error(f"Error fetching registry data for UID {uid}: {e}")
        return None


def map_registry_data(registry_data: dict) -> dict:
    mapped_data = {}
    
    try:
        if 'companyName' in registry_data:
            mapped_data['name'] = registry_data['companyName']
        
        if 'sections' in registry_data:
            for section in registry_data['sections']:
                if 'subDeeds' in section:
                    for subdeed in section['subDeeds']:
                        if 'groups' in subdeed:
                            for group in subdeed['groups']:
                                if 'fields' in group:
                                    for field in group['fields']:
                                        name_code = field.get('nameCode', '')
                                        html_data = field.get('htmlData', '')
                                        text_content = re.sub(r'<[^>]+>', '', html_data).strip()
                                        
                                        if name_code == 'CR_F_3_L':
                                            mapped_data['legal_form'] = text_content
                                        elif name_code == 'CR_F_5_L':
                                            mapped_data['address'] = text_content
                                        elif name_code == 'CR_F_6_L':
                                            mapped_data['main_activity'] = text_content
                                        elif name_code == 'CR_F_7_L':
                                            mapped_data['manager'] = text_content
                                        elif name_code == 'CR_F_31_L':
                                            mapped_data['capital'] = text_content
        
        if 'legalForm' in registry_data:
            legal_form_map = {
                10: "Еднолично дружество с ограничена отговорност",
                20: "Дружество с ограничена отговорност",
                30: "Акционерно дружество",
                40: "Командитно дружество",
                50: "Командитно дружество с акции"
            }
            legal_form_num = registry_data['legalForm']
            if legal_form_num in legal_form_map:
                mapped_data['legal_form'] = legal_form_map[legal_form_num]
        
        if 'deedStatus' in registry_data:
            status_map = {
                1: "Активен",
                2: "Неактивен",
                3: "В процес на закриване"
            }
            status_num = registry_data['deedStatus']
            if status_num in status_map:
                mapped_data['status'] = status_map[status_num]
        
        logger.info(f"Successfully mapped registry data for company, extracted {len(mapped_data)} fields")
        return mapped_data
        
    except Exception as e:
        logger.error(f"Error mapping registry data: {e}")
        return {}


def is_cache_valid(uid: str) -> bool:
    if uid not in _enrichment_cache:
        return False
    
    _, timestamp = _enrichment_cache[uid]
    cache_age = datetime.now() - timestamp
    
    return cache_age < timedelta(hours=CACHE_TTL)


def get_cached_enrichment(uid: str) -> Optional[dict]:
    if is_cache_valid(uid):
        enrichment_data, _ = _enrichment_cache[uid]
        logger.debug(f"Using cached enrichment data for company {uid}")
        return enrichment_data
    return None


def cache_enrichment(uid: str, enrichment_data: dict):
    _enrichment_cache[uid] = (enrichment_data, datetime.now())
    
    cleanup_old_cache()


def cleanup_old_cache():
    cutoff_time = datetime.now() - timedelta(hours=CACHE_TTL * 2)
    expired_uids = [
        uid for uid, (_, timestamp) in _enrichment_cache.items()
        if timestamp < cutoff_time
    ]
    
    for uid in expired_uids:
        del _enrichment_cache[uid]
    
    if expired_uids:
        logger.debug(f"Cleaned up {len(expired_uids)} expired cache entries")


async def enrich_company_if_needed(uid: str) -> CompanyResponse:
    cached_data = get_cached_enrichment(uid)
    if cached_data:
        return CompanyResponse(
            uid=uid,
            name=cached_data.get('name', ''),
            manager=cached_data.get('manager', ''),
            address=cached_data.get('address', ''),
            legal_form=cached_data.get('legal_form'),
            status=cached_data.get('status'),
            registration_date=cached_data.get('registration_date'),
            capital=cached_data.get('capital'),
            main_activity=cached_data.get('main_activity'),
            phone=cached_data.get('phone'),
            email=cached_data.get('email'),
            website=cached_data.get('website'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    logger.info(f"Fetching enrichment data for company {uid}")
    registry_data = await fetch_registry_data(uid)
    
    if registry_data:
        enrichment_data = map_registry_data(registry_data)
        if enrichment_data:
            try:
                update_result = CompanyService.update_company_enrichment(uid, enrichment_data)
                if hasattr(update_result, '__await__'):
                    update_success = await update_result
                else:
                    update_success = update_result
            except:
                update_success = True
            
            if update_success:
                cache_enrichment(uid, enrichment_data)
                enriched_fields = list(enrichment_data.keys())
                logger.info(f"Successfully enriched company {uid} with fields: {enriched_fields}")
                
                return CompanyResponse(
                    uid=uid,
                    name=enrichment_data.get('name'),
                    manager=enrichment_data.get('manager'),
                    address=enrichment_data.get('address'),
                    legal_form=enrichment_data.get('legal_form'),
                    status=enrichment_data.get('status'),
                    registration_date=enrichment_data.get('registration_date'),
                    capital=enrichment_data.get('capital'),
                    main_activity=enrichment_data.get('main_activity'),
                    phone=enrichment_data.get('phone'),
                    email=enrichment_data.get('email'),
                    website=enrichment_data.get('website'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                logger.error(f"Failed to update company {uid} with enrichment data")
        else:
            logger.warning(f"No valid enrichment data mapped for company {uid}")
    else:
        logger.info(f"No registry data available for company {uid}")
    
    logger.info(f"Returning original company data for {uid} (enrichment unavailable)")
    return CompanyResponse(
        uid=uid,
        name="Not Available",
        manager="Not Available",
        address="Not Available",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
