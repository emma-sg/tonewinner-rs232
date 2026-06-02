"""Receiver state dataclass."""

from __future__ import annotations

from dataclasses import dataclass, replace


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
