# tonewinner-rs232

Async Python library to control Tonewinner AV processors over RS232 serial, built on [serialx](https://github.com/puddly/serialx).

Supports the AT-500 specifically, other models should work but haven't been tested. Please open an issue if you encounter problems with other models.

## Installation

```
pip install tonewinner-rs232
```

Requires Python 3.12+.

## Quick start

```python
import asyncio
from tonewinner_rs232 import TonewinnerReceiver

async def main():
    receiver = TonewinnerReceiver("/dev/ttyUSB0")

    # Establish a connection
    await receiver.connect()

    # Query the receiver's current state
    await receiver.query_state()

    print(f"Power: {receiver.state.power}")
    print(f"Volume: {receiver.state.volume}")
    print(f"Source: {receiver.state.source_name}")

    await receiver.power_off()
    await receiver.disconnect()

asyncio.run(main())
```

## Features

- Async API built on serialx
- Full state query and real-time state updates
- Event subscription for state changes
- Power, volume, mute, input source, and sound mode control
- Automatic framing of the `##...*` Tonewinner RS232 protocol
- Built-in CLI for testing

## CLI

Just prints current state at the moment.

```bash
python -m tonewinner_rs232 /dev/ttyUSB0
```
