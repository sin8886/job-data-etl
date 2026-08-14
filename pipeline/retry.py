import logging
import time

logger = logging.getLogger(__name__)


def retry(
    func,
    *args,
    max_retries=3,
    base_delay=2,
    **kwargs,
):
    """
    Execute a function with retry and exponential backoff.

    Parameters
    ----------
    func : callable
        Function to execute.

    max_retries : int
        Maximum number of retry attempts after the initial attempt.

    base_delay : int or float
        Initial delay in seconds.
        The delay doubles after each failed attempt.

    Returns
    -------
    Any
        The return value of func.

    Raises
    ------
    Exception
        Re-raises the final exception if all attempts fail.
    """

    for attempt in range(max_retries + 1):

        try:

            logger.info(
                "Executing %s (attempt %d/%d)",
                func.__name__,
                attempt + 1,
                max_retries + 1,
            )

            return func(*args, **kwargs)

        except Exception:

            if attempt == max_retries:

                logger.exception(
                    "%s failed after %d attempts",
                    func.__name__,
                    max_retries + 1,
                )

                raise

            delay = base_delay * (2**attempt)

            logger.warning(
                "%s failed. Retry %d/%d after %s seconds.",
                func.__name__,
                attempt + 1,
                max_retries,
                delay,
            )

            time.sleep(delay)
