"""Tests for tonewinner-rs232."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from tonewinner_rs232 import (
    TonewinnerReceiver,
    parse_input_source,
    parse_mute_status,
    parse_power_status,
    parse_sound_mode,
    parse_volume_status,
)


class TestProtocolParsing:
    """Tests for protocol message parsing."""

    def test_parse_power_on(self) -> None:
        """Test parsing a POWER ON message."""
        assert parse_power_status("POWER ON") is True

    def test_parse_power_off(self) -> None:
        """Test parsing a POWER OFF message."""
        assert parse_power_status("POWER OFF") is False

    def test_parse_power_not_power_message(self) -> None:
        """Test parsing a non-power message returns None."""
        assert parse_power_status("VOL 50.0") is None

    def test_parse_volume(self) -> None:
        """Test parsing volume messages."""
        assert parse_volume_status("VOL 50.0") == 50.0
        assert parse_volume_status("VOL 80.0") == 80.0

    def test_parse_volume_not_volume_message(self) -> None:
        """Test parsing a non-volume message returns None."""
        assert parse_volume_status("POWER ON") is None

    def test_parse_mute_on(self) -> None:
        """Test parsing a MUTE ON message."""
        assert parse_mute_status("MUTE ON") is True

    def test_parse_mute_off(self) -> None:
        """Test parsing a MUTE OFF message."""
        assert parse_mute_status("MUTE OFF") is False

    def test_parse_mute_not_mute_message(self) -> None:
        """Test parsing a non-mute message returns None."""
        assert parse_mute_status("POWER ON") is None

    def test_parse_input_source_with_av(self) -> None:
        """Test parsing an input source with V= and A= fields."""
        result = parse_input_source("SI 01 HDMI 1 V=HD1 A=HDMI")
        assert result == ("HDMI 1", "HDMI", "HD1")

    def test_parse_input_source_simple(self) -> None:
        """Test parsing a simple input source without V=/A= fields."""
        result = parse_input_source("SI CO1")
        assert result == ("CO1", None, None)

    def test_parse_input_source_not_source_message(self) -> None:
        """Test parsing a non-source message returns None."""
        assert parse_input_source("POWER ON") is None

    def test_parse_sound_mode(self) -> None:
        """Test parsing a STEREO sound mode message."""
        result = parse_sound_mode("MODE STEREO")
        assert result == ("STEREO", "Stereo")

    def test_parse_sound_mode_firmware_bug(self) -> None:
        """Test parsing the DITECT firmware bug variant maps to Direct."""
        result = parse_sound_mode("MODE DITECT")
        assert result == ("DITECT", "Direct")

    def test_parse_sound_mode_not_mode_message(self) -> None:
        """Test parsing a non-mode message returns None."""
        assert parse_sound_mode("POWER ON") is None


class TestReceiver:
    """Tests for the TonewinnerReceiver class."""

    async def test_connect_disconnect(self, mock_serial) -> None:
        """Test connecting and disconnecting."""
        receiver = TonewinnerReceiver("/dev/mock")

        open_conn = AsyncMock(return_value=(mock_serial.reader, mock_serial.writer))
        with patch("serialx.open_serial_connection", open_conn):
            await receiver.connect()
            assert receiver.connected is True

            await receiver.disconnect()
            assert receiver.connected is False

    async def test_power_on_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test power_on sends correct command."""
        await receiver.power_on()
        written = mock_serial.get_written()
        assert any(b"POWER ON" in w for w in written)

    async def test_power_off_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test power_off sends correct command."""
        await receiver.power_off()
        written = mock_serial.get_written()
        assert any(b"POWER OFF" in w for w in written)

    async def test_set_volume_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test set_volume sends correct command."""
        await receiver.set_volume(50.0)
        written = mock_serial.get_written()
        assert any(b"VOL" in w for w in written)

    async def test_mute_on_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test mute_on sends correct command."""
        await receiver.mute_on()
        written = mock_serial.get_written()
        assert any(b"MUTE ON" in w for w in written)

    async def test_mute_off_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test mute_off sends correct command."""
        await receiver.mute_off()
        written = mock_serial.get_written()
        assert any(b"MUTE OFF" in w for w in written)

    async def test_select_source_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test select_source sends correct command."""
        await receiver.select_source("HD1")
        written = mock_serial.get_written()
        assert any(b"SI HD1" in w for w in written)

    async def test_select_sound_mode_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test select_sound_mode sends correct command."""
        await receiver.select_sound_mode("STEREO")
        written = mock_serial.get_written()
        assert any(b"MODE STEREO" in w for w in written)

    async def test_power_state_update(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that incoming power messages update state."""
        mock_serial.inject_response("POWER ON")
        await asyncio.sleep(0.1)
        assert receiver.state.power is True

        mock_serial.inject_response("POWER OFF")
        await asyncio.sleep(0.1)
        assert receiver.state.power is False

    async def test_volume_state_update(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that incoming volume messages update state."""
        mock_serial.inject_response("VOL 35.5")
        await asyncio.sleep(0.1)
        assert receiver.state.volume == 35.5

    async def test_mute_state_update(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that incoming mute messages update state."""
        mock_serial.inject_response("MUTE ON")
        await asyncio.sleep(0.1)
        assert receiver.state.mute is True

    async def test_source_state_update(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that incoming source messages update state."""
        mock_serial.inject_response("SI 01 HDMI 1 V=HD1 A=HDMI")
        await asyncio.sleep(0.1)
        assert receiver.state.source_name == "HDMI 1"
        assert receiver.state.audio_source == "HDMI"

    async def test_sound_mode_state_update(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that incoming sound mode messages update state."""
        mock_serial.inject_response("MODE STEREO")
        await asyncio.sleep(0.1)
        assert receiver.state.sound_mode == "STEREO"
        assert receiver.state.sound_mode_label == "Stereo"

    async def test_subscriber_called_on_state_change(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that subscribers are notified on state change."""
        states: list = []
        receiver.subscribe(lambda s: states.append(s))

        mock_serial.inject_response("POWER ON")
        await asyncio.sleep(0.1)

        assert len(states) >= 1
        assert states[0] is not None
        assert states[0].power is True

    async def test_subscriber_called_on_disconnect(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that subscribers receive None on disconnect."""
        states: list = []
        receiver.subscribe(lambda s: states.append(s))

        mock_serial.feed_eof()
        await asyncio.sleep(0.1)

        assert any(s is None for s in states)

    async def test_unsubscribe(self, receiver: TonewinnerReceiver, mock_serial) -> None:
        """Test that unsubscribe removes the callback."""
        states: list = []
        unsub = receiver.subscribe(lambda s: states.append(s))
        unsub()

        mock_serial.inject_response("POWER ON")
        await asyncio.sleep(0.1)

        assert len(states) == 0

    async def test_command_framing(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that commands use ##...* framing."""
        await receiver.power_on()
        written = mock_serial.get_written()
        assert any(b"##POWER ON*" in w for w in written)

    async def test_message_framing_single(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test parsing a single framed message."""
        mock_serial.inject_response("POWER ON")
        await asyncio.sleep(0.1)
        assert receiver.state.power is True

    async def test_message_framing_multiple(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test parsing multiple messages in one frame."""
        mock_serial.inject_raw(b"#POWER ON*#VOL 50.0*")
        await asyncio.sleep(0.1)
        assert receiver.state.power is True
        assert receiver.state.volume == 50.0

    async def test_message_framing_garbage_before(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test parsing with garbage data before valid message."""
        mock_serial.inject_raw(b"\xff\x00junk##POWER ON*")
        await asyncio.sleep(0.1)
        assert receiver.state.power is True

    async def test_send_command(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test send_command method (used for raw commands)."""
        await receiver.send_command("CUSTOM CMD")
        written = mock_serial.get_written()
        assert any(b"##CUSTOM CMD*" in w for w in written)

    async def test_query_timeout_cleans_up_pending(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that a timed-out query removes its pending entry."""
        _real_wait_for = asyncio.wait_for

        async def fast_wait_for(fut, timeout):
            return await _real_wait_for(fut, timeout=0.01)

        with (
            patch(
                "tonewinner_rs232.receiver.asyncio.wait_for", side_effect=fast_wait_for
            ),
            pytest.raises(
                ConnectionError, match="No response for POWER query within timeout"
            ),
        ):
            await receiver.query_power()

        assert len(receiver._pending_queries) == 0  # noqa: SLF001

    async def test_query_after_timeout_receives_response(
        self,
        receiver: TonewinnerReceiver,
        mock_serial,
    ) -> None:
        """Test that a query after a timeout still receives its response."""
        _real_wait_for = asyncio.wait_for

        async def fast_wait_for(fut, timeout):
            return await _real_wait_for(fut, timeout=0.01)

        with patch(
            "tonewinner_rs232.receiver.asyncio.wait_for", side_effect=fast_wait_for
        ):
            # First query times out, leaving no stale entry
            with pytest.raises(ConnectionError):
                await receiver.query_power()

            # Second query should work normally
            query_task = asyncio.create_task(receiver.query_power())
            await asyncio.sleep(0)  # Let the task send the command
            mock_serial.inject_response("POWER ON")
            result = await query_task

        assert result is True
