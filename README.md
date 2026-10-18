# tonewinner-rs232

[![PyPI Version](https://img.shields.io/pypi/v/tonewinner-rs232)](https://pypi.org/project/tonewinner-rs232/) [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/emma-sg/tonewinner-rs232/test.yaml)](https://github.com/emma-sg/tonewinner-rs232/actions/workflows/test.yaml)

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

## Probing a receiver

`probe()` checks that a receiver answers and reads its identity. The Home Assistant Tonewinner integration calls it during setup.

```python
info = await receiver.probe()
print(info.model if info else "model unknown")
```

A receiver in standby answers power polls and ignores every other query, so `probe()` polls power first. If the receiver reports standby, `probe()` powers it on to read the model and powers it off again when it is done. A receiver that already reports power as on is read directly and never woken.

`probe()` raises `ConnectionError` when the power poll goes unanswered, since that means the connection is unusable. It returns `None` when the receiver answers but reports no readable identity, such as when it is still booting after the wake.

`query_state()` uses the same behavior. It skips the queries a standby receiver would ignore instead of waiting on the timeouts, so querying a device in standby returns its power state rather than failing.

## Features

- Async API built on serialx
- Full state query and real-time state updates
- Event subscription for state changes
- Power, volume, mute, input source, and sound mode control
- `probe()` for reading a receiver's identity, waking it from standby if needed
- Automatic framing of the `##...*` Tonewinner RS232 protocol
- Built-in CLI for testing

## CLI

Just prints current state at the moment.

```bash
python -m tonewinner_rs232 /dev/ttyUSB0
```
