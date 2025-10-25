"""
Prometheus Metrics Configuration
Exposes application metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from fastapi import Response
import time
from typing import Callable
from functools import wraps


# Create custom registry
registry = CollectorRegistry()

# Application info
app_info = Info(
    'ancient_free_will_api',
    'Ancient Free Will Database API Information',
    registry=registry
)

# HTTP Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# GraphRAG metrics
graphrag_queries_total = Counter(
    'graphrag_queries_total',
    'Total GraphRAG queries',
    ['status'],
    registry=registry
)

graphrag_query_duration_seconds = Histogram(
    'graphrag_query_duration_seconds',
    'GraphRAG query duration in seconds',
    registry=registry
)

graphrag_queries_in_progress = Gauge(
    'graphrag_queries_in_progress',
    'Number of GraphRAG queries in progress',
    registry=registry
)

graphrag_nodes_retrieved = Histogram(
    'graphrag_nodes_retrieved',
    'Number of nodes retrieved per GraphRAG query',
    registry=registry
)

# Search metrics
search_queries_total = Counter(
    'search_queries_total',
    'Total search queries',
    ['search_type', 'status'],
    registry=registry
)

search_query_duration_seconds = Histogram(
    'search_query_duration_seconds',
    'Search query duration in seconds',
    ['search_type'],
    registry=registry
)

search_results_count = Histogram(
    'search_results_count',
    'Number of search results returned',
    ['search_type'],
    registry=registry
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'status'],
    registry=registry
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    registry=registry
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'token_type'],
    registry=registry
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'status'],
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry
)

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=registry
)

# Cache metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],
    registry=registry
)

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (0-1)',
    registry=registry
)

# Vector DB metrics
qdrant_queries_total = Counter(
    'qdrant_queries_total',
    'Total Qdrant queries',
    ['collection', 'status'],
    registry=registry
)

qdrant_query_duration_seconds = Histogram(
    'qdrant_query_duration_seconds',
    'Qdrant query duration in seconds',
    ['collection'],
    registry=registry
)

# Application state metrics
api_health = Gauge(
    'api_health',
    'API health status (1=healthy, 0=unhealthy)',
    registry=registry
)

database_health = Gauge(
    'database_health',
    'Database health status (1=healthy, 0=unhealthy)',
    registry=registry
)

qdrant_health = Gauge(
    'qdrant_health',
    'Qdrant health status (1=healthy, 0=unhealthy)',
    registry=registry
)

llm_health = Gauge(
    'llm_health',
    'LLM service health status (1=healthy, 0=unhealthy)',
    registry=registry
)


def init_metrics():
    """Initialize application metrics"""
    app_info.info({
        'version': '1.0.0',
        'name': 'Ancient Free Will Database API',
        'description': 'FAIR-compliant knowledge graph API with GraphRAG'
    })


def get_metrics() -> Response:
    """
    Get Prometheus metrics in text format

    Returns:
        FastAPI Response with Prometheus metrics
    """
    metrics_data = generate_latest(registry)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


def track_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Track HTTP request metrics

    Args:
        method: HTTP method
        endpoint: Request endpoint
        status_code: Response status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_graphrag_query(status: str, duration: float, nodes_count: int):
    """
    Track GraphRAG query metrics

    Args:
        status: Query status (success, error)
        duration: Query duration in seconds
        nodes_count: Number of nodes retrieved
    """
    graphrag_queries_total.labels(status=status).inc()
    graphrag_query_duration_seconds.observe(duration)
    graphrag_nodes_retrieved.observe(nodes_count)


def track_search_query(search_type: str, status: str, duration: float, results_count: int):
    """
    Track search query metrics

    Args:
        search_type: Type of search (fulltext, semantic, hybrid)
        status: Query status (success, error)
        duration: Query duration in seconds
        results_count: Number of results returned
    """
    search_queries_total.labels(search_type=search_type, status=status).inc()
    search_query_duration_seconds.labels(search_type=search_type).observe(duration)
    search_results_count.labels(search_type=search_type).observe(results_count)


def track_llm_request(provider: str, model: str, status: str, duration: float,
                      prompt_tokens: int = 0, completion_tokens: int = 0):
    """
    Track LLM request metrics

    Args:
        provider: LLM provider (ollama, gemini)
        model: Model name
        status: Request status (success, error)
        duration: Request duration in seconds
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
    """
    llm_requests_total.labels(provider=provider, model=model, status=status).inc()
    llm_request_duration_seconds.labels(provider=provider, model=model).observe(duration)

    if prompt_tokens > 0:
        llm_tokens_total.labels(provider=provider, model=model, token_type='prompt').inc(prompt_tokens)
    if completion_tokens > 0:
        llm_tokens_total.labels(provider=provider, model=model, token_type='completion').inc(completion_tokens)


def track_db_query(operation: str, status: str, duration: float):
    """
    Track database query metrics

    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        status: Query status (success, error)
        duration: Query duration in seconds
    """
    db_queries_total.labels(operation=operation, status=status).inc()
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def track_cache_operation(operation: str, hit: bool):
    """
    Track cache operation metrics

    Args:
        operation: Cache operation (GET, SET, DELETE)
        hit: Whether it was a cache hit
    """
    result = 'hit' if hit else 'miss'
    cache_operations_total.labels(operation=operation, result=result).inc()


def track_qdrant_query(collection: str, status: str, duration: float):
    """
    Track Qdrant query metrics

    Args:
        collection: Collection name
        status: Query status (success, error)
        duration: Query duration in seconds
    """
    qdrant_queries_total.labels(collection=collection, status=status).inc()
    qdrant_query_duration_seconds.labels(collection=collection).observe(duration)


def update_health_metrics(api: bool = True, database: bool = True,
                          qdrant: bool = True, llm: bool = True):
    """
    Update health status metrics

    Args:
        api: API health status
        database: Database health status
        qdrant: Qdrant health status
        llm: LLM service health status
    """
    api_health.set(1 if api else 0)
    database_health.set(1 if database else 0)
    qdrant_health.set(1 if qdrant else 0)
    llm_health.set(1 if llm else 0)


class MetricsMiddleware:
    """
    Middleware to track HTTP request metrics
    """

    def __init__(self):
        pass

    async def __call__(self, request, call_next):
        """
        Track request metrics

        Args:
            request: FastAPI request
            call_next: Next middleware

        Returns:
            Response
        """
        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Track completed request
            track_http_request(method, endpoint, response.status_code, duration)

            return response

        except Exception as e:
            duration = time.time() - start_time
            # Track failed request
            track_http_request(method, endpoint, 500, duration)
            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def metrics_decorator(metric_type: str):
    """
    Decorator to automatically track metrics for functions

    Args:
        metric_type: Type of metric (graphrag, search, llm, db, qdrant)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Track success metrics based on type
                if metric_type == 'graphrag':
                    track_graphrag_query('success', duration, 0)
                elif metric_type == 'search':
                    search_type = kwargs.get('search_type', 'unknown')
                    track_search_query(search_type, 'success', duration, 0)
                elif metric_type == 'llm':
                    provider = kwargs.get('provider', 'unknown')
                    model = kwargs.get('model', 'unknown')
                    track_llm_request(provider, model, 'success', duration)
                elif metric_type == 'db':
                    operation = kwargs.get('operation', 'SELECT')
                    track_db_query(operation, 'success', duration)
                elif metric_type == 'qdrant':
                    collection = kwargs.get('collection', 'unknown')
                    track_qdrant_query(collection, 'success', duration)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Track error metrics based on type
                if metric_type == 'graphrag':
                    track_graphrag_query('error', duration, 0)
                elif metric_type == 'search':
                    search_type = kwargs.get('search_type', 'unknown')
                    track_search_query(search_type, 'error', duration, 0)
                elif metric_type == 'llm':
                    provider = kwargs.get('provider', 'unknown')
                    model = kwargs.get('model', 'unknown')
                    track_llm_request(provider, model, 'error', duration)
                elif metric_type == 'db':
                    operation = kwargs.get('operation', 'SELECT')
                    track_db_query(operation, 'error', duration)
                elif metric_type == 'qdrant':
                    collection = kwargs.get('collection', 'unknown')
                    track_qdrant_query(collection, 'error', duration)

                raise

        return wrapper
    return decorator
