"""Constants and enums for the Tonewinner RS232 protocol."""

from enum import StrEnum


class InputSource(StrEnum):
    """Known input source codes for Tonewinner devices."""

    HDMI_1 = "HD1"
    HDMI_2 = "HD2"
    HDMI_3 = "HD3"
    HDMI_4 = "HD4"
    HDMI_5 = "HD5"
    HDMI_6 = "HD6"
    OPTICAL_1 = "OP1"
    OPTICAL_2 = "OP2"
    COAXIAL_1 = "CO1"
    COAXIAL_2 = "CO2"
    ANALOG_1 = "AN1"
    ANALOG_2 = "AN2"
    ANALOG_3 = "AN3"
    BLUETOOTH = "BT"
    USB = "USB"
    PC = "PC"
    HDMI_EARC = "ARC"


class SoundMode(StrEnum):
    """Known sound mode codes."""

    DIRECT = "DIRECT"
    DITECT = "DITECT"  # firmware bug in V1.02.0796
    PURE = "PURE"
    STEREO = "STEREO"
    ALL_STEREO = "ALLSTEREO"
    ALLSTREO = "ALLSTREO"  # firmware bug in V1.02.0796
    PRO_LOGIC_IIX_MOVIE = "PLIIMOVIE"
    PRO_LOGIC_IIX_MUSIC = "PLIIMUSIC"
    PRO_LOGIC_IIZ_HEIGHT = "PLIIHEIGHT"
    PRO_LOGIC_IIZ_HEIGHT_MOVIE = "PLIIHEIGHTMOVIE"
    PRO_LOGIC_IIZ_HEIGHT_MUSIC = "PLIIHEIGHTMUSIC"
    NEO6_CINEMA = "NEO6CINEMA"
    NEO6_MUSIC = "NEO6MUSIC"
    AUTO = "AUTO"


# Display labels for each sound mode code
SOUND_MODE_LABELS: dict[str, str] = {
    "DIRECT": "Direct",
    "DITECT": "Direct",
    "PURE": "Pure",
    "STEREO": "Stereo",
    "ALLSTEREO": "All Stereo",
    "ALLSTREO": "All Stereo",
    "PLIIMOVIE": "Pro Logic IIx Movie (Dolby Upmix)",
    "PLIIMUSIC": "Pro Logic IIx Music",
    "PLIIHEIGHT": "Pro Logic IIz Height",
    "PLIIHEIGHTMOVIE": "Pro Logic IIz Height Movie",
    "PLIIHEIGHTMUSIC": "Pro Logic IIz Height Music",
    "NEO6CINEMA": "Neo6:Cinema (DTS Neural)",
    "NEO6MUSIC": "Neo6:Music",
    "AUTO": "Auto",
}

# Display names for input source codes
INPUT_SOURCE_NAMES: dict[str, str] = {
    "HD1": "HDMI 1",
    "HD2": "HDMI 2",
    "HD3": "HDMI 3",
    "HD4": "HDMI 4",
    "HD5": "HDMI 5",
    "HD6": "HDMI 6",
    "OP1": "Optical 1",
    "OP2": "Optical 2",
    "CO1": "Coaxial 1",
    "CO2": "Coaxial 2",
    "AN1": "Analog 1",
    "AN2": "Analog 2",
    "AN3": "Analog 3",
    "BT": "Bluetooth",
    "USB": "USB",
    "PC": "PC",
    "ARC": "HDMI eARC",
}

# Protocol framing
COMMAND_START = "##"
COMMAND_TERMINATOR = "*"

# Default serial settings
DEFAULT_BAUDRATE = 9600
DEFAULT_READ_TIMEOUT = 1.0
