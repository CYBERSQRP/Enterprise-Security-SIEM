"""
Performance Optimization Engine

This module provides advanced performance optimization capabilities including:
- Query optimization and caching
- Intelligent data tiering (hot/warm/cold)
- Resource usage optimization
- Adaptive indexing strategies
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import hashlib
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageTier(Enum):
    """Storage tier levels."""
    HOT = "hot"      # SSD, fastest access, most recent data
    WARM = "warm"    # HDD, moderate access, recent data
    COLD = "cold"    # S3/archive, slow access, old data
    FROZEN = "frozen"  # Glacier, very slow, compliance/archive


@dataclass
class QueryMetrics:
    """Metrics for a query execution."""
    query_hash: str
    execution_time_ms: float
    rows_scanned: int
    rows_returned: int
    bytes_scanned: int
    cache_hit: bool
    index_used: bool
    timestamp: datetime


@dataclass
class QueryCacheEntry:
    """Cached query result."""
    query_hash: str
    query_text: str
    result: Any
    cached_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    ttl_seconds: int = 300  # 5 minutes default


@dataclass
class IndexStrategy:
    """Index strategy for a field."""
    field_name: str
    index_type: str  # 'btree', 'hash', 'fulltext', 'geo'
    usage_count: int = 0
    avg_selectivity: float = 0.0
    last_used: Optional[datetime] = None
    size_bytes: int = 0


class QueryOptimizer:
    """
    Intelligent query optimizer that analyzes and optimizes queries.
    """

    def __init__(self):
        self.query_history: List[QueryMetrics] = []
        self.slow_query_threshold_ms = 1000
        self.query_patterns: Dict[str, int] = defaultdict(int)

    def analyze_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a query and suggest optimizations.

        Args:
            query: Query object to analyze

        Returns:
            Analysis with optimization suggestions
        """
        analysis = {
            'original_query': query,
            'optimizations': [],
            'estimated_improvement': 0.0,
            'warnings': []
        }

        # Check for full table scans
        if self._is_full_scan(query):
            analysis['warnings'].append('Query performs full table scan')
            analysis['optimizations'].append({
                'type': 'add_index',
                'description': 'Add index on filtered fields',
                'expected_improvement': '50-90% faster'
            })

        # Check for inefficient date ranges
        if self._has_wide_date_range(query):
            analysis['warnings'].append('Very wide date range specified')
            analysis['optimizations'].append({
                'type': 'narrow_date_range',
                'description': 'Consider narrowing time window',
                'expected_improvement': '30-70% faster'
            })

        # Check for wildcard searches
        if self._has_leading_wildcard(query):
            analysis['warnings'].append('Leading wildcard prevents index usage')
            analysis['optimizations'].append({
                'type': 'avoid_leading_wildcard',
                'description': 'Avoid wildcards at start of search terms',
                'expected_improvement': '40-80% faster'
            })

        # Check for OR conditions that could be optimized
        if self._has_or_conditions(query):
            analysis['optimizations'].append({
                'type': 'rewrite_or_to_in',
                'description': 'Rewrite OR conditions as IN clause',
                'expected_improvement': '10-30% faster'
            })

        # Check for missing field filters
        if self._missing_common_filters(query):
            analysis['optimizations'].append({
                'type': 'add_filters',
                'description': 'Add commonly used filters (severity, source, etc.)',
                'expected_improvement': '20-50% faster'
            })

        return analysis

    def optimize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically optimize a query.

        Args:
            query: Original query

        Returns:
            Optimized query
        """
        optimized = query.copy()

        # Add time-based partitioning hint
        if 'timestamp' in query.get('filters', {}):
            optimized['_partition_hint'] = 'timestamp'

        # Rewrite OR to IN
        if 'filters' in optimized:
            optimized['filters'] = self._rewrite_or_to_in(optimized['filters'])

        # Add limit if not present
        if 'limit' not in optimized:
            optimized['limit'] = 10000  # Prevent unbounded queries

        # Add field projection to reduce data transfer
        if 'fields' not in optimized or optimized['fields'] == '*':
            optimized['fields'] = self._suggest_fields(query)

        return optimized

    def _is_full_scan(self, query: Dict[str, Any]) -> bool:
        """Check if query will result in full table scan."""
        filters = query.get('filters', {})
        return len(filters) == 0

    def _has_wide_date_range(self, query: Dict[str, Any]) -> bool:
        """Check if date range is too wide."""
        filters = query.get('filters', {})
        if 'timestamp' in filters:
            time_range = filters['timestamp']
            if isinstance(time_range, dict) and 'gte' in time_range and 'lte' in time_range:
                start = datetime.fromisoformat(time_range['gte'])
                end = datetime.fromisoformat(time_range['lte'])
                delta = end - start
                return delta.days > 30  # More than 30 days is wide
        return False

    def _has_leading_wildcard(self, query: Dict[str, Any]) -> bool:
        """Check for leading wildcard searches."""
        filters = query.get('filters', {})
        for value in filters.values():
            if isinstance(value, str) and value.startswith('*'):
                return True
        return False

    def _has_or_conditions(self, query: Dict[str, Any]) -> bool:
        """Check if query has OR conditions."""
        return 'or' in str(query).lower()

    def _missing_common_filters(self, query: Dict[str, Any]) -> bool:
        """Check if common filters are missing."""
        filters = query.get('filters', {})
        common_filters = {'severity', 'source_type', 'event_type'}
        return len(common_filters.intersection(set(filters.keys()))) == 0

    def _rewrite_or_to_in(self, filters: Dict) -> Dict:
        """Rewrite OR conditions to IN clause."""
        # Simplified implementation
        return filters

    def _suggest_fields(self, query: Dict[str, Any]) -> List[str]:
        """Suggest commonly used fields."""
        return [
            'timestamp',
            'event_type',
            'severity',
            'source_ip',
            'dest_ip',
            'user',
            'message'
        ]

    def record_query_execution(self, metrics: QueryMetrics):
        """Record query execution metrics."""
        self.query_history.append(metrics)

        # Track query patterns
        self.query_patterns[metrics.query_hash] += 1

        # Identify slow queries
        if metrics.execution_time_ms > self.slow_query_threshold_ms:
            logger.warning(
                f"Slow query detected: {metrics.query_hash} "
                f"({metrics.execution_time_ms:.2f}ms)"
            )

    def get_slow_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """Get slowest queries."""
        sorted_queries = sorted(
            self.query_history,
            key=lambda x: x.execution_time_ms,
            reverse=True
        )
        return sorted_queries[:limit]

    def get_query_patterns(self) -> Dict[str, int]:
        """Get most common query patterns."""
        sorted_patterns = sorted(
            self.query_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_patterns[:20])


class QueryCache:
    """
    Intelligent query result cache with TTL and LRU eviction.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, QueryCacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, query_hash: str) -> Optional[Any]:
        """Get cached query result."""
        entry = self.cache.get(query_hash)

        if entry is None:
            self.misses += 1
            return None

        # Check if expired
        if self._is_expired(entry):
            del self.cache[query_hash]
            self.misses += 1
            return None

        # Update access stats
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        self.hits += 1

        return entry.result

    def put(self, query_hash: str, query_text: str, result: Any, ttl: Optional[int] = None):
        """Cache query result."""
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        entry = QueryCacheEntry(
            query_hash=query_hash,
            query_text=query_text,
            result=result,
            cached_at=datetime.utcnow(),
            ttl_seconds=ttl or self.default_ttl
        )

        self.cache[query_hash] = entry

    def invalidate(self, query_hash: str):
        """Invalidate a cached entry."""
        if query_hash in self.cache:
            del self.cache[query_hash]

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def _is_expired(self, entry: QueryCacheEntry) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.utcnow() - entry.cached_at).total_seconds()
        return age > entry.ttl_seconds

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return

        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed or self.cache[k].cached_at
        )
        del self.cache[lru_key]


class DataTieringManager:
    """
    Manages intelligent data tiering across hot/warm/cold storage.
    """

    def __init__(self):
        self.tier_policies: Dict[str, Dict] = {
            StorageTier.HOT.value: {
                'max_age_days': 7,
                'max_size_gb': 1000,
                'access_frequency_threshold': 10  # accesses per day
            },
            StorageTier.WARM.value: {
                'max_age_days': 30,
                'max_size_gb': 5000,
                'access_frequency_threshold': 1
            },
            StorageTier.COLD.value: {
                'max_age_days': 365,
                'max_size_gb': 50000,
                'access_frequency_threshold': 0.1
            },
            StorageTier.FROZEN.value: {
                'max_age_days': None,  # Unlimited
                'max_size_gb': None,  # Unlimited
                'access_frequency_threshold': 0
            }
        }

    def determine_tier(self, data_age_days: int, access_frequency: float) -> StorageTier:
        """
        Determine appropriate storage tier for data.

        Args:
            data_age_days: Age of data in days
            access_frequency: Number of accesses per day

        Returns:
            Appropriate storage tier
        """
        # Hot tier: recent and frequently accessed
        if data_age_days <= 7 and access_frequency >= 10:
            return StorageTier.HOT

        # Warm tier: somewhat recent or occasionally accessed
        if data_age_days <= 30 or access_frequency >= 1:
            return StorageTier.WARM

        # Cold tier: old but may be accessed
        if data_age_days <= 365:
            return StorageTier.COLD

        # Frozen tier: very old, rarely accessed
        return StorageTier.FROZEN

    async def migrate_data(
        self,
        data_id: str,
        from_tier: StorageTier,
        to_tier: StorageTier
    ) -> bool:
        """
        Migrate data between tiers.

        Args:
            data_id: Identifier of data to migrate
            from_tier: Source tier
            to_tier: Destination tier

        Returns:
            True if migration successful
        """
        logger.info(f"Migrating {data_id} from {from_tier.value} to {to_tier.value}")

        # In production, this would:
        # 1. Copy data to destination tier
        # 2. Verify data integrity
        # 3. Update metadata
        # 4. Delete from source tier
        # 5. Update routing rules

        await asyncio.sleep(0.1)  # Simulate migration

        return True

    def analyze_tiering_efficiency(self) -> Dict[str, Any]:
        """Analyze current tiering efficiency."""
        return {
            'total_storage_gb': 0,  # Would query actual storage
            'tier_distribution': {
                'hot': {'size_gb': 0, 'percentage': 0},
                'warm': {'size_gb': 0, 'percentage': 0},
                'cold': {'size_gb': 0, 'percentage': 0},
                'frozen': {'size_gb': 0, 'percentage': 0}
            },
            'recommendations': [
                'Migrate data older than 30 days to cold storage',
                'Consider compressing cold tier data'
            ]
        }


class ResourceOptimizer:
    """
    Optimizes resource usage across the system.
    """

    def __init__(self):
        self.cpu_threshold = 80.0  # percent
        self.memory_threshold = 85.0  # percent
        self.disk_threshold = 90.0  # percent

    def analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyze current resource usage."""
        # In production, would get actual metrics from monitoring system
        return {
            'cpu': {
                'current': 65.0,
                'threshold': self.cpu_threshold,
                'status': 'normal'
            },
            'memory': {
                'current': 70.0,
                'threshold': self.memory_threshold,
                'status': 'normal'
            },
            'disk': {
                'current': 75.0,
                'threshold': self.disk_threshold,
                'status': 'normal'
            }
        }

    def get_scaling_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for scaling resources."""
        usage = self.analyze_resource_usage()
        recommendations = []

        if usage['cpu']['current'] > self.cpu_threshold:
            recommendations.append({
                'resource': 'CPU',
                'action': 'scale_up',
                'reason': f"CPU usage ({usage['cpu']['current']}%) exceeds threshold",
                'recommendation': 'Add 2 more worker nodes'
            })

        if usage['memory']['current'] > self.memory_threshold:
            recommendations.append({
                'resource': 'Memory',
                'action': 'scale_up',
                'reason': f"Memory usage ({usage['memory']['current']}%) exceeds threshold",
                'recommendation': 'Increase memory per node or add nodes'
            })

        return recommendations

    def optimize_indexing_strategy(
        self,
        field_usage_stats: Dict[str, int]
    ) -> List[IndexStrategy]:
        """
        Optimize indexing strategy based on usage patterns.

        Args:
            field_usage_stats: Dictionary of field names to usage counts

        Returns:
            List of recommended index strategies
        """
        strategies = []

        # Sort fields by usage
        sorted_fields = sorted(
            field_usage_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Recommend indexes for top fields
        for field, count in sorted_fields[:10]:
            if count > 1000:  # High usage threshold
                strategies.append(IndexStrategy(
                    field_name=field,
                    index_type='btree',
                    usage_count=count
                ))

        return strategies


class PerformanceOptimizer:
    """
    Main performance optimization orchestrator.
    """

    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.query_cache = QueryCache(max_size=10000)
        self.tiering_manager = DataTieringManager()
        self.resource_optimizer = ResourceOptimizer()

    async def optimize_system(self) -> Dict[str, Any]:
        """
        Run comprehensive system optimization.

        Returns:
            Optimization results and recommendations
        """
        logger.info("Starting comprehensive system optimization")

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'optimizations_applied': [],
            'recommendations': []
        }

        # Analyze slow queries
        slow_queries = self.query_optimizer.get_slow_queries(limit=10)
        if slow_queries:
            results['recommendations'].append({
                'category': 'query_optimization',
                'priority': 'high',
                'description': f'Found {len(slow_queries)} slow queries',
                'action': 'Review and optimize slow queries'
            })

        # Check cache efficiency
        cache_stats = self.query_cache.get_stats()
        if cache_stats['hit_rate'] < 0.5:
            results['recommendations'].append({
                'category': 'caching',
                'priority': 'medium',
                'description': f'Low cache hit rate ({cache_stats["hit_rate"]:.2%})',
                'action': 'Increase cache size or TTL'
            })

        # Analyze resource usage
        resource_usage = self.resource_optimizer.analyze_resource_usage()
        scaling_recs = self.resource_optimizer.get_scaling_recommendations()
        results['recommendations'].extend(scaling_recs)

        # Analyze data tiering
        tiering_analysis = self.tiering_manager.analyze_tiering_efficiency()
        results['recommendations'].extend([
            {'category': 'data_tiering', 'priority': 'low', **rec}
            for rec in tiering_analysis['recommendations']
        ])

        logger.info(f"Optimization complete. Found {len(results['recommendations'])} recommendations")

        return results

    def get_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        report = {
            'query_cache': self.query_cache.get_stats(),
            'slow_queries': [
                {
                    'query_hash': q.query_hash,
                    'execution_time_ms': q.execution_time_ms,
                    'rows_scanned': q.rows_scanned
                }
                for q in self.query_optimizer.get_slow_queries(5)
            ],
            'query_patterns': self.query_optimizer.get_query_patterns(),
            'resource_usage': self.resource_optimizer.analyze_resource_usage()
        }

        return json.dumps(report, indent=2)
