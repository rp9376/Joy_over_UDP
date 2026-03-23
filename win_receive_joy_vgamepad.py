#!/usr/bin/env python3
"""
UDP receiver that creates a virtual Xbox 360 controller.
Receives joystick events over UDP and translates them to a virtual gamepad.

Usage:
  python3 receive_joy_vgamepad.py -d [options]
  python3 receive_joy_vgamepad.py --host HOST --port PORT

Options:
  -d, --default      Use default settings (host: 0.0.0.0, port: 5005)
  -q, --quiet        Quiet mode - suppress console output
  --host HOST        Host to bind to (default: 0.0.0.0)
  --port PORT        UDP port to listen on (default: 5005)
  
Axis Mapping (Linux joystick to Xbox 360):
  Axis 0 (Left X)  -> Left Stick X
  Axis 1 (Left Y)  -> Left Stick Y
  Axis 2 (Right X) -> Right Stick X
  Axis 3 (Right Y) -> Right Stick Y
  Axis 6           -> Left Trigger
  Axis 7           -> Right Trigger
  
Button Mapping:
  All buttons are mapped to corresponding Xbox 360 buttons (0-15)
"""

import os
import socket
import json
import argparse
import sys
import vgamepad as vg

# ---------------------------------------------------------------------------
# Live terminal display
# ---------------------------------------------------------------------------

# Enable ANSI escape-code support on Windows
os.system('')

_BAR_WIDTH = 30          # characters inside bar brackets, e.g. [######----]
_BAR_TOTAL = _BAR_WIDTH + 2   # including the [ and ] brackets
_VAL_FIELD = _BAR_TOTAL + 8   # bar + space + value string (padded)
_HLINE_VAL = '\u2500' * (_VAL_FIELD + 2)


def _axis_bar(norm: float) -> str:
    """Centre-anchored bar for a normalised axis value in [-1.0, 1.0]."""
    half = _BAR_WIDTH // 2
    fill = round(abs(norm) * half)
    buf = ['-'] * _BAR_WIDTH
    if norm >= 0:
        for i in range(half, min(half + fill, _BAR_WIDTH)):
            buf[i] = '#'
    else:
        for i in range(max(half - fill, 0), half):
            buf[i] = '#'
    return '[' + ''.join(buf) + ']'


def _button_bar(val: int) -> str:
    """Full or empty bar for a button value (0 or 1)."""
    return '[' + ('#' if val else '-') * _BAR_WIDTH + ']'


class LiveDisplay:
    """
    In-place updating table that shows the state of every received
    axis and button channel.  Uses ANSI cursor control to overwrite
    the previous render on each call to ``render()``.
    """

    def __init__(self) -> None:
        self._axes: dict[int, int] = {}     # axis_number  -> raw value
        self._buttons: dict[int, int] = {}  # button_number -> 0 / 1
        self._prev_lines: int = 0

    def update(self, event_type: int, number: int, value: int) -> None:
        """Record the latest value for an axis (type 2) or button (type 1)."""
        if event_type == 2:
            self._axes[number] = value
        elif event_type == 1:
            self._buttons[number] = value

    def render(self) -> None:
        """Overwrite the previous table render with the current state."""
        vf = _VAL_FIELD
        hv = _HLINE_VAL

        lines: list[str] = [
            f'\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c{hv}\u2510',
            f'\u2502 Channel \u2502  Type  \u2502    \u00b5s    \u2502 {"Value":<{vf}} \u2502',
            f'\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c{hv}\u2524',
        ]

        ch = 1
        for num in sorted(self._axes):
            raw  = self._axes[num]
            norm = max(-1.0, min(1.0, raw / 32767.0))
            us   = 1500.0 + norm * 500.0
            bar  = _axis_bar(norm)
            val  = f'{norm:+.3f}'
            field = f'{bar} {val}'
            lines.append(
                f'\u2502  CH{ch:>2}   \u2502 axis   \u2502 {us:>8.1f} \u2502 {field:<{vf}} \u2502'
            )
            ch += 1

        for num in sorted(self._buttons):
            v     = self._buttons[num]
            us    = 1000.0 + v * 1000.0
            bar   = _button_bar(v)
            val   = str(v)
            field = f'{bar} {val}'
            lines.append(
                f'\u2502  CH{ch:>2}   \u2502 button \u2502 {us:>8.1f} \u2502 {field:<{vf}} \u2502'
            )
            ch += 1

        lines.append(
            f'\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534{hv}\u2518'
        )

        # Erase the previous render and draw the updated table
        if self._prev_lines:
            sys.stdout.write(f'\033[{self._prev_lines}A\033[J')
        sys.stdout.write('\n'.join(lines) + '\n')
        sys.stdout.flush()
        self._prev_lines = len(lines)


class VirtualControllerMapper:
    """Maps joystick events to virtual Xbox 360 controller."""
    
    def __init__(self, quiet=False):
        self.gamepad = vg.VX360Gamepad()
        self.quiet = quiet
        
        # Store current axis values (Linux joystick uses -32767 to 32767)
        self.axis_values = {
            0: 0,  # Left stick X (Roll)
            1: 0,  # Left stick Y (Pitch)
            2: 0,  # Right stick X (Throttle)
            3: 0,  # Right stick Y (Yaw)
            4: 0,  # Aux 1 - additional axis
            5: 0,  # Aux 2 - additional axis
            6: -32767,  # Left trigger (Potentiometer/Button-axis)
            7: -32767,  # Right trigger (Potentiometer/Button-axis)
        }
        
        # Button mapping (Linux joystick button -> Xbox 360 button)
        self.button_map = {
            0: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            1: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            2: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            3: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            4: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            5: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            6: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            7: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            8: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            9: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            10: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            # D-pad buttons
            11: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            12: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            13: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            14: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        
        if not self.quiet:
            print("Virtual Xbox 360 controller created!")
    
    def handle_axis_event(self, number, value):
        """Handle axis movement event."""
        # Store all axis values even if not mapped
        if number not in self.axis_values:
            self.axis_values[number] = value
            if not self.quiet:
                print(f"[INFO] Received unmapped axis {number}, storing but not mapping to controller")
            return
        
        self.axis_values[number] = value
        
        # Update the appropriate stick or trigger
        if number in [0, 1]:  # Left stick (Roll, Pitch)
            self.gamepad.left_joystick(
                x_value=self.axis_values[0],
                y_value=-self.axis_values[1]  # Invert Y for proper direction
            )
        elif number in [2, 3]:  # Right stick (Throttle, Yaw)
            self.gamepad.right_joystick(
                x_value=self.axis_values[2],
                y_value=-self.axis_values[3]  # Invert Y for proper direction
            )
        elif number == 6:  # Left trigger
            # Convert from -32767..32767 to 0..255
            trigger_value = int((value + 32767) / 65534 * 255)
            self.gamepad.left_trigger(value=trigger_value)
        elif number == 7:  # Right trigger
            # Convert from -32767..32767 to 0..255
            trigger_value = int((value + 32767) / 65534 * 255)
            self.gamepad.right_trigger(value=trigger_value)
        # Note: Axes 4 and 5 are not mapped to Xbox 360 controller
        # Xbox 360 only has: 2 sticks (4 axes) + 2 triggers (2 axes) = 6 axes total
        # If you need axes 4-5, consider using a different virtual controller library
        
        # Update the virtual controller
        self.gamepad.update()
    
    def handle_button_event(self, number, value):
        """Handle button press/release event."""
        if number not in self.button_map:
            return
        
        button = self.button_map[number]
        
        if value == 1:  # Button pressed
            self.gamepad.press_button(button=button)
        else:  # Button released
            self.gamepad.release_button(button=button)
        
        # Update the virtual controller
        self.gamepad.update()
    
    def reset(self):
        """Reset the controller to neutral state."""
        self.gamepad.reset()
        self.gamepad.update()


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Receive joystick events over UDP and create virtual Xbox 360 controller',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-d', '--default', action='store_true', 
                        help='Use default settings (host: 0.0.0.0, port: 5005)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode - suppress console output')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5005, help='UDP port to listen on (default: 5005)')
    
    # If no arguments provided, show help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    args = parser.parse_args()
    
    # If -d/--default is used, ensure default values
    if args.default:
        args.host = '0.0.0.0'
        args.port = 5005
    
    # Create virtual controller mapper
    try:
        controller = VirtualControllerMapper(quiet=args.quiet)
    except Exception as e:
        print(f"Error creating virtual controller: {e}")
        print("\nMake sure vgamepad is installed: pip install vgamepad")
        print("On Windows, you may also need to install the ViGEm Bus Driver.")
        return 1
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)  # Set 1 second timeout to allow Ctrl+C to work
    
    try:
        # Bind to address
        sock.bind((args.host, args.port))
        if not args.quiet:
            print(f"Listening for joystick events on {args.host}:{args.port}...")
            print("Press Ctrl+C to stop")

        live_display = LiveDisplay()

        while True:
            try:
                # Receive data
                data, addr = sock.recvfrom(1024)  # Buffer size 1024 bytes
            except socket.timeout:
                # Timeout occurred, just continue to allow Ctrl+C checking
                continue
            
            try:
                # Decode JSON
                event = json.loads(data.decode('utf-8'))
                
                # Extract fields
                event_type = event.get('type', 0)
                time = event.get('time', 0)
                number = event.get('number', 0)
                value = event.get('value', 0)
                
                # Process event based on type
                if event_type == 2:  # Axis event
                    controller.handle_axis_event(number, value)
                    type_str = "AXIS  "
                elif event_type == 1:  # Button event
                    controller.handle_button_event(number, value)
                    type_str = "BUTTON"
                else:
                    type_str = f"TYPE{event_type}"
                
                if not args.quiet:
                    live_display.update(event_type, number, value)
                    live_display.render()
                
            except json.JSONDecodeError:
                if not args.quiet:
                    print(f"Received invalid JSON from {addr}: {data}")
            except Exception as e:
                if not args.quiet:
                    print(f"Error processing data from {addr}: {e}")
                
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nStopping and resetting controller...")
        controller.reset()
        if not args.quiet:
            print("Stopped.")
        return 0
    except Exception as e:
        if not args.quiet:
            print(f"Error: {e}")
        controller.reset()
        return 1
    finally:
        sock.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
