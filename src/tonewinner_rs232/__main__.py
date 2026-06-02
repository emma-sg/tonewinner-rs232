"""CLI entry point for testing the Tonewinner RS232 connection.

Usage:
    python -m tonewinner_rs232 /dev/ttyUSB0

Queries and prints the current receiver state.
"""

import argparse
import asyncio
import sys

from . import TonewinnerReceiver


async def _query(port: str, baudrate: int) -> None:
    receiver = TonewinnerReceiver(port, baudrate)
    try:
        await receiver.connect()
        await receiver.query_state()
        state = receiver.state
        print(f"Power:    {'ON' if state.power else 'OFF' if state.power is not None else 'Unknown'}")
        print(f"Volume:   {state.volume:.1f}" if state.volume is not None else "Volume:   Unknown")
        print(f"Mute:     {'ON' if state.mute else 'OFF' if state.mute is not None else 'Unknown'}")
        print(f"Source:   {state.source_name or 'Unknown'} (code: {state.source or '?'})")
        print(f"Sound:    {state.sound_mode_label or 'Unknown'}")
    finally:
        await receiver.disconnect()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Tonewinner RS232 CLI")
    parser.add_argument("port", help="Serial port path (e.g., /dev/ttyUSB0)")
    parser.add_argument(
        "-b", "--baudrate", type=int, default=9600, help="Baud rate (default: 9600)"
    )
    args = parser.parse_args()

    try:
        asyncio.run(_query(args.port, args.baudrate))
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
