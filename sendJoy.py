#!/usr/bin/env python3
"""
Simple script to read jstest --event output and send values over UDP.

Usage:
  python3 sendJoy.py -d [--host HOST] [--port PORT] [-v]
  python3 sendJoy.py --device DEVICE [--host HOST] [--port PORT] [-v]

Requires at least -d flag to run with defaults.
Default device: /dev/input/js0, Default host: localhost, Default port: 5005
"""

import sys
import re
import subprocess
import argparse
from joystick_udp import JoystickUDP

# Pattern to match jstest --event output
# Example: Event: type 2, time 3656941, number 1, value -171
EVENT_PATTERN = re.compile(
    r'Event: type\s+(\d+),\s+time\s+(\d+),\s+number\s+(\d+),\s+value\s+([-]?\d+)'
)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Read joystick events and send over UDP',
        epilog='Use -d to run with all defaults, or specify options as needed.'
    )
    parser.add_argument('-d', '--defaults', action='store_true', 
                       help='Run with default settings (required if no device specified)')
    parser.add_argument('--device', default='/dev/input/js0', 
                       help='Joystick device (default: /dev/input/js0)')
    parser.add_argument('--host', default='localhost', 
                       help='Target host (default: localhost)')
    parser.add_argument('--port', type=int, default=5005, 
                       help='Target UDP port (default: 5005)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output')
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Reading joystick events from {args.device}...")
        print(f"Sending to {args.host}:{args.port}")
        print("-" * 60)
    else:
        # Brief startup message in non-verbose mode
        print(f"Sending joystick from {args.device} to {args.host}:{args.port} (Ctrl+C to stop)")
    
    try:
        # Initialize UDP sender
        udp_sender = JoystickUDP(host=args.host, port=args.port)
        
        # Start jstest as a subprocess
        process = subprocess.Popen(
            ["jstest", "--event", args.device],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Read output line by line
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            match = EVENT_PATTERN.search(line)
            if match:
                event_type, time, number, value = match.groups()
                # Convert to integers
                event_type = int(event_type)
                time = int(time)
                number = int(number)
                value = int(value)
                
                # Send over UDP
                udp_sender.send_event(event_type, time, number, value)
                
                # Print locally if verbose mode enabled
                if args.verbose:
                    print(f"Sent: Time: {time:>10} | EventType: {event_type} | Number: {number:>2} | Value: {value:>6}")
            else:
                # Print unrecognized lines only in verbose mode
                if args.verbose:
                    print("Failed to parse line:")
                    print(line)
        
        udp_sender.close()
                
    except KeyboardInterrupt:
        if args.verbose:
            print("\nStopped.")
        if 'process' in locals():
            process.terminate()
        if 'udp_sender' in locals():
            udp_sender.close()
        return 0
    except FileNotFoundError:
        print("Error: jstest not found. Please install it (e.g., sudo apt install joystick)")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    print("Jstest process ended.")
    print("Joystick disconnected?")
    return 0

if __name__ == "__main__":
    sys.exit(main())
