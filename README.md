# Joystick over UDP

Send joystick events over UDP to a remote PC using Python.

## Files

- **joystick_udp.py** - Class module for sending joystick events over UDP
- **send_joy.py** - Reads joystick events from `jstest` and sends them over UDP
- **receive_joy.py** - Receives and displays joystick events over UDP

## Quick Start

### 1. Test on Localhost

Open two terminals.

**Terminal 1 - Start the receiver:**
```bash
python3 receive_joy.py
```

**Terminal 2 - Start the sender:**
```bash
python3 send_joy.py -d -v
```

Move your joystick or press buttons. You should see events in both terminals.

### 2. Test on Local Network

**On the receiving PC (e.g., 192.168.1.100):**
```bash
python3 receive_joy.py
```

**On the sending PC (with joystick connected):**
```bash
python3 send_joy.py -d --host 192.168.1.100
```

## Usage

### Sender (send_joy.py)

**Important:** The sender requires at least the `-d` flag (for defaults) or another option to run. Without any arguments, it displays the help page.

```bash
python3 send_joy.py -d [--device DEVICE] [--host HOST] [--port PORT] [-v]
```

Options:
- `-d, --defaults` - Run with default settings (required to use defaults)
- `--device DEVICE` - Joystick device path (default: `/dev/input/js0`)
- `--host HOST` - Target host IP or hostname (default: `localhost`)
- `--port PORT` - Target UDP port (default: `5005`)
- `-v, --verbose` - Enable verbose output (shows events being sent)

**Note:** By default, `send_joy.py` shows a brief startup message then runs silently. Use `-v` or `--verbose` to see each event as it's sent.

Examples:
```bash
# Show help (no arguments)
python3 send_joy.py

# Run with all defaults (localhost:5005, /dev/input/js0)
python3 send_joy.py -d

# Run with defaults and verbose output
python3 send_joy.py -d -v

# Send to remote PC
python3 send_joy.py -d --host 192.168.1.100

# Send to remote PC with verbose output
python3 send_joy.py -d --host 192.168.1.100 --verbose

# Different joystick device
python3 send_joy.py --device /dev/input/js1 --host 192.168.1.100

# Custom port with verbose mode
python3 send_joy.py -d --host 192.168.1.100 --port 6000 -v
```

### Receiver (receive_joy.py)
```bash
python3 receive_joy.py [--host HOST] [--port PORT]
```

Options:
- `--host` - Host to bind to (default: `0.0.0.0` - all interfaces)
- `--port` - UDP port to listen on (default: `5005`)

Examples:
```bash
# Listen on all interfaces
python3 receive_joy.py

# Listen on specific interface
python3 receive_joy.py --host 192.168.1.100

# Custom port
python3 receive_joy.py --port 6000
```

## Event Format

Events are sent as JSON over UDP:
```json
{
  "type": 2,
  "time": 3656941,
  "number": 1,
  "value": -171
}
```

- **type**: 1 = button, 2 = axis
- **time**: Timestamp from jstest
- **number**: Button/axis number
- **value**: Event value (button: 0/1, axis: -32767 to 32767)

## Requirements

- Python 3.6+
- `jstest` utility (install: `sudo apt install joystick`)
- Joystick connected to sender PC

## Troubleshooting

**"jstest not found"**
```bash
sudo apt install joystick
```

**"No such device"**
- Check joystick is connected: `ls /dev/input/js*`
- Try different device: `python3 send_joy.py --device /dev/input/js1`

**No data received on local network**
- Check firewall allows UDP on port 5005
- Verify IPs are correct: `ip addr`
- Test connectivity: `ping <target-ip>`
