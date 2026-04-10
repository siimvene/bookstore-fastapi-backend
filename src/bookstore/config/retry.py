from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import structlog
from sqlalchemy.exc import OperationalError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from bookstore.config.settings import get_settings

logger = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Any])

RECOVERABLE_SQLSTATES = frozenset({
    "08000",  # connection_exception
    "08001",  # sqlclient_unable_to_establish_sqlconnection
    "08003",  # connection_does_not_exist
    "08004",  # sqlserver_rejected_establishment_of_sqlconnection
    "08006",  # connection_failure
    "57P01",  # admin_shutdown
    "57P02",  # crash_shutdown
    "57P03",  # cannot_connect_now
    "25006",  # read_only_sql_transaction
})


def is_recoverable(exc: BaseException) -> bool:
    if isinstance(exc, OperationalError) and exc.orig is not None:
        pgcode = getattr(exc.orig, "pgcode", None) or getattr(exc.orig, "sqlstate", None)
        if pgcode and pgcode in RECOVERABLE_SQLSTATES:
            return True
    return False


def db_retry(func: F) -> F:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        settings = get_settings()
        retrying = retry(
            retry=retry_if_exception(is_recoverable),
            stop=stop_after_attempt(settings.retry_max_attempts),
            wait=wait_exponential(
                multiplier=settings.retry_multiplier,
                min=settings.retry_initial_backoff_ms / 1000,
                max=settings.retry_max_backoff_ms / 1000,
            ),
            before_sleep=lambda retry_state: logger.warning(
                "db_retry_attempt",
                attempt=retry_state.attempt_number,
                wait=retry_state.next_action.sleep if retry_state.next_action else 0,
            ),
            reraise=True,
        )
        return await retrying(func)(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
