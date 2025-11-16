# Performance Optimization Service

Intelligent performance optimization service providing query optimization, caching, data tiering, and resource management for the SIEM platform.

## Features

- **Query Optimization**: Automatic query analysis and optimization
- **Intelligent Caching**: LRU cache with TTL for query results
- **Data Tiering**: Automated hot/warm/cold storage management
- **Resource Monitoring**: CPU, memory, and disk usage analysis
- **Slow Query Detection**: Identify and analyze slow queries
- **Scaling Recommendations**: Auto-scaling suggestions based on usage
- **Index Strategy**: Optimize indexing based on query patterns

## Storage Tiers

| Tier | Use Case | Max Age | Access Frequency | Storage Type |
|------|----------|---------|------------------|--------------|
| HOT | Recent, frequent access | 7 days | 10+ accesses/day | SSD |
| WARM | Recent or occasional | 30 days | 1+ accesses/day | HDD |
| COLD | Old, infrequent | 365 days | 0.1+ accesses/day | S3/Object Storage |
| FROZEN | Archive, compliance | Unlimited | <0.1 accesses/day | Glacier |

## API Endpoints

### Health Check
```bash
GET /health
```

### Analyze Query
```bash
POST /api/v1/analyze-query
Content-Type: application/json

{
  "query": {
    "filters": {
      "severity": "high"
    },
    "fields": "*",
    "limit": 1000
  }
}
```

Response:
```json
{
  "original_query": {...},
  "optimizations": [
    {
      "type": "add_index",
      "description": "Add index on filtered fields",
      "expected_improvement": "50-90% faster"
    }
  ],
  "warnings": ["Query performs full table scan"],
  "estimated_improvement": 0.0
}
```

### Optimize Query
```bash
POST /api/v1/optimize-query
Content-Type: application/json

{
  "query": {
    "filters": {
      "timestamp": {
        "gte": "2024-01-01T00:00:00Z",
        "lte": "2024-03-01T00:00:00Z"
      }
    }
  }
}
```

Response:
```json
{
  "original_query": {...},
  "optimized_query": {
    "filters": {...},
    "_partition_hint": "timestamp",
    "limit": 10000,
    "fields": ["timestamp", "event_type", "severity", "source_ip", "dest_ip", "user", "message"]
  },
  "optimizations_applied": [
    "Added time-based partitioning hint",
    "Added query limit to prevent unbounded results",
    "Optimized field projection"
  ]
}
```

### Record Query Execution
```bash
POST /api/v1/record-execution
Content-Type: application/json

{
  "query_hash": "abc123",
  "execution_time_ms": 1500.5,
  "rows_scanned": 1000000,
  "rows_returned": 100,
  "bytes_scanned": 52428800,
  "cache_hit": false,
  "index_used": true
}
```

### Get Slow Queries
```bash
GET /api/v1/slow-queries?limit=10
```

Response:
```json
{
  "count": 5,
  "threshold_ms": 1000,
  "queries": [
    {
      "query_hash": "abc123",
      "execution_time_ms": 5432.1,
      "rows_scanned": 5000000,
      "rows_returned": 50,
      "cache_hit": false,
      "index_used": false,
      "timestamp": "2024-01-15T10:30:00.000000"
    }
  ]
}
```

### Cache Statistics
```bash
GET /api/v1/cache/stats
```

Response:
```json
{
  "size": 450,
  "max_size": 10000,
  "hits": 8500,
  "misses": 2500,
  "hit_rate": 0.77,
  "total_requests": 11000
}
```

### Clear Cache
```bash
POST /api/v1/cache/clear
```

### Storage Tier Recommendation
```bash
POST /api/v1/tiering/recommend
Content-Type: application/json

{
  "data_age_days": 45,
  "access_frequency": 0.5
}
```

Response:
```json
{
  "recommended_tier": "cold",
  "current_tier": null,
  "reason": "Data is old but may still be accessed"
}
```

### Tiering Analysis
```bash
GET /api/v1/tiering/analysis
```

### System Optimization
```bash
POST /api/v1/optimize-system
```

Response:
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "optimizations_applied": [],
  "recommendations": [
    {
      "category": "query_optimization",
      "priority": "high",
      "description": "Found 5 slow queries",
      "action": "Review and optimize slow queries"
    },
    {
      "category": "caching",
      "priority": "medium",
      "description": "Low cache hit rate (35.00%)",
      "action": "Increase cache size or TTL"
    }
  ]
}
```

### Performance Report
```bash
GET /api/v1/performance-report
```

### Resource Usage
```bash
GET /api/v1/resource-usage
```

Response:
```json
{
  "cpu": {
    "current": 65.0,
    "threshold": 80.0,
    "status": "normal"
  },
  "memory": {
    "current": 70.0,
    "threshold": 85.0,
    "status": "normal"
  },
  "disk": {
    "current": 75.0,
    "threshold": 90.0,
    "status": "normal"
  }
}
```

### Scaling Recommendations
```bash
GET /api/v1/scaling-recommendations
```

### Statistics
```bash
GET /api/v1/stats
```

### Metrics
```bash
GET /metrics
```

## Query Optimization Examples

### Before Optimization
```json
{
  "filters": {
    "message": "*error*"
  },
  "fields": "*"
}
```

**Issues:**
- Leading wildcard prevents index usage
- Selects all fields (high data transfer)
- No limit (unbounded results)

### After Optimization
```json
{
  "filters": {
    "message": "error*"
  },
  "fields": ["timestamp", "severity", "message"],
  "limit": 10000,
  "_partition_hint": "timestamp"
}
```

**Improvements:**
- Removed leading wildcard
- Limited fields to reduce data transfer
- Added result limit
- Added partitioning hint

## Integration Examples

### Python
```python
import requests

# Analyze query
response = requests.post(
    "http://localhost:8093/api/v1/analyze-query",
    json={
        "query": {
            "filters": {"severity": "high"},
            "fields": "*"
        }
    }
)
analysis = response.json()
print(f"Warnings: {analysis['warnings']}")

# Get optimized version
response = requests.post(
    "http://localhost:8093/api/v1/optimize-query",
    json={
        "query": {
            "filters": {"severity": "high"}
        }
    }
)
optimized = response.json()
print(f"Optimizations: {optimized['optimizations_applied']}")

# Record execution metrics
requests.post(
    "http://localhost:8093/api/v1/record-execution",
    json={
        "query_hash": "query123",
        "execution_time_ms": 850.5,
        "rows_scanned": 10000,
        "rows_returned": 50,
        "bytes_scanned": 1048576,
        "cache_hit": False,
        "index_used": True
    }
)

# Check for slow queries
response = requests.get("http://localhost:8093/api/v1/slow-queries?limit=5")
slow_queries = response.json()
print(f"Found {slow_queries['count']} slow queries")
```

### cURL
```bash
# Optimize query
curl -X POST http://localhost:8093/api/v1/optimize-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "filters": {"event_type": "login"},
      "fields": "*"
    }
  }'

# Get cache stats
curl http://localhost:8093/api/v1/cache/stats

# Get storage tier recommendation
curl -X POST http://localhost:8093/api/v1/tiering/recommend \
  -H "Content-Type: application/json" \
  -d '{"data_age_days": 15, "access_frequency": 5.0}'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | 8093 |
| `ENV` | Environment (development/production) | production |
| `CACHE_MAX_SIZE` | Maximum cache entries | 10000 |
| `CACHE_DEFAULT_TTL` | Default TTL in seconds | 300 |
| `SLOW_QUERY_THRESHOLD_MS` | Slow query threshold | 1000 |

## Running Locally

### With Docker
```bash
docker build -t performance-optimizer .
docker run -p 8093:8093 performance-optimizer
```

### With Python
```bash
pip install -r requirements.txt
python main.py
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `performance_optimization_requests_total` - Total optimization requests by type
- `performance_cache_hit_rate` - Current cache hit rate
- `performance_slow_queries_count` - Number of slow queries detected

## Best Practices

### Query Optimization
1. Always add time range filters
2. Use specific field projections instead of `SELECT *`
3. Add limits to prevent unbounded results
4. Avoid leading wildcards in searches
5. Use indexes on frequently filtered fields

### Caching
1. Cache frequently executed queries
2. Set appropriate TTLs based on data volatility
3. Monitor cache hit rate (target >70%)
4. Clear cache after schema changes

### Data Tiering
1. Move old data to cold storage
2. Archive compliance data to frozen tier
3. Keep recent data in hot tier
4. Monitor access patterns for tier adjustments

### Resource Management
1. Monitor resource usage regularly
2. Act on scaling recommendations
3. Optimize indexes based on query patterns
4. Archive or delete unused data

## Development

### Adding New Optimization Types
1. Add optimization logic to `QueryOptimizer` class
2. Update `analyze_query()` to detect the pattern
3. Implement fix in `optimize_query()`
4. Document the optimization

### Extending Caching
1. Add cache invalidation strategies
2. Implement distributed caching for multi-node
3. Add cache warming for common queries

## License

Copyright © 2024 Enterprise Security SIEM
