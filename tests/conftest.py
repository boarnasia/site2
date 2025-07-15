import pytest
from loguru import logger


@pytest.fixture
def caplog(caplog):
    """Fixture to propagate loguru logs to pytest's caplog."""
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level="DEBUG",
        # Make sure to use the same handler as caplog
        enqueue=False,  # Or True if you use enqueue in your app
    )
    yield caplog
    logger.remove(handler_id)
