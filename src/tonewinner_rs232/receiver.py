"""Tonewinner RS232 receiver client."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable

import serialx

from .const import (
    DEFAULT_BAUDRATE,
    DEFAULT_READ_TIMEOUT,
)
from .protocol import (
    CMD_INPUT_QUERY,
    CMD_MODE_QUERY,
    CMD_MUTE_OFF,
    CMD_MUTE_ON,
    CMD_MUTE_QUERY,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_POWER_QUERY,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_QUERY,
    CMD_VOLUME_UP,
    PendingQuery,
    build_command,
    build_source_command,
    build_volume_command,
    parse_input_source,
    parse_mute_status,
    parse_power_status,
    parse_sound_mode,
    parse_volume_status,
)
from .state import ReceiverState

_LOGGER = logging.getLogger(__name__)

type StateCallback = Callable[[ReceiverState | None], None]
"""Callback signature for state change subscriptions.

Receives the updated state, or None when disconnected.
"""


class TonewinnerReceiver:
    """Async client for a Tonewinner AV processor over RS232 serial."""

    def __init__(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> None:
        """Initialize the Tonewinner receiver client.

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0).
            baudrate: Baud rate for serial communication.

        """
        self._port = port
        self._baudrate = baudrate
        self._reader: asyncio.StreamReader | None = None
        self._writer: serialx.SerialStreamWriter | None = None
        self._state = ReceiverState()
        self._subscribers: list[StateCallback] = []
        self._pending_queries: list[PendingQuery] = []
        self._read_task: asyncio.Task[None] | None = None
        self._batching = False
        self._batch_changed = False

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> ReceiverState:
        """Current receiver state snapshot."""
        return self._state

    @property
    def connected(self) -> bool:
        """Whether the serial connection is active."""
        return self._writer is not None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the serial connection and start the read loop."""
        if self.connected:
            return

        _LOGGER.debug("Connecting to %s at %d baud", self._port, self._baudrate)
        self._reader, self._writer = await serialx.open_serial_connection(
            self._port,
            baudrate=self._baudrate,
            read_timeout=DEFAULT_READ_TIMEOUT,
        )
        self._read_task = asyncio.create_task(self._read_loop())
        _LOGGER.info("Connected to %s", self._port)

    async def disconnect(self) -> None:
        """Close the serial connection."""
        if not self.connected:
            return

        _LOGGER.debug("Disconnecting from %s", self._port)
        if self._read_task:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        if self._writer:
            self._writer.close()
            self._reader = None
            self._writer = None

        self._notify(None)
        _LOGGER.info("Disconnected from %s", self._port)

    # ------------------------------------------------------------------
    # State query
    # ------------------------------------------------------------------

    async def query_state(self) -> ReceiverState:
        """Query all device state and return the updated snapshot."""
        self._batching = True
        self._batch_changed = False
        try:
            await self._send_command(CMD_POWER_QUERY)
            await asyncio.sleep(0.3)
            await self._send_command(CMD_VOLUME_QUERY)
            await asyncio.sleep(0.3)
            await self._send_command(CMD_MUTE_QUERY)
            await asyncio.sleep(0.3)
            await self._send_command(CMD_INPUT_QUERY)
            await asyncio.sleep(0.3)
            await self._send_command(CMD_MODE_QUERY)
            # Give the receiver time to respond to the last command
            await asyncio.sleep(0.3)
        finally:
            self._batching = False
            if self._batch_changed:
                self._notify(self._state.copy())
        return self._state

    # ------------------------------------------------------------------
    # Event subscription
    # ------------------------------------------------------------------

    def subscribe(self, callback: StateCallback) -> Callable[[], None]:
        """Subscribe to state changes.

        Returns an unsubscribe function.
        """
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    # ------------------------------------------------------------------
    # Power
    # ------------------------------------------------------------------

    async def power_on(self) -> None:
        """Turn the receiver on."""
        await self._send_command(CMD_POWER_ON)

    async def power_off(self) -> None:
        """Turn the receiver off."""
        await self._send_command(CMD_POWER_OFF)

    async def query_power(self) -> bool | None:
        """Query and return the current power state."""
        response = await self._query(CMD_POWER_QUERY, "POWER")
        return parse_power_status(response)

    # ------------------------------------------------------------------
    # Volume
    # ------------------------------------------------------------------

    async def set_volume(self, level: float) -> None:
        """Set master volume (0.0-80.0)."""
        await self._send_command(build_volume_command(level))

    async def volume_up(self) -> None:
        """Increase volume by one step."""
        await self._send_command(CMD_VOLUME_UP)

    async def volume_down(self) -> None:
        """Decrease volume by one step."""
        await self._send_command(CMD_VOLUME_DOWN)

    async def query_volume(self) -> float | None:
        """Query and return the current volume level (0-80)."""
        response = await self._query(CMD_VOLUME_QUERY, "VOL")
        return parse_volume_status(response)

    # ------------------------------------------------------------------
    # Mute
    # ------------------------------------------------------------------

    async def mute_on(self) -> None:
        """Mute the receiver."""
        await self._send_command(CMD_MUTE_ON)

    async def mute_off(self) -> None:
        """Unmute the receiver."""
        await self._send_command(CMD_MUTE_OFF)

    async def query_mute(self) -> bool | None:
        """Query and return the current mute state."""
        response = await self._query(CMD_MUTE_QUERY, "MUTE")
        return parse_mute_status(response)

    # ------------------------------------------------------------------
    # Input source
    # ------------------------------------------------------------------

    async def select_source(self, source_code: str) -> None:
        """Select an input source by code (e.g. 'HD1', 'BT')."""
        await self._send_command(build_source_command(source_code))

    async def query_source(self) -> tuple[str, str | None, str | None] | None:
        """Query and return the current input source.

        Returns (source_name, audio_source, video_source) or None.
        """
        response = await self._query(CMD_INPUT_QUERY, "SI")
        return parse_input_source(response)

    # ------------------------------------------------------------------
    # Sound mode
    # ------------------------------------------------------------------

    async def select_sound_mode(self, mode_code: str) -> None:
        """Select a sound mode by code (e.g. 'STEREO', 'DIRECT')."""
        await self._send_command(build_command(f"MODE {mode_code}"))

    async def query_sound_mode(self) -> tuple[str, str] | None:
        """Query and return the current sound mode.

        Returns (mode_code, mode_label) or None.
        """
        response = await self._query(CMD_MODE_QUERY, "MODE")
        return parse_sound_mode(response)

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------

    async def send_command(self, command: str) -> None:
        """Send a raw command string to the receiver.

        The command is automatically wrapped in the ##...* protocol framing.
        """
        await self._send_command(command)

    # ------------------------------------------------------------------
    # Internal: command sending
    # ------------------------------------------------------------------

    async def _send_command(self, command: str | bytes) -> None:
        """Send a command to the receiver."""
        if not self._writer:
            msg = "Not connected"
            raise ConnectionError(msg)

        data = build_command(command) if isinstance(command, str) else command

        _LOGGER.debug("TX: %s", data.hex())
        self._writer.write(data)
        await self._writer.drain()

    async def _query(self, command: str, prefix: str) -> str:
        """Send a query and wait for the matching response."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        pending = PendingQuery(prefix=prefix, future=future)
        self._pending_queries.append(pending)
        await self._send_command(command)
        try:
            return await asyncio.wait_for(future, timeout=3.0)
        except TimeoutError:
            msg = f"No response for {prefix} query within timeout"
            raise ConnectionError(
                msg,
            ) from None
        finally:
            if pending in self._pending_queries:
                self._pending_queries.remove(pending)

    # ------------------------------------------------------------------
    # Internal: read loop and message processing
    # ------------------------------------------------------------------

    async def _read_loop(self) -> None:
        """Read and parse framed messages from the serial port."""
        buffer = b""
        while self._reader:
            try:
                data = await self._reader.read(256)
            except OSError:
                _LOGGER.debug("Read error, connection lost")
                break

            if not data:
                _LOGGER.debug("Empty read, connection closed")
                break

            _LOGGER.debug("RX: %s", data.hex())
            buffer += data

            while True:
                start = buffer.find(b"#")
                if start == -1:
                    buffer = b""
                    break
                # Skip any number of consecutive # markers
                content_start = start
                while content_start < len(buffer) and buffer[content_start : content_start + 1] == b"#":
                    content_start += 1
                end = buffer.find(b"*", start)
                if end == -1:
                    buffer = buffer[start:]
                    break
                message_bytes = buffer[content_start : end]
                if message_bytes:
                    message = message_bytes.decode("ascii", errors="ignore")
                    self._process_message(message)
                buffer = buffer[end + 1 :]

        await self.disconnect()

    def _process_message(self, message: str) -> None:
        """Process a single framed message from the receiver."""
        _LOGGER.debug("MSG: %s", message)
        changed = self._update_state(message)
        self._resolve_pending_queries(message)
        if changed and not self._batching:
            self._notify(self._state.copy())
        elif changed and self._batching:
            self._batch_changed = True

    def _update_state(self, message: str) -> bool:  # noqa: C901
        """Update receiver state from a message. Returns True if anything changed."""
        changed = False

        if (
            power := parse_power_status(message)
        ) is not None and self._state.power != power:
            self._state.power = power
            changed = True

        if (
            volume := parse_volume_status(message)
        ) is not None and self._state.volume != volume:
            self._state.volume = volume
            changed = True

        if (
            mute := parse_mute_status(message)
        ) is not None and self._state.mute != mute:
            self._state.mute = mute
            changed = True

        if (source := parse_input_source(message)) is not None:
            source_name, audio_source, video_source = source
            if self._state.source_name != source_name:
                self._state.source_name = source_name
                changed = True
            if self._state.audio_source != audio_source:
                self._state.audio_source = audio_source
                changed = True
            if self._state.video_source != video_source:
                self._state.video_source = video_source
                changed = True

        if (mode := parse_sound_mode(message)) is not None:
            mode_code, mode_label = mode
            if self._state.sound_mode != mode_code:
                self._state.sound_mode = mode_code
                changed = True
            if self._state.sound_mode_label != mode_label:
                self._state.sound_mode_label = mode_label
                changed = True

        return changed

    def _resolve_pending_queries(self, message: str) -> None:
        """Resolve any pending queries that match this message."""
        for pq in list(self._pending_queries):
            if message.startswith(pq.prefix):
                self._pending_queries.remove(pq)
                if not pq.future.done():
                    pq.future.set_result(message)
                break

    def _notify(self, state: ReceiverState | None) -> None:
        """Notify all subscribers of a state change."""
        for callback in self._subscribers:
            try:
                callback(state)
            except Exception:
                _LOGGER.exception("Error in subscriber callback")
