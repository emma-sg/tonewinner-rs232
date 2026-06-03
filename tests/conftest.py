"""Test fixtures for tonewinner-rs232."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tonewinner_rs232 import TonewinnerReceiver


class MockSerialConnection:
    """Simulates a serialx open_serial_connection with a reader/writer pair."""

    def __init__(self) -> None:
        """Initialize the mock serial connection."""
        self._reader: asyncio.StreamReader | None = None
        self.writer = MagicMock()
        self.writer.write = MagicMock()
        self.writer.drain = AsyncMock()
        self.writer.close = MagicMock()

    @property
    def reader(self) -> asyncio.StreamReader:
        """Return the mock stream reader, creating it lazily."""
        if self._reader is None:
            self._reader = asyncio.StreamReader()
        return self._reader

    def inject_response(self, message: str) -> None:
        """Feed a response message into the reader.

        Device responses use single #...* framing (not ##).
        """
        framed = f"#{message}*".encode("ascii")
        self.reader.feed_data(framed)

    def inject_raw(self, data: bytes) -> None:
        """Feed raw bytes into the reader."""
        self.reader.feed_data(data)

    def feed_eof(self) -> None:
        """Signal EOF to the reader (simulates disconnect)."""
        self.reader.feed_eof()

    def get_written(self) -> list[bytes]:
        """Get all data written to the mock writer."""
        return [call[0][0] for call in self.writer.write.call_args_list]


@pytest.fixture
def mock_serial() -> MockSerialConnection:
    """Return a mock serial connection."""
    return MockSerialConnection()


@pytest.fixture
async def receiver(mock_serial: MockSerialConnection) -> TonewinnerReceiver:
    """Return a connected TonewinnerReceiver with a mock serial connection."""
    receiver = TonewinnerReceiver("/dev/mock")

    open_conn = AsyncMock(return_value=(mock_serial.reader, mock_serial.writer))
    with patch("serialx.open_serial_connection", open_conn):
        await receiver.connect()

    # Let the read loop task start
    await asyncio.sleep(0)

    yield receiver

    await receiver.disconnect()
