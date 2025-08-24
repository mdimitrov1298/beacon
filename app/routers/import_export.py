"""
Import and export operations for company data
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import json
import csv
from io import StringIO
from loguru import logger

from ..models import CompanyResponse
from ..auth import get_current_user
from ..database import get_db
from ..cache import get_cache
from ..services import get_company_service, get_log_service

router = APIRouter(tags=["data"])


@router.post("/import", status_code=201)
async def import_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    cache = Depends(get_cache)
):
    """Import company data from open data file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        logger.info(f"User {current_user['username']} attempting to import file: {file.filename}")
        
        content = await file.read()
        
        if file.filename.endswith('.json'):
            try:
                companies_data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in file {file.filename}: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON format")
                
        elif file.filename.endswith('.csv'):
            try:
                csv_content = content.decode('utf-8')
                csv_reader = csv.DictReader(StringIO(csv_content))
                companies_data = list(csv_reader)
            except Exception as e:
                logger.error(f"Error parsing CSV file {file.filename}: {e}")
                raise HTTPException(status_code=400, detail="Error parsing CSV file")
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Use JSON or CSV"
            )
        
        required_fields = ['uid', 'name', 'manager', 'address']
        invalid_companies = []
        
        for i, company in enumerate(companies_data):
            if not all(field in company for field in required_fields):
                invalid_companies.append(i)
        
        if invalid_companies:
            logger.warning(f"File {file.filename} contains {len(invalid_companies)} invalid records")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid data structure. Missing required fields in {len(invalid_companies)} records"
            )
        
        company_service = await get_company_service(db, cache)
        log_service = await get_log_service(db)
        
        import_result = await company_service.import_companies(companies_data)
        
        import_details = f"Import: file={file.filename}, companies={import_result.get('imported', 0)}"
        import_details = f"Import: file={file.filename}, companies={import_result.get('imported', 0)}"
        await log_service.add_log_entry("import", import_details, current_user['id'])
        
        logger.info(f"Successfully imported {import_result.get('imported', 0)} companies from {file.filename}")
        
        return JSONResponse(
            status_code=201,
            content={
                "message": f"Successfully imported {import_result.get('imported', 0)} companies",
                "filename": file.filename,
                "imported_count": import_result.get('imported', 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during import: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error occurred during import"
        )


@router.get("/export", response_model=List[CompanyResponse])
async def export_data(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    cache = Depends(get_cache)
):
    """Export the full database as a JSON file"""
    try:
        logger.info(f"User {current_user['username']} requesting data export")
        
        company_service = await get_company_service(db, cache)
        log_service = await get_log_service(db)
        
        from sqlalchemy import select
        from sqlalchemy import select
        from ..models import Company
        
        query = select(Company).order_by(Company.name)
        result = await db.execute(query)
        companies = result.scalars().all()
        
        company_responses = []
        for company in companies:
            try:
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
                        from datetime import datetime
                        company_dict['created_at'] = datetime.strptime(company_dict['created_at'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        company_dict['created_at'] = None

                if isinstance(company_dict['updated_at'], str):
                    try:
                        from datetime import datetime
                        company_dict['updated_at'] = datetime.strptime(company_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        company_dict['updated_at'] = None
                
                company_responses.append(CompanyResponse.model_validate(company_dict))
            except Exception as e:
                logger.error(f"Error processing company {getattr(company, 'uid', 'unknown')}: {e}")
                continue
        
        export_details = f"Export: companies={len(company_responses)}"
        await log_service.add_log_entry("export", export_details, current_user['id'])
        
        logger.info(f"Successfully exported {len(company_responses)} companies for user {current_user['username']}")
        
        return company_responses
        
    except Exception as e:
        logger.error(f"Error during data export: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error occurred during export"
        )
