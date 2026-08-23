"""Receiver state dataclass."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, replace


@dataclass
class ReceiverInfo:
    """Device identity information reported by the VER command.

    Fields are None when not present or unparseable in the response.
    """

    model: str | None = None
    firmware: str | None = None
    date: datetime.datetime | None = None


@dataclass
class ReceiverState:
    """Complete state snapshot for a Tonewinner receiver.

    All fields are None until first populated by query_state().
    """

    power: bool | None = None
    volume: float | None = None
    mute: bool | None = None
    source: str | None = None
    source_name: str | None = None
    audio_source: str | None = None
    video_source: str | None = None
    sound_mode: str | None = None
    sound_mode_label: str | None = None

    def copy(self) -> ReceiverState:
        """Return a shallow copy of this state."""
        return replace(self)
