#!/usr/bin/env python3
"""
DDSM115 Motor Diagnostic Script
Systematically troubleshoot motor communication and state
"""

import serial
import time

def crc8_update(crc, data_byte):
    """CRC-8 update function (from Waveshare official code)"""
    crc = crc ^ data_byte
    for _ in range(8):
        if crc & 0x01:
            crc = (crc >> 1) ^ 0x8C
        else:
            crc >>= 1
    return crc

def calculate_crc(data):
    """Calculate CRC-8 for packet"""
    if len(data) == 8:
        data = data + [0x00]
    
    crc = 0x00
    for byte in data[:9]:
        crc = crc8_update(crc, byte)
    return crc

def send_command(ser, packet_data):
    """Send command to motor and return response"""
    # packet_data should be 9 bytes [DATA[0] through DATA[8]]
    if len(packet_data) != 9:
        raise ValueError("Packet data must be exactly 9 bytes")
    
    crc = calculate_crc(packet_data)
    packet = packet_data + [crc]
    
    hex_str = ' '.join(f'{b:02X}' for b in packet)
    print(f"TX: {hex_str}")
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(packet))
        ser.flush()
        time.sleep(0.2)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            hex_response = ' '.join(f'{b:02X}' for b in response)
            print(f"RX: {hex_response} ({len(response)} bytes)")
            return response
        else:
            print("RX: No response")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_mode_switch(ser, motor_id, mode_value):
    """Send mode switch command: ID 0xA0 00 00 00 00 00 00 00 MODE_VALUE"""
    packet = [motor_id, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, mode_value]
    return send_command(ser, packet)

def send_drive_command(ser, motor_id, value, accel_time=0, brake=0):
    """Send drive command: ID 0x64 VAL_HIGH VAL_LOW 00 00 ACCEL BRAKE 00"""
    val_high = (value >> 8) & 0xFF
    val_low = value & 0xFF
    packet = [motor_id, 0x64, val_high, val_low, 0x00, 0x00, accel_time, brake, 0x00]
    return send_command(ser, packet)

def send_feedback_request(ser, motor_id):
    """Send feedback request: ID 0x74 00 00 00 00 00 00 00"""
    packet = [motor_id, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    return send_command(ser, packet)

def parse_error_code(error_code):
    """Parse error code bits"""
    errors = []
    if error_code & 0x01:
        errors.append("Sensor error")
    if error_code & 0x02:
        errors.append("Overcurrent error")
    if error_code & 0x04:
        errors.append("Phase overcurrent error")
    if error_code & 0x08:
        errors.append("Stall error")
    if error_code & 0x10:
        errors.append("Troubleshooting")
    return errors if errors else ["No errors"]

def main():
    print("DDSM115 Motor Diagnostic Tool")
    print("============================")
    
    # Connect to serial port
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)
        print(f"Connected to {ser.name} at {ser.baudrate} baud")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    motor_id = 1  # Start with ID 1
    
    print(f"\nStep 1: Testing motor ID {motor_id} detection")
    print("-" * 40)
    
    # Try to read feedback from motor
    response = send_feedback_request(ser, motor_id)
    if response and len(response) >= 10 and response[0] == motor_id:
        print("✓ Motor responds to feedback request")
        error_code = response[8]
        errors = parse_error_code(error_code)
        print(f"  Error status: {', '.join(errors)}")
    else:
        print("✗ No response to feedback request")
        print("Trying to detect motor on different IDs...")
        
        # Try IDs 0-5
        for test_id in range(6):
            print(f"  Testing ID {test_id}...")
            response = send_feedback_request(ser, test_id)
            if response and len(response) >= 10 and response[0] == test_id:
                print(f"  ✓ Found motor at ID {test_id}")
                motor_id = test_id
                error_code = response[8]
                errors = parse_error_code(error_code)
                print(f"    Error status: {', '.join(errors)}")
                break
        else:
            print("  ✗ No motor found on IDs 0-5")
            print("  Proceeding with ID 1 anyway...")
    
    print(f"\nStep 2: Switch to Velocity Mode (ID {motor_id})")
    print("-" * 40)
    
    # Switch to velocity loop mode (0x02)
    print("Switching to velocity loop mode...")
    response = send_mode_switch(ser, motor_id, 0x02)
    time.sleep(0.5)
    
    # Verify mode switch worked
    print("Verifying mode switch...")
    response = send_feedback_request(ser, motor_id)
    if response and len(response) >= 10:
        mode = response[1]
        print(f"Current mode: 0x{mode:02X}")
        error_code = response[8]
        errors = parse_error_code(error_code)
        print(f"Error status: {', '.join(errors)}")
        
        if error_code != 0:
            print("⚠️  Motor has errors - this might prevent movement!")
    
    print(f"\nStep 3: Motor Movement Test (ID {motor_id})")
    print("-" * 40)
    
    # Try different speeds
    speeds = [10, 25, 50, -25, 0]  # Including stop command
    
    for speed in speeds:
        if speed == 0:
            print("Stopping motor...")
        else:
            print(f"Testing {speed} RPM...")
        
        # Send drive command
        response = send_drive_command(ser, motor_id, speed)
        time.sleep(1)
        
        # Read feedback to see current state
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            # Parse feedback data
            mode = response[1]
            torque = int.from_bytes(response[2:4], 'big', signed=True)
            velocity = int.from_bytes(response[4:6], 'big', signed=True)
            position_high = response[6]
            position_low = response[7]
            error_code = response[8]
            
            print(f"  Mode: 0x{mode:02X}, Torque: {torque}, Velocity: {velocity} RPM")
            print(f"  Position: {position_high}.{position_low}, Error: 0x{error_code:02X}")
            
            if error_code != 0:
                errors = parse_error_code(error_code)
                print(f"  ⚠️  Errors: {', '.join(errors)}")
        
        print("  (Check if motor is spinning visually)")
        time.sleep(1)
    
    # Apply brake to stop
    print("Applying brake...")
    send_drive_command(ser, motor_id, 0, brake=0xFF)
    
    print(f"\nStep 4: Final Diagnosis (ID {motor_id})")
    print("-" * 40)
    
    response = send_feedback_request(ser, motor_id)
    if response and len(response) >= 10:
        print("✓ Motor communication is working")
        error_code = response[8]
        if error_code == 0:
            print("✓ No motor errors detected")
            print("If motor is still not spinning, check:")
            print("  - Power supply voltage (12-24V)")
            print("  - Motor mechanical load")
            print("  - Physical connections")
        else:
            errors = parse_error_code(error_code)
            print(f"✗ Motor errors detected: {', '.join(errors)}")
            print("These errors may prevent motor movement!")
    else:
        print("✗ Motor communication failed")
    
    ser.close()
    print("\nDiagnostic complete.")

if __name__ == "__main__":
    main()