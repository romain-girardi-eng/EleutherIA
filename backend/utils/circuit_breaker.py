"""
Circuit Breaker Pattern Implementation
Prevents cascading failures by failing fast when services are unavailable
"""
from pybreaker import CircuitBreaker, CircuitBreakerError
from typing import Callable, Any
import time
from functools import wraps


# Circuit breakers for different services
llm_circuit_breaker = CircuitBreaker(
    fail_max=3,  # Open after 3 failures
    timeout_duration=60,  # Try again after 60 seconds
    name="LLM Service"
)

database_circuit_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    name="Database"
)

qdrant_circuit_breaker = CircuitBreaker(
    fail_max=3,
    timeout_duration=45,
    name="Qdrant"
)


def with_circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator to wrap function calls with circuit breaker

    Args:
        breaker: Circuit breaker instance

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await breaker.call_async(func, *args, **kwargs)
            except CircuitBreakerError:
                # Circuit is open, fail fast
                raise Exception(f"{breaker.name} circuit breaker is OPEN - service unavailable")
        return wrapper
    return decorator


# Example usage:
# @with_circuit_breaker(llm_circuit_breaker)
# async def call_llm(prompt: str):
#     return await llm_service.generate(prompt)
