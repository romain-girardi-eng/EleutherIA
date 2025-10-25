"""
Sentry Error Tracking Configuration
Captures and reports errors for monitoring and debugging
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
import os
from typing import Optional


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> None:
    """
    Initialize Sentry error tracking

    Args:
        dsn: Sentry DSN (Data Source Name). If None, reads from SENTRY_DSN env var
        environment: Environment name (production, staging, development)
        traces_sample_rate: Percentage of transactions to sample (0.0 to 1.0)
        profiles_sample_rate: Percentage of profiles to sample (0.0 to 1.0)
    """
    # Get DSN from parameter or environment variable
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")

    # Only initialize if DSN is provided
    if not sentry_dsn:
        print("⚠️  Sentry DSN not provided - error tracking disabled")
        return

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=os.getenv("RELEASE_VERSION", "1.0.0"),
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                AsyncioIntegration(),
            ],
            # Send default PII (Personally Identifiable Information)
            send_default_pii=False,
            # Attach stack trace to messages
            attach_stacktrace=True,
            # Maximum breadcrumbs
            max_breadcrumbs=50,
            # Before send callback to filter events
            before_send=before_send_filter,
        )

        print(f"✅ Sentry initialized for environment: {environment}")

    except Exception as e:
        print(f"❌ Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """
    Filter Sentry events before sending

    Args:
        event: Sentry event dictionary
        hint: Additional context

    Returns:
        Modified event or None to drop the event
    """
    # Filter out specific errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Don't report certain errors
        if isinstance(exc_value, (KeyboardInterrupt,)):
            return None

        # Don't report 404 errors
        if hasattr(exc_value, 'status_code') and exc_value.status_code == 404:
            return None

    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['api_version'] = '1.0.0'

    return event


def capture_exception(
    error: Exception,
    context: dict = None,
    level: str = "error"
) -> Optional[str]:
    """
    Capture and report an exception to Sentry

    Args:
        error: Exception to capture
        context: Additional context dictionary
        level: Error level (error, warning, info)

    Returns:
        Event ID or None
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            # Add context to the scope
            for key, value in context.items():
                scope.set_context(key, value)

            # Set level
            scope.level = level

            # Capture the exception
            return sentry_sdk.capture_exception(error)
    else:
        return sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: str = "info",
    context: dict = None
) -> Optional[str]:
    """
    Capture and report a message to Sentry

    Args:
        message: Message to capture
        level: Message level (error, warning, info)
        context: Additional context dictionary

    Returns:
        Event ID or None
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            # Add context to the scope
            for key, value in context.items():
                scope.set_context(key, value)

            # Set level
            scope.level = level

            # Capture the message
            return sentry_sdk.capture_message(message, level=level)
    else:
        return sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str, email: str = None, username: str = None):
    """
    Set user context for Sentry events

    Args:
        user_id: User ID
        email: User email (optional)
        username: Username (optional)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def set_transaction_name(name: str):
    """
    Set transaction name for performance monitoring

    Args:
        name: Transaction name
    """
    with sentry_sdk.configure_scope() as scope:
        scope.transaction = name


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict = None
):
    """
    Add a breadcrumb to track user actions

    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Severity level
        data: Additional data dictionary
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def start_transaction(name: str, op: str = "function") -> sentry_sdk.tracing.Transaction:
    """
    Start a performance monitoring transaction

    Args:
        name: Transaction name
        op: Operation type

    Returns:
        Transaction object
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def capture_graphrag_error(
    query: str,
    error: Exception,
    user_id: str = None,
    nodes_retrieved: int = 0
):
    """
    Capture a GraphRAG-specific error

    Args:
        query: User query
        error: Exception that occurred
        user_id: User ID (if authenticated)
        nodes_retrieved: Number of nodes retrieved before error
    """
    context = {
        "graphrag": {
            "query": query[:200],  # Truncate long queries
            "nodes_retrieved": nodes_retrieved,
            "user_id": user_id or "anonymous"
        }
    }

    capture_exception(error, context=context, level="error")
    add_breadcrumb(
        message=f"GraphRAG query failed: {query[:50]}...",
        category="graphrag",
        level="error",
        data={"nodes_retrieved": nodes_retrieved}
    )


def capture_search_error(
    search_type: str,
    query: str,
    error: Exception
):
    """
    Capture a search-specific error

    Args:
        search_type: Type of search (fulltext, semantic, hybrid)
        query: Search query
        error: Exception that occurred
    """
    context = {
        "search": {
            "type": search_type,
            "query": query[:200]
        }
    }

    capture_exception(error, context=context, level="error")
    add_breadcrumb(
        message=f"{search_type} search failed: {query[:50]}...",
        category="search",
        level="error"
    )


def capture_llm_error(
    provider: str,
    model: str,
    error: Exception,
    prompt_length: int = 0
):
    """
    Capture an LLM-specific error

    Args:
        provider: LLM provider (ollama, gemini)
        model: Model name
        error: Exception that occurred
        prompt_length: Length of the prompt
    """
    context = {
        "llm": {
            "provider": provider,
            "model": model,
            "prompt_length": prompt_length
        }
    }

    capture_exception(error, context=context, level="error")
    add_breadcrumb(
        message=f"LLM generation failed: {provider}/{model}",
        category="llm",
        level="error",
        data={"prompt_length": prompt_length}
    )


def capture_database_error(
    operation: str,
    table: str,
    error: Exception,
    query: str = None
):
    """
    Capture a database-specific error

    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        error: Exception that occurred
        query: SQL query (optional, will be sanitized)
    """
    context = {
        "database": {
            "operation": operation,
            "table": table,
            "query": query[:200] if query else None
        }
    }

    capture_exception(error, context=context, level="error")
    add_breadcrumb(
        message=f"Database {operation} failed on {table}",
        category="database",
        level="error"
    )
