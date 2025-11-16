from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class IOCType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    CVE = "cve"
    YARA_RULE = "yara_rule"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IOCModel(Base):
    __tablename__ = "iocs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ioc_type = Column(SQLEnum(IOCType), nullable=False)
    value = Column(String, nullable=False, index=True)
    threat_level = Column(SQLEnum(ThreatLevel), nullable=False)
    source = Column(String, nullable=False)
    description = Column(String)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ThreatActorModel(Base):
    __tablename__ = "threat_actors"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False, unique=True)
    aliases = Column(JSON, default=list)
    description = Column(String)
    country = Column(String)
    motivation = Column(String)
    sophistication = Column(String)
    first_seen = Column(DateTime)
    last_activity = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Pydantic schemas

class IOCBase(BaseModel):
    ioc_type: IOCType
    value: str
    threat_level: ThreatLevel
    source: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IOCCreate(IOCBase):
    pass


class IOC(IOCBase):
    id: UUID
    first_seen: datetime
    last_seen: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IOCMatch(BaseModel):
    ioc_id: UUID
    ioc_type: IOCType
    value: str
    threat_level: ThreatLevel
    source: str
    description: Optional[str]
    tags: List[str]
    matched_at: datetime


class ThreatActorBase(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    country: Optional[str] = None
    motivation: Optional[str] = None
    sophistication: Optional[str] = None


class ThreatActorCreate(ThreatActorBase):
    pass


class ThreatActor(ThreatActorBase):
    id: UUID
    first_seen: Optional[datetime]
    last_activity: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnrichmentRequest(BaseModel):
    ioc_type: IOCType
    value: str


class EnrichmentResponse(BaseModel):
    value: str
    ioc_type: IOCType
    is_malicious: bool
    threat_level: Optional[ThreatLevel]
    sources: List[str]
    metadata: Dict[str, Any]
