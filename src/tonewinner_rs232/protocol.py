"""Tonewinner RS232 protocol utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .const import (
    COMMAND_START,
    COMMAND_TERMINATOR,
    INPUT_SOURCE_NAMES,
    SOUND_MODE_LABELS,
)


# Power commands
CMD_POWER_ON = "POWER ON"
CMD_POWER_OFF = "POWER OFF"
CMD_POWER_QUERY = "POWER ?"

# Volume commands
CMD_VOLUME_UP = "VOL UP"
CMD_VOLUME_DOWN = "VOL DN"
CMD_VOLUME_QUERY = "VOL ?"

# Mute commands
CMD_MUTE_ON = "MUTE ON"
CMD_MUTE_OFF = "MUTE OFF"
CMD_MUTE_QUERY = "MUTE ?"

# Input source commands
CMD_INPUT_NEXT = "SI UP"
CMD_INPUT_PREV = "SI DN"
CMD_INPUT_QUERY = "SI ?"

# Sound mode commands
CMD_MODE_QUERY = "MODE ?"


def build_command(command: str) -> bytes:
    """Build a complete framed command for the RS232 protocol.

    Wraps a plain command string in the ##...* framing markers.
    """
    return f"{COMMAND_START}{command}{COMMAND_TERMINATOR}".encode("ascii")


def build_volume_command(level: float) -> bytes:
    """Build a volume set command (level 0.0-80.0)."""
    return build_command(f"VOL {level:.1f}")


def build_source_command(source_code: str) -> bytes:
    """Build an input source selection command."""
    return build_command(f"SI {source_code}")


def build_mode_command(mode_code: str) -> bytes:
    """Build a sound mode selection command."""
    return build_command(f"MODE {mode_code}")


def parse_power_status(message: str) -> bool | None:
    """Parse power status from a device response message.

    Returns True for ON, False for OFF, None if not a power message.
    """
    if not message or not message.startswith("POWER"):
        return None
    return message[6:8] == "ON"


def parse_volume_status(message: str) -> float | None:
    """Parse volume level (0-80) from a device response message.

    Returns the volume as float, or None if not a volume message.
    """
    if not message or not message.startswith("VOL"):
        return None
    try:
        return float(message[4:8])
    except (ValueError, IndexError):
        return None


def parse_mute_status(message: str) -> bool | None:
    """Parse mute status from a device response message.

    Returns True if muted, False if not, None if not a mute message.
    """
    if not message or not message.startswith("MUTE"):
        return None
    return message[5:7] == "ON"


def parse_input_source(message: str) -> tuple[str, str | None, str | None] | None:
    """Parse input source from a device response message.

    Returns (source_name, audio_source, video_source) or None.
    """
    if not message or not message.startswith("SI"):
        return None

    # Format: "SI XX source_name V=video A=audio" or "SI source_code"
    rest = message[3:]
    if len(rest) > 3 and rest[:2].isdigit() and rest[2] == " ":
        source = rest[3:]
    else:
        source = rest

    match = re.search(r"(?P<name>.+) V=(?P<video>\w+) A=(?P<audio>\w+)$", source)
    if match:
        return (
            match.group("name"),
            match.group("audio"),
            match.group("video"),
        )

    source_stripped = source.strip()
    if source_stripped:
        return source_stripped, None, None

    return None


def parse_sound_mode(message: str) -> tuple[str, str] | None:
    """Parse sound mode from a device response message.

    Returns (mode_code, mode_label) or None.
    """
    if not message or not message.startswith("MODE"):
        return None

    mode_code = message[5:]
    label = SOUND_MODE_LABELS.get(mode_code, f"Unknown ({mode_code})")
    return mode_code, label


def resolve_source_name(source_code: str) -> str:
    """Resolve a source code to its display name."""
    return INPUT_SOURCE_NAMES.get(source_code, source_code)


@dataclass
class PendingQuery:
    """An in-flight query awaiting a response from the receiver."""

    prefix: str
    future: "asyncio.Future[str]" = field()
