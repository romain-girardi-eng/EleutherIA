"""
Structured Logging Configuration
Uses structlog for JSON-formatted, structured logging
"""
import structlog
import logging
import sys
from typing import Any, Dict


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for the application

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests with structured data
    """

    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger

    async def log_request(self, request, call_next):
        """
        Log incoming HTTP request and response

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        import time

        # Extract request info
        request_id = request.headers.get("X-Request-ID", "unknown")
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Log request start
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
        )

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful response
            self.logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            self.logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=round(duration, 3),
                exc_info=True,
            )

            raise


def log_service_operation(
    logger: structlog.BoundLogger,
    operation: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Log a service operation with structured context

    Args:
        logger: Structured logger instance
        operation: Operation name
        **kwargs: Additional context fields

    Returns:
        Context dictionary for further logging
    """
    context = {
        "operation": operation,
        **kwargs
    }

    logger.info("service_operation", **context)
    return context


def log_graphrag_query(
    logger: structlog.BoundLogger,
    query: str,
    user_id: str,
    **kwargs: Any
) -> None:
    """
    Log a GraphRAG query with structured data

    Args:
        logger: Structured logger instance
        query: User query
        user_id: User ID
        **kwargs: Additional context
    """
    logger.info(
        "graphrag_query",
        query=query[:200],  # Truncate long queries
        user_id=user_id,
        **kwargs
    )


def log_search_operation(
    logger: structlog.BoundLogger,
    search_type: str,
    query: str,
    results_count: int,
    duration: float,
    **kwargs: Any
) -> None:
    """
    Log a search operation

    Args:
        logger: Structured logger instance
        search_type: Type of search (fulltext, semantic, hybrid)
        query: Search query
        results_count: Number of results
        duration: Operation duration in seconds
        **kwargs: Additional context
    """
    logger.info(
        "search_operation",
        search_type=search_type,
        query=query[:200],
        results_count=results_count,
        duration_seconds=round(duration, 3),
        **kwargs
    )


def log_database_operation(
    logger: structlog.BoundLogger,
    operation: str,
    table: str,
    duration: float,
    rows_affected: int = 0,
    **kwargs: Any
) -> None:
    """
    Log a database operation

    Args:
        logger: Structured logger instance
        operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration: Operation duration in seconds
        rows_affected: Number of rows affected
        **kwargs: Additional context
    """
    logger.info(
        "database_operation",
        operation=operation,
        table=table,
        duration_seconds=round(duration, 3),
        rows_affected=rows_affected,
        **kwargs
    )


def log_llm_generation(
    logger: structlog.BoundLogger,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration: float,
    **kwargs: Any
) -> None:
    """
    Log an LLM generation operation

    Args:
        logger: Structured logger instance
        provider: LLM provider (ollama, gemini)
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        duration: Operation duration in seconds
        **kwargs: Additional context
    """
    logger.info(
        "llm_generation",
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        duration_seconds=round(duration, 3),
        **kwargs
    )


def log_cache_operation(
    logger: structlog.BoundLogger,
    operation: str,
    cache_key: str,
    hit: bool,
    **kwargs: Any
) -> None:
    """
    Log a cache operation

    Args:
        logger: Structured logger instance
        operation: Operation type (GET, SET, DELETE)
        cache_key: Cache key
        hit: Whether it was a cache hit
        **kwargs: Additional context
    """
    logger.info(
        "cache_operation",
        operation=operation,
        cache_key=cache_key,
        cache_hit=hit,
        **kwargs
    )
