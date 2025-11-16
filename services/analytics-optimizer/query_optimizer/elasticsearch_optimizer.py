"""
Elasticsearch Query Optimizer

Analyzes and optimizes Elasticsearch queries for better performance.
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import json
import re


@dataclass
class OptimizationResult:
    """Query optimization result"""
    original_query: Dict
    optimized_query: Dict
    improvements: List[str]
    estimated_performance_gain: float


class ElasticsearchOptimizer:
    """
    Optimizes Elasticsearch queries for better performance.

    Optimization strategies:
    - Convert wildcards to term queries when possible
    - Move clauses to filter context for caching
    - Limit _source fields to reduce data transfer
    - Add size limits to prevent large result sets
    - Optimize aggregations
    - Use index patterns effectively
    """

    def __init__(self):
        self.optimization_count = 0

    def optimize_query(self, query: Dict, index_pattern: str = "*") -> OptimizationResult:
        """
        Optimize an Elasticsearch query.

        Args:
            query: Original Elasticsearch query DSL
            index_pattern: Index pattern being queried

        Returns:
            OptimizationResult with optimized query and improvements
        """
        optimized = query.copy()
        improvements = []
        performance_gain = 0.0

        # Apply optimization strategies
        optimized, wildcard_improvement = self._optimize_wildcards(optimized)
        if wildcard_improvement:
            improvements.append("Converted wildcard to term query")
            performance_gain += 0.6  # 60% improvement

        optimized, filter_improvement = self._move_to_filter_context(optimized)
        if filter_improvement:
            improvements.append("Moved clauses to filter context for caching")
            performance_gain += 0.2  # 20% improvement

        optimized, source_improvement = self._limit_source_fields(optimized)
        if source_improvement:
            improvements.append("Limited _source fields to reduce data transfer")
            performance_gain += 0.1  # 10% improvement

        optimized, size_improvement = self._add_size_limit(optimized)
        if size_improvement:
            improvements.append("Added size limit to prevent large result sets")
            performance_gain += 0.05  # 5% improvement

        optimized, agg_improvement = self._optimize_aggregations(optimized)
        if agg_improvement:
            improvements.append("Optimized aggregations")
            performance_gain += 0.15  # 15% improvement

        self.optimization_count += 1

        return OptimizationResult(
            original_query=query,
            optimized_query=optimized,
            improvements=improvements,
            estimated_performance_gain=min(performance_gain, 0.95)  # Cap at 95%
        )

    def _optimize_wildcards(self, query: Dict) -> Tuple[Dict, bool]:
        """Convert wildcard queries to term queries when possible"""
        improved = False

        if 'query' in query and 'bool' in query['query']:
            bool_query = query['query']['bool']

            # Check must clauses
            if 'must' in bool_query:
                for i, clause in enumerate(bool_query['must']):
                    if 'wildcard' in clause:
                        # Check if wildcard is actually a simple term
                        for field, pattern in clause['wildcard'].items():
                            if self._is_simple_wildcard(pattern):
                                # Convert to term query
                                bool_query['must'][i] = {
                                    'term': {
                                        f"{field}.keyword": pattern.replace('*', '')
                                    }
                                }
                                improved = True

        return query, improved

    def _is_simple_wildcard(self, pattern: str) -> bool:
        """Check if wildcard pattern is simple enough to convert to term"""
        # Simple pattern: *value* or value* or *value
        if isinstance(pattern, str):
            if pattern.startswith('*') and pattern.endswith('*') and pattern.count('*') == 2:
                return True
            if pattern.startswith('*') or pattern.endswith('*') and pattern.count('*') == 1:
                return False
        return False

    def _move_to_filter_context(self, query: Dict) -> Tuple[Dict, bool]:
        """Move clauses to filter context for better caching"""
        improved = False

        if 'query' in query and 'bool' in query['query']:
            bool_query = query['query']['bool']

            # Candidates for filter context:
            # - term queries
            # - range queries
            # - exists queries

            if 'must' in bool_query:
                filter_candidates = []
                remaining_must = []

                for clause in bool_query['must']:
                    if self._is_filter_candidate(clause):
                        filter_candidates.append(clause)
                        improved = True
                    else:
                        remaining_must.append(clause)

                if filter_candidates:
                    bool_query['must'] = remaining_must
                    if 'filter' not in bool_query:
                        bool_query['filter'] = []
                    bool_query['filter'].extend(filter_candidates)

        return query, improved

    def _is_filter_candidate(self, clause: Dict) -> bool:
        """Check if clause is a good candidate for filter context"""
        # term, terms, range, exists are good filter candidates
        filter_types = ['term', 'terms', 'range', 'exists', 'prefix']
        return any(filter_type in clause for filter_type in filter_types)

    def _limit_source_fields(self, query: Dict) -> Tuple[Dict, bool]:
        """Limit _source fields to reduce data transfer"""
        improved = False

        # Only add _source limitation if not already specified
        if '_source' not in query:
            # Default essential fields
            query['_source'] = [
                '@timestamp',
                'event.action',
                'user.name',
                'source.ip',
                'destination.ip'
            ]
            improved = True

        return query, improved

    def _add_size_limit(self, query: Dict) -> Tuple[Dict, bool]:
        """Add size limit to prevent large result sets"""
        improved = False

        # Add size limit if not specified or too large
        if 'size' not in query:
            query['size'] = 100
            improved = True
        elif query.get('size', 0) > 10000:
            query['size'] = 10000
            improved = True

        return query, improved

    def _optimize_aggregations(self, query: Dict) -> Tuple[Dict, bool]:
        """Optimize aggregations for better performance"""
        improved = False

        if 'aggs' in query or 'aggregations' in query:
            aggs_key = 'aggs' if 'aggs' in query else 'aggregations'
            aggs = query[aggs_key]

            # Add execution_hint for terms aggregations
            for agg_name, agg_body in aggs.items():
                if 'terms' in agg_body:
                    if 'execution_hint' not in agg_body['terms']:
                        agg_body['terms']['execution_hint'] = 'map'
                        improved = True

                    # Add reasonable size limit
                    if 'size' not in agg_body['terms']:
                        agg_body['terms']['size'] = 10
                        improved = True

        return query, improved

    def analyze_query_complexity(self, query: Dict) -> Dict[str, Any]:
        """
        Analyze query complexity and provide recommendations.

        Args:
            query: Elasticsearch query

        Returns:
            Analysis results with recommendations
        """
        analysis = {
            'complexity_score': 0,
            'issues': [],
            'recommendations': []
        }

        # Check for expensive operations
        if self._has_wildcards(query):
            analysis['complexity_score'] += 10
            analysis['issues'].append('Uses wildcard queries')
            analysis['recommendations'].append('Consider using term or prefix queries')

        if self._has_regexp(query):
            analysis['complexity_score'] += 15
            analysis['issues'].append('Uses regex queries')
            analysis['recommendations'].append('Regex queries are expensive, use alternatives')

        if self._has_script(query):
            analysis['complexity_score'] += 20
            analysis['issues'].append('Uses script queries')
            analysis['recommendations'].append('Script queries are very expensive, pre-compute if possible')

        # Check result size
        size = query.get('size', 10)
        if size > 1000:
            analysis['complexity_score'] += 5
            analysis['issues'].append(f'Large result size: {size}')
            analysis['recommendations'].append('Use pagination or reduce result size')

        # Check aggregation complexity
        if 'aggs' in query or 'aggregations' in query:
            agg_count = len(query.get('aggs', query.get('aggregations', {})))
            if agg_count > 5:
                analysis['complexity_score'] += agg_count * 2
                analysis['issues'].append(f'Many aggregations: {agg_count}')
                analysis['recommendations'].append('Consider splitting into multiple queries')

        return analysis

    def _has_wildcards(self, query: Dict) -> bool:
        """Check if query uses wildcards"""
        return 'wildcard' in json.dumps(query).lower()

    def _has_regexp(self, query: Dict) -> bool:
        """Check if query uses regex"""
        return 'regexp' in json.dumps(query).lower()

    def _has_script(self, query: Dict) -> bool:
        """Check if query uses scripts"""
        return 'script' in json.dumps(query).lower()


# Example usage
if __name__ == "__main__":
    optimizer = ElasticsearchOptimizer()

    # Example query needing optimization
    query = {
        "query": {
            "bool": {
                "must": [
                    {"wildcard": {"user.name": "*admin*"}},
                    {"range": {"@timestamp": {"gte": "now-7d"}}},
                    {"term": {"event.category": "authentication"}}
                ]
            }
        }
    }

    result = optimizer.optimize_query(query, "logs-*")

    print("Original Query:")
    print(json.dumps(result.original_query, indent=2))

    print("\nOptimized Query:")
    print(json.dumps(result.optimized_query, indent=2))

    print("\nImprovements:")
    for improvement in result.improvements:
        print(f"  - {improvement}")

    print(f"\nEstimated Performance Gain: {result.estimated_performance_gain * 100:.1f}%")

    # Analyze complexity
    analysis = optimizer.analyze_query_complexity(query)
    print(f"\nComplexity Score: {analysis['complexity_score']}")
    print("Issues:", analysis['issues'])
    print("Recommendations:", analysis['recommendations'])
