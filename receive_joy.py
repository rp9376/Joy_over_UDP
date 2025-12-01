#!/usr/bin/env python3
"""
Simple UDP receiver for joystick events.

Usage:
  python3 receive_joy.py -d [options]
  python3 receive_joy.py --host HOST --port PORT

Options:
  -d, --default      Use default settings (host: 0.0.0.0, port: 5005)
  -q, --quiet        Quiet mode - suppress console output
  --host HOST        Host to bind to (default: 0.0.0.0)
  --port PORT        UDP port to listen on (default: 5005)
"""

import socket
import json
import argparse
import sys


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Receive joystick events over UDP',
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
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Bind to address
        sock.bind((args.host, args.port))
        if not args.quiet:
            print(f"Listening for joystick events on {args.host}:{args.port}...")
            print("Press Ctrl+C to stop")
            print("-" * 60)
        
        while True:
            # Receive data
            data, addr = sock.recvfrom(1024)  # Buffer size 1024 bytes
            
            try:
                # Decode JSON
                event = json.loads(data.decode('utf-8'))
                
                # Extract fields
                event_type = event.get('type', 0)
                time = event.get('time', 0)
                number = event.get('number', 0)
                value = event.get('value', 0)
                
                # Format output
                type_str = "BUTTON" if event_type == 1 else "AXIS  " if event_type == 2 else f"TYPE{event_type}"
                
                if not args.quiet:
                    print(f"[{addr[0]}:{addr[1]}] Time: {time:>10} | {type_str} | Number: {number:>2} | Value: {value:>6}")
                
            except json.JSONDecodeError:
                if not args.quiet:
                    print(f"Received invalid JSON from {addr}: {data}")
            except Exception as e:
                if not args.quiet:
                    print(f"Error processing data from {addr}: {e}")
                
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nStopped.")
        return 0
    except Exception as e:
        if not args.quiet:
            print(f"Error: {e}")
        return 1
    finally:
        sock.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
