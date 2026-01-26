# Windows Virtual Controller Setup - Project Handoff

## 🎯 Project Overview

This system routes FPV drone controls between a physical controller and UDP-based vision control. The router runs on Linux (Jetson), and the virtual controller runs on Windows to receive the UDP stream.

## 📋 Current Status

✅ **COMPLETED on Linux (Jetson)**
- Router program switches between physical controller and UDP vision control
- Button 3 switches modes: pressed = physical control, released = UDP control
- All buttons and auxiliary axes (4-7) pass through to output in BOTH modes
- Main 4 axes (0-3: Roll, Pitch, Throttle, Yaw) switch sources based on mode

✅ **COMPLETED on Windows**
- Virtual Xbox 360 controller emulation program
- Receives UDP events and maps to virtual gamepad
- Button support already implemented (buttons 0-15 mapped to Xbox buttons)
- Axes 0-7 support (Xbox 360 limitation: only 6 axes can be mapped)

## 🏗️ Architecture

```
┌─────────────────┐     UDP Port 5001      ┌──────────────┐
│ Vision System   │────────────────────────>│              │
│ (UDP Input)     │   {dx, dy, bw, bh}     │              │
└─────────────────┘                         │    ROUTER    │
                                            │   (Jetson)   │
┌─────────────────┐                         │              │
│ Physical        │──> Direct Read          │              │
│ Controller      │    /dev/input/js0       │              │
│                 │                         │              │
│ - 8 Axes:       │                         └──────┬───────┘
│   0-3: Sticks   │                                │
│   4-7: Pots/Btn │                                │ UDP Port 5005
│ - Buttons       │                                │ Joystick Events
│   3: Mode Switch│                                │
│   Others: Pass  │                                ▼
└─────────────────┘                         ┌──────────────┐
                                            │   WINDOWS    │
                                            │   Virtual    │
                                            │  Controller  │
                                            └──────────────┘
```

## 🎮 Physical Controller Layout

**8 Axes:**
- **Axis 0**: Roll (left stick X)
- **Axis 1**: Pitch (left stick Y)
- **Axis 2**: Throttle (right stick X)
- **Axis 3**: Yaw (right stick Y)
- **Axis 4-5**: Potentiometer thumb knobs
- **Axis 6-7**: Button-style axes (press = max value)

**Buttons:**
- **Button 3**: MODE SWITCH (pressed=physical, released=UDP)
- **Other buttons**: Flight switches, arm/disarm, etc. (pass through)

## 📦 Files Included

### Linux (Jetson) Files
1. `main.py` - Main orchestration, starts all processes
2. `router.py` - Routes between input sources, handles passthrough
3. `joystick_receiver.py` - Reads physical controller
4. `udp_input_receiver.py` - Receives vision control commands
5. `udp_output.py` - Sends joystick events via UDP
6. `config.py` - Configuration constants
7. `test_receiver.py` - Test program to verify UDP output

### Windows Files
1. `win_receive_joy_vgamepad.py` - Virtual Xbox 360 controller emulator

## 🔧 Windows Setup Instructions

### Prerequisites
```bash
pip install vgamepad
```

**Important**: On Windows, you need the ViGEm Bus Driver:
- Download from: https://github.com/ViGEm/ViGEmBus/releases
- Install the latest version (e.g., `ViGEmBus_Setup_x64.msi`)

### Running the Virtual Controller

**Basic usage:**
```bash
python win_receive_joy_vgamepad.py --default
```

**Custom host/port:**
```bash
python win_receive_joy_vgamepad.py --host 0.0.0.0 --port 5005
```

**Quiet mode (less console output):**
```bash
python win_receive_joy_vgamepad.py --default --quiet
```

### Network Setup

Make sure Windows can receive from Jetson:
1. Check firewall allows UDP port 5005
2. Verify network connectivity: `ping <jetson-ip>`
3. Jetson sends to: `192.168.178.200:5005` (configured in `config.py`)

## 🧪 Testing Workflow

### 1. Test on Jetson (Linux)

**Terminal 1** - Run the test receiver:
```bash
cd /home/jetson/Desktop/ControlSwitch
python test_receiver.py
```

**Terminal 2** - Run the router:
```bash
python main.py
```

**Expected test_receiver.py output:**
- 🎮 Axes 0-3: Main control (source depends on mode)
- 🔧 Axes 4-7: Auxiliary from physical controller
- 🔘 Buttons: From physical controller (except button 3)

### 2. Test on Windows

**Run virtual controller:**
```bash
python win_receive_joy_vgamepad.py --default
```

**Test in game/simulator:**
- Open Windows Game Controllers (`joy.cpl`)
- Should see "Xbox 360 Controller"
- Move physical controller → should see virtual controller move
- Press buttons → should see button lights

## 📊 Expected Behavior

### JOYSTICK Mode (Button 3 PRESSED)
| Input | Source | Output |
|-------|--------|--------|
| Axes 0-3 | Physical Controller | Sent to Windows |
| Axes 4-7 | Physical Controller | Sent to Windows |
| Buttons | Physical Controller | Sent to Windows |

### UDP Mode (Button 3 RELEASED)
| Input | Source | Output |
|-------|--------|--------|
| Axes 0-3 | UDP Vision System | Sent to Windows |
| Axes 4-7 | Physical Controller | Sent to Windows |
| Buttons | Physical Controller | Sent to Windows |

## ⚠️ Known Limitations

1. **Xbox 360 Controller Limitation**: Only 6 axes available
   - Axes 0-5 are mapped
   - Axes 6-7 are received but cannot be mapped to Xbox 360
   - If you need 8 axes, consider using DirectInput virtual controller

2. **Button Mapping**: Limited to 15 buttons (Xbox 360 standard)
   - If you have more buttons, they won't be mapped

3. **Axis Range**: Xbox 360 uses -32768 to 32767 (matches Linux joystick range)

## 🐛 Troubleshooting

### No virtual controller appears
- Ensure ViGEm Bus Driver is installed
- Restart Windows after driver installation
- Check Device Manager for ViGEm devices

### No UDP packets received
- Check firewall settings
- Verify Jetson can ping Windows PC
- Check router output with `test_receiver.py` on Jetson first
- Verify IP address in `config.py` matches Windows PC

### Buttons not working
- Buttons ARE implemented and should work
- Check test_receiver.py output to verify buttons are being sent
- Verify button mapping in button_map dictionary

### Axes inverted or wrong
- Left stick Y and Right stick Y are inverted in code (normal for games)
- Adjust axis mapping in handle_axis_event() if needed

## 🔍 Debug Commands

**On Jetson - Check UDP output:**
```bash
sudo tcpdump -n -i any udp port 5005 -X
```

**On Windows - Check if UDP is received:**
```bash
# Use Wireshark or test with simple UDP listener
```

## 📝 Configuration Changes

If you need to change ports or IP addresses, edit `config.py` on Jetson:

```python
OUTPUT_UDP_PORT = 5005
OUTPUT_UDP_HOST = "192.168.178.200"  # Your Windows PC IP
```

## 🎯 Next Steps (If Needed)

1. **If you need axes 6-7**: Switch from Xbox 360 to DirectInput virtual controller
2. **If you need more buttons**: Use a DirectInput library instead of vgamepad
3. **Performance tuning**: Adjust `ROUTER_LOOP_HZ` in config.py (currently 50Hz)
4. **Wireless issues**: Consider UDP packet loss handling, add reconnection logic

## 📧 Context for Future Development

**Core Design Philosophy:**
- Clean separation between input sources (physical vs UDP)
- Button 3 as the single mode switch
- Auxiliary controls always pass through from physical controller
- Only main flight axes (0-3) switch sources

**Why this works:**
- Pilot maintains control of arm/disarm and flight modes at all times
- Vision system only controls main flight axes
- No conflicts between control sources
- Smooth transition with jerk prevention (3-frame skip on switch)

---

## 🚀 Quick Start Command Summary

**On Jetson:**
```bash
cd /home/jetson/Desktop/ControlSwitch
python main.py
```

**On Windows:**
```bash
python win_receive_joy_vgamepad.py --default
```

That's it! The system should now be routing controls to your Windows virtual controller.
