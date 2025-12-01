#!/usr/bin/env python3
"""
JoystickUDP - Simple class for sending joystick events over UDP.

Usage:
    from joystick_udp import JoystickUDP
    
    sender = JoystickUDP(host='192.168.1.100', port=5005)
    sender.send_event(event_type=2, time=123456, number=1, value=-171)
    sender.close()
"""

import socket
import json


class JoystickUDP:
    """Simple UDP sender for joystick events."""
    
    def __init__(self, host: str = 'localhost', port: int = 5005):
        """
        Initialize UDP sender.
        
        Args:
            host: Target hostname or IP address
            port: Target UDP port number
        """
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_event(self, event_type: int, time: int, number: int, value: int) -> None:
        """
        Send a joystick event over UDP as JSON.
        
        Args:
            event_type: Event type (1=button, 2=axis)
            time: Timestamp from jstest
            number: Button/axis number
            value: Event value
        """
        event_data = {
            'type': event_type,
            'time': time,
            'number': number,
            'value': value
        }
        
        # Convert to JSON and encode as bytes
        message = json.dumps(event_data).encode('utf-8')
        
        # Send over UDP
        self.socket.sendto(message, (self.host, self.port))
    
    def close(self) -> None:
        """Close the UDP socket."""
        self.socket.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures socket is closed."""
        self.close()


if __name__ == "__main__":
    # Simple test
    print("Testing JoystickUDP...")
    with JoystickUDP(host='localhost', port=5005) as sender:
        # Send a test button press
        sender.send_event(event_type=1, time=1000, number=0, value=1)
        print("Sent test button press event")
        
        # Send a test axis movement
        sender.send_event(event_type=2, time=1001, number=1, value=-32767)
        print("Sent test axis movement event")
    
    print("Done!")
