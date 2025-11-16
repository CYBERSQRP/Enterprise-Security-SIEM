from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    IOC, IOCCreate, IOCModel, IOCType, ThreatLevel,
    ThreatActor, ThreatActorCreate, ThreatActorModel,
    EnrichmentRequest, EnrichmentResponse, IOCMatch
)
from app.enrichment import EnrichmentService

router = APIRouter()


# IOC endpoints

@router.post("/iocs", response_model=IOC, status_code=201)
async def create_ioc(
    ioc: IOCCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new IOC"""
    db_ioc = IOCModel(
        **ioc.model_dump(),
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    db.add(db_ioc)
    await db.commit()
    await db.refresh(db_ioc)
    return db_ioc


@router.get("/iocs", response_model=List[IOC])
async def list_iocs(
    ioc_type: Optional[IOCType] = None,
    threat_level: Optional[ThreatLevel] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List IOCs with filters"""
    stmt = select(IOCModel)

    filters = []
    if ioc_type:
        filters.append(IOCModel.ioc_type == ioc_type)
    if threat_level:
        filters.append(IOCModel.threat_level == threat_level)
    if is_active is not None:
        filters.append(IOCModel.is_active == is_active)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.limit(limit).offset(offset).order_by(IOCModel.created_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/iocs/{ioc_id}", response_model=IOC)
async def get_ioc(
    ioc_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get an IOC by ID"""
    stmt = select(IOCModel).where(IOCModel.id == ioc_id)
    result = await db.execute(stmt)
    ioc = result.scalar_one_or_none()

    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    return ioc


@router.post("/iocs/match")
async def match_ioc(
    value: str,
    ioc_type: IOCType,
    db: AsyncSession = Depends(get_db)
) -> Optional[IOCMatch]:
    """Check if a value matches any known IOC"""
    stmt = select(IOCModel).where(
        and_(
            IOCModel.value == value,
            IOCModel.ioc_type == ioc_type,
            IOCModel.is_active == True
        )
    )

    result = await db.execute(stmt)
    ioc = result.scalar_one_or_none()

    if not ioc:
        return None

    return IOCMatch(
        ioc_id=ioc.id,
        ioc_type=ioc.ioc_type,
        value=ioc.value,
        threat_level=ioc.threat_level,
        source=ioc.source,
        description=ioc.description,
        tags=ioc.tags,
        matched_at=datetime.utcnow()
    )


@router.post("/enrich")
async def enrich_indicator(
    request: EnrichmentRequest,
    db: AsyncSession = Depends(get_db)
) -> EnrichmentResponse:
    """Enrich an indicator with threat intelligence"""
    enrichment_service = EnrichmentService()
    return await enrichment_service.enrich(request.value, request.ioc_type)


# Threat Actor endpoints

@router.post("/threat-actors", response_model=ThreatActor, status_code=201)
async def create_threat_actor(
    actor: ThreatActorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new threat actor"""
    db_actor = ThreatActorModel(**actor.model_dump())
    db.add(db_actor)
    await db.commit()
    await db.refresh(db_actor)
    return db_actor


@router.get("/threat-actors", response_model=List[ThreatActor])
async def list_threat_actors(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List threat actors"""
    stmt = select(ThreatActorModel).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/threat-actors/{actor_id}", response_model=ThreatActor)
async def get_threat_actor(
    actor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a threat actor by ID"""
    stmt = select(ThreatActorModel).where(ThreatActorModel.id == actor_id)
    result = await db.execute(stmt)
    actor = result.scalar_one_or_none()

    if not actor:
        raise HTTPException(status_code=404, detail="Threat actor not found")

    return actor


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get threat intelligence statistics"""
    from sqlalchemy import func

    # Count IOCs by type
    ioc_count_stmt = select(
        IOCModel.ioc_type,
        func.count(IOCModel.id).label('count')
    ).where(IOCModel.is_active == True).group_by(IOCModel.ioc_type)

    ioc_result = await db.execute(ioc_count_stmt)
    ioc_counts = {row[0]: row[1] for row in ioc_result}

    # Count IOCs by threat level
    threat_level_stmt = select(
        IOCModel.threat_level,
        func.count(IOCModel.id).label('count')
    ).where(IOCModel.is_active == True).group_by(IOCModel.threat_level)

    threat_result = await db.execute(threat_level_stmt)
    threat_counts = {row[0]: row[1] for row in threat_result}

    # Total threat actors
    actor_count_stmt = select(func.count(ThreatActorModel.id))
    actor_result = await db.execute(actor_count_stmt)
    actor_count = actor_result.scalar()

    return {
        "total_iocs": sum(ioc_counts.values()),
        "iocs_by_type": ioc_counts,
        "iocs_by_threat_level": threat_counts,
        "total_threat_actors": actor_count
    }
