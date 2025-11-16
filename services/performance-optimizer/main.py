"""
Performance Optimization Service - FastAPI Application

Provides intelligent query optimization, caching, data tiering,
and resource usage optimization.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse
import uvicorn

from optimizer import (
    PerformanceOptimizer,
    QueryMetrics,
    StorageTier
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
optimization_requests = Counter(
    'performance_optimization_requests_total',
    'Total number of optimization requests',
    ['optimization_type']
)
cache_hit_rate = Gauge(
    'performance_cache_hit_rate',
    'Query cache hit rate'
)
slow_queries_count = Gauge(
    'performance_slow_queries_count',
    'Number of slow queries detected'
)

# Global optimizer instance
optimizer: Optional[PerformanceOptimizer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global optimizer

    # Startup
    logger.info("Starting Performance Optimization Service...")
    optimizer = PerformanceOptimizer()
    logger.info("Performance Optimization Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Performance Optimization Service...")


app = FastAPI(
    title="Performance Optimization Service",
    description="Intelligent query optimization, caching, and resource management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryOptimizationRequest(BaseModel):
    """Query optimization request."""
    query: Dict[str, Any] = Field(..., description="Query to optimize")


class QueryAnalysisResponse(BaseModel):
    """Query analysis response."""
    original_query: Dict[str, Any]
    optimizations: List[Dict[str, str]]
    warnings: List[str]
    estimated_improvement: float


class OptimizedQueryResponse(BaseModel):
    """Optimized query response."""
    original_query: Dict[str, Any]
    optimized_query: Dict[str, Any]
    optimizations_applied: List[str]


class QueryExecutionRequest(BaseModel):
    """Query execution metrics request."""
    query_hash: str
    execution_time_ms: float
    rows_scanned: int
    rows_returned: int
    bytes_scanned: int
    cache_hit: bool = False
    index_used: bool = False


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float
    total_requests: int


class TieringRecommendationRequest(BaseModel):
    """Data tiering recommendation request."""
    data_age_days: int
    access_frequency: float


class TieringRecommendationResponse(BaseModel):
    """Data tiering recommendation response."""
    recommended_tier: str
    current_tier: Optional[str] = None
    reason: str


class SystemOptimizationResponse(BaseModel):
    """System optimization response."""
    timestamp: str
    optimizations_applied: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="performance-optimizer",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Update metrics
    stats = optimizer.query_cache.get_stats()
    cache_hit_rate.set(stats['hit_rate'])
    slow_queries_count.set(len(optimizer.query_optimizer.get_slow_queries()))

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/api/v1/analyze-query", response_model=QueryAnalysisResponse)
async def analyze_query(request: QueryOptimizationRequest):
    """
    Analyze a query and suggest optimizations.

    Returns warnings and optimization suggestions without modifying the query.
    """
    try:
        optimization_requests.labels(optimization_type='analyze').inc()

        analysis = optimizer.query_optimizer.analyze_query(request.query)

        return QueryAnalysisResponse(
            original_query=analysis['original_query'],
            optimizations=analysis['optimizations'],
            warnings=analysis['warnings'],
            estimated_improvement=analysis['estimated_improvement']
        )

    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/optimize-query", response_model=OptimizedQueryResponse)
async def optimize_query(request: QueryOptimizationRequest):
    """
    Optimize a query automatically.

    Returns the optimized version of the query.
    """
    try:
        optimization_requests.labels(optimization_type='optimize').inc()

        optimized_query = optimizer.query_optimizer.optimize_query(request.query)

        # Determine what optimizations were applied
        optimizations_applied = []
        if '_partition_hint' in optimized_query:
            optimizations_applied.append("Added time-based partitioning hint")
        if 'limit' in optimized_query and 'limit' not in request.query:
            optimizations_applied.append("Added query limit to prevent unbounded results")
        if optimized_query.get('fields') != request.query.get('fields'):
            optimizations_applied.append("Optimized field projection")

        return OptimizedQueryResponse(
            original_query=request.query,
            optimized_query=optimized_query,
            optimizations_applied=optimizations_applied
        )

    except Exception as e:
        logger.error(f"Error optimizing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/record-execution")
async def record_execution(request: QueryExecutionRequest):
    """
    Record query execution metrics for analysis.

    Helps identify slow queries and optimization opportunities.
    """
    try:
        metrics = QueryMetrics(
            query_hash=request.query_hash,
            execution_time_ms=request.execution_time_ms,
            rows_scanned=request.rows_scanned,
            rows_returned=request.rows_returned,
            bytes_scanned=request.bytes_scanned,
            cache_hit=request.cache_hit,
            index_used=request.index_used,
            timestamp=datetime.utcnow()
        )

        optimizer.query_optimizer.record_query_execution(metrics)

        return {
            "status": "recorded",
            "query_hash": request.query_hash,
            "is_slow": request.execution_time_ms > optimizer.query_optimizer.slow_query_threshold_ms
        }

    except Exception as e:
        logger.error(f"Error recording execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/slow-queries")
async def get_slow_queries(limit: int = 10):
    """
    Get slowest queries for review.

    Use this to identify queries that need optimization.
    """
    try:
        slow_queries = optimizer.query_optimizer.get_slow_queries(limit=limit)

        return {
            "count": len(slow_queries),
            "threshold_ms": optimizer.query_optimizer.slow_query_threshold_ms,
            "queries": [
                {
                    "query_hash": q.query_hash,
                    "execution_time_ms": q.execution_time_ms,
                    "rows_scanned": q.rows_scanned,
                    "rows_returned": q.rows_returned,
                    "cache_hit": q.cache_hit,
                    "index_used": q.index_used,
                    "timestamp": q.timestamp.isoformat()
                }
                for q in slow_queries
            ]
        }

    except Exception as e:
        logger.error(f"Error getting slow queries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get query cache statistics."""
    try:
        stats = optimizer.query_cache.get_stats()
        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Clear the query cache."""
    try:
        optimizer.query_cache.clear()
        return {"status": "cleared", "message": "Query cache has been cleared"}

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tiering/recommend", response_model=TieringRecommendationResponse)
async def recommend_tier(request: TieringRecommendationRequest):
    """
    Get storage tier recommendation for data.

    Based on data age and access patterns.
    """
    try:
        tier = optimizer.tiering_manager.determine_tier(
            data_age_days=request.data_age_days,
            access_frequency=request.access_frequency
        )

        reasons = []
        if tier == StorageTier.HOT:
            reasons.append("Data is recent and frequently accessed")
        elif tier == StorageTier.WARM:
            reasons.append("Data is somewhat recent or occasionally accessed")
        elif tier == StorageTier.COLD:
            reasons.append("Data is old but may still be accessed")
        else:
            reasons.append("Data is very old and rarely accessed")

        return TieringRecommendationResponse(
            recommended_tier=tier.value,
            reason="; ".join(reasons)
        )

    except Exception as e:
        logger.error(f"Error recommending tier: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tiering/analysis")
async def analyze_tiering():
    """Get data tiering efficiency analysis."""
    try:
        analysis = optimizer.tiering_manager.analyze_tiering_efficiency()
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing tiering: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/optimize-system", response_model=SystemOptimizationResponse)
async def optimize_system(background_tasks: BackgroundTasks):
    """
    Run comprehensive system optimization.

    Analyzes all aspects of performance and provides recommendations.
    """
    try:
        optimization_requests.labels(optimization_type='system').inc()

        result = await optimizer.optimize_system()

        return SystemOptimizationResponse(**result)

    except Exception as e:
        logger.error(f"Error optimizing system: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/performance-report")
async def get_performance_report():
    """Get comprehensive performance report."""
    try:
        report = optimizer.get_performance_report()
        return Response(content=report, media_type="application/json")

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/resource-usage")
async def get_resource_usage():
    """Get current resource usage analysis."""
    try:
        usage = optimizer.resource_optimizer.analyze_resource_usage()
        return usage

    except Exception as e:
        logger.error(f"Error getting resource usage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/scaling-recommendations")
async def get_scaling_recommendations():
    """Get resource scaling recommendations."""
    try:
        recommendations = optimizer.resource_optimizer.get_scaling_recommendations()
        return {
            "count": len(recommendations),
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error getting scaling recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get service statistics."""
    cache_stats = optimizer.query_cache.get_stats()
    slow_queries = len(optimizer.query_optimizer.get_slow_queries())

    return {
        "service": "performance-optimizer",
        "uptime": "healthy",
        "cache_hit_rate": cache_stats['hit_rate'],
        "slow_queries_count": slow_queries,
        "statistics": {
            "total_optimizations": "See /metrics endpoint",
            "cache_size": cache_stats['size']
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8093"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production") == "development"
    )
