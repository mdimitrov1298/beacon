from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, TIMESTAMP, Index, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"
    
    uid = Column(String(50), primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    
    manager = Column(String(200), nullable=True)
    address = Column(String(1000), nullable=True)
    legal_form = Column(String(100))
    status = Column(String(50), default="active")
    
    capital = Column(String(100))
    registration_date = Column(Date)
    
    phone = Column(String(50))
    email = Column(String(200))
    website = Column(String(500))
    
    main_activity = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    activities = relationship("ActivityLog", back_populates="company")
    
    __table_args__ = (
        Index('idx_company_name_legal_form', 'name', 'legal_form'),
        Index('idx_company_status', 'status'),
        Index('idx_company_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Company(uid='{self.uid}', name='{self.name}')>"
    
    @property
    def is_active(self) -> bool:
        return self.status == "active"
    
    @property
    def has_contact_info(self) -> bool:
        return bool(self.phone or self.email or self.website)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    api_key = Column(String(200), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    activities = relationship("ActivityLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_uid = Column(String(50), ForeignKey("companies.uid"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")
    company = relationship("Company", back_populates="activities")
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}')>"


class SyncHistory(Base):
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_date = Column(Date, nullable=False)
    sync_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SyncHistory(id={self.id}, type='{self.sync_type}', status='{self.status}')>"


class CompanyResponse(BaseModel):
    uid: str
    name: str
    manager: Optional[str] = None
    address: Optional[str] = None
    legal_form: Optional[str] = None
    status: Optional[str] = None
    registration_date: Optional[datetime] = None
    capital: Optional[str] = None
    main_activity: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class CompanySearchResult(BaseModel):
    uid: str
    name: str
    legal_form: Optional[str] = None
    status: Optional[str] = None


class NameSearchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    limit: Optional[int] = Field(25, ge=1, le=100)
    include_inactive: Optional[bool] = False


class CompanyCreate(BaseModel):
    uid: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=500)
    manager: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=1000)
    legal_form: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field("active", max_length=50)
    capital: Optional[str] = Field(None, max_length=100)
    registration_date: Optional[datetime] = None
    main_activity: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    manager: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=1000)
    legal_form: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    capital: Optional[str] = Field(None, max_length=100)
    registration_date: Optional[datetime] = None
    main_activity: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    api_key: str = Field(..., min_length=32, max_length=200)


class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    company_uid: Optional[str] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActivityLogCreate(BaseModel):
    user_id: int
    company_uid: Optional[str] = None
    action: str = Field(..., min_length=1, max_length=100)
    details: Optional[str] = Field(None, max_length=1000)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    api_key: Optional[str] = Field(None, min_length=32, max_length=200)
    is_active: Optional[bool] = None


class SyncHistoryResponse(BaseModel):
    id: int
    sync_type: str
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
