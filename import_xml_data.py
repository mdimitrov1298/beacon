#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db_connection, update_company_enrichment, add_log_entry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XMLTradeRegisterImporter:
    
    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        self.imported_count = 0
        self.updated_count = 0
        self.error_count = 0
        
    def parse_xml_file(self, xml_file_path: Path) -> list:
        companies = []
        
        try:
            logger.info(f"Parsing {xml_file_path.name}")
            
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            filename = xml_file_path.name
            date_match = None
            if "Търговски регистър" in filename and ".xml" in filename:
                date_part = filename.replace("Търговски регистър ", "").replace(".xml", "").replace("г.", "")
                try:
                    date_match = datetime.strptime(date_part, "%d.%m.%Y")
                except ValueError:
                    logger.warning(f"Could not parse date from filename: {filename}")
            
            for deed in root.findall('.//Deed'):
                company_data = self._extract_company_from_deed(deed, date_match)
                if company_data:
                    companies.append(company_data)
            
            logger.info(f"Extracted {len(companies)} companies from {xml_file_path.name}")
            return companies
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {xml_file_path.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing {xml_file_path.name}: {e}")
            return []
    
    def _extract_company_from_deed(self, deed_elem, file_date) -> Optional[dict]:
        try:
            deed_attrs = deed_elem.attrib
            uid = deed_attrs.get('UIC')
            company_name = deed_attrs.get('CompanyName')
            legal_form = deed_attrs.get('LegalForm')
            deed_status = deed_attrs.get('DeedStatus')
            
            if not uid or not company_name:
                return None
            
            company_data = {
                'uid': uid,
                'name': company_name,
                'legal_form': legal_form,
                'status': deed_status,
                'manager': None,
                'address': None,
                'phone': None,
                'email': None,
                'website': None,
                'file_date': file_date.isoformat() if file_date else None
            }
            
            for subdeed in deed_elem.findall('.//SubDeed'):
                self._extract_subdeed_data(subdeed, company_data)
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            return None
    
    def _extract_subdeed_data(self, subdeed_elem, company_data: dict):
        try:
            managers_elem = subdeed_elem.find('.//Managers')
            if managers_elem is not None:
                for manager in managers_elem.findall('.//Manager'):
                    if manager.find('.//Name') is not None and manager.find('.//Name').text:
                        manager_name = manager.find('.//Name').text.strip()
                        if manager_name and manager_name != '**********':
                            company_data['manager'] = manager_name
                            break
            
            seat_elem = subdeed_elem.find('.//Seat')
            if seat_elem is not None:
                address_parts = []
                
                address_elem = seat_elem.find('.//Address')
                if address_elem is not None:
                    settlement = address_elem.find('.//Settlement')
                    if settlement is not None and settlement.text:
                        address_parts.append(settlement.text.strip())
                    
                    street = address_elem.find('.//Street')
                    if street is not None and street.text:
                        address_parts.append(street.text.strip())
                    
                    street_number = address_elem.find('.//StreetNumber')
                    if street_number is not None and street_number.text:
                        address_parts.append(street_number.text.strip())
                    
                    post_code = address_elem.find('.//PostCode')
                    if post_code is not None and post_code.text:
                        address_parts.append(post_code.text.strip())
                    
                    housing_estate = address_elem.find('.//HousingEstate')
                    if housing_estate is not None and housing_estate.text:
                        address_parts.append(housing_estate.text.strip())
                    
                    block = address_elem.find('.//Block')
                    if block is not None and block.text:
                        address_parts.append(f"бл. {block.text.strip()}")
                    
                    entrance = address_elem.find('.//Entrance')
                    if entrance is not None and entrance.text:
                        address_parts.append(f"вх. {entrance.text.strip()}")
                    
                    floor = address_elem.find('.//Floor')
                    if floor is not None and floor.text:
                        address_parts.append(f"ет. {floor.text.strip()}")
                    
                    apartment = address_elem.find('.//Apartment')
                    if apartment is not None and apartment.text:
                        address_parts.append(f"ап. {apartment.text.strip()}")
                
                if address_parts:
                    company_data['address'] = ', '.join(filter(None, address_parts))
                
                contacts_elem = seat_elem.find('.//Contacts')
                if contacts_elem is not None:
                    phone = contacts_elem.find('.//Phone')
                    if phone is not None and phone.text and phone.text.strip() != '**********':
                        company_data['phone'] = phone.text.strip()
                    
                    email = contacts_elem.find('.//EMail')
                    if email is not None and email.text:
                        company_data['email'] = email.text.strip()
                    
                    url = contacts_elem.find('.//URL')
                    if url is not None and url.text:
                        company_data['website'] = url.text.strip()
                        
        except Exception as e:
            logger.error(f"Error extracting subdeed data: {e}")
    
    def import_companies_to_database(self, companies: list) -> tuple:
        imported = 0
        updated = 0
        errors = 0
        
        for i, company in enumerate(companies):
            try:
                if self._import_single_company(company):
                    if company.get('file_date'):
                        imported += 1
                    else:
                        updated += 1
                else:
                    errors += 1
                
                if (i + 1) % 100 == 0:
                    import time
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error importing company {company.get('uid', 'unknown')}: {e}")
                errors += 1
        
        return imported, updated, errors
    
    def _import_single_company(self, company: dict) -> bool:
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM companies WHERE uid = ?", (company['uid'],))
            existing = cursor.fetchone()
            
            if existing:
                enrichment_data = {
                    'name': company.get('name'),
                    'manager': company.get('manager'),
                    'address': company.get('address'),
                    'legal_form': company.get('legal_form'),
                    'phone': company.get('phone'),
                    'email': company.get('email'),
                    'website': company.get('website')
                }
                
                enrichment_data = {k: v for k, v in enrichment_data.items() if v is not None}
                
                if enrichment_data:
                    success = update_company_enrichment(company['uid'], enrichment_data)
                    if success:
                        add_log_entry("xml_import", f"Updated company {company['uid']} from {company.get('file_date', 'unknown')}")
                        return True
            else:
                manager = company.get('manager') or 'Не е посочен'
                address = company.get('address') or 'Не е посочен'
                
                cursor.execute('''
                    INSERT INTO companies (
                        uid, name, manager, address, 
                        legal_form, phone, email, website,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    company['uid'],
                    company['name'],
                    manager,
                    address,
                    company.get('legal_form'),
                    company.get('phone'),
                    company.get('email'),
                    company.get('website')
                ))
                
                conn.commit()
                add_log_entry("xml_import", f"Inserted new company {company['uid']}: {company['name']} from {company.get('file_date', 'unknown')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Database error for company {company.get('uid', 'unknown')}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def process_all_files(self, max_files: int = None) -> dict:
        xml_files = list(self.data_directory.glob("*.xml"))
        
        if max_files:
            xml_files = xml_files[:max_files]
        
        logger.info(f"Found {len(xml_files)} XML files to process")
        
        total_companies = 0
        total_imported = 0
        total_updated = 0
        total_errors = 0
        
        for i, xml_file in enumerate(xml_files, 1):
            logger.info(f"Processing file {i}/{len(xml_files)}: {xml_file.name}")
            
            companies = self.parse_xml_file(xml_file)
            total_companies += len(companies)
            
            if companies:
                imported, updated, errors = self.import_companies_to_database(companies)
                total_imported += imported
                total_updated += updated
                total_errors += errors
                
                logger.info(f"File {xml_file.name}: {imported} imported, {updated} updated, {errors} errors")
            
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(xml_files)} files processed")
        
        return {
            'total_files': len(xml_files),
            'total_companies': total_companies,
            'total_imported': total_imported,
            'total_updated': total_updated,
            'total_errors': total_errors
        }

def main():
    data_dir = "/Users/martindimitrov/Documents/Trade register data/07dd2a58-f96e-48d9-82c9-9aa0b7513e0e"
    
    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    importer = XMLTradeRegisterImporter(data_dir)
    
    logger.info("Starting XML import process...")
    results = importer.process_all_files(max_files=1)
    
    logger.info("Import completed!")
    logger.info(f"Files processed: {results['total_files']}")
    logger.info(f"Total companies found: {results['total_companies']}")
    logger.info(f"New companies imported: {results['total_imported']}")
    logger.info(f"Existing companies updated: {results['total_updated']}")
    logger.info(f"Errors: {results['total_errors']}")

if __name__ == "__main__":
    main()
