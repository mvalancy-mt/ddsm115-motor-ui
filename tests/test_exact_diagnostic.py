#!/usr/bin/env python3
"""
Test using exact same approach as motor_diagnostic.py
"""

import serial
import time

def crc8_update(crc, data_byte):
    """CRC-8 update function (from diagnostic script)"""
    crc = crc ^ data_byte
    for _ in range(8):
        if crc & 0x01:
            crc = (crc >> 1) ^ 0x8C
        else:
            crc >>= 1
    return crc

def calculate_crc(data):
    """Calculate CRC-8 for packet (from diagnostic script)"""
    if len(data) == 8:
        data = data + [0x00]
    
    crc = 0x00
    for byte in data[:9]:
        crc = crc8_update(crc, byte)
    return crc

def send_command(ser, packet_data):
    """Send command to motor (from diagnostic script)"""
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
    """Send mode switch command (from diagnostic script)"""
    packet = [motor_id, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, mode_value]
    return send_command(ser, packet)

def send_feedback_request(ser, motor_id):
    """Send feedback request (from diagnostic script)"""
    packet = [motor_id, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    return send_command(ser, packet)

def test_exact_diagnostic():
    """Test using exact diagnostic approach"""
    print("🔧 Exact Diagnostic Approach Test")
    print("=" * 50)
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)
        print(f"Connected to {ser.name}")
        
        motor_id = 4  # Use the motor we found
        
        # Get initial state
        print(f"\n1. Getting initial state...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Initial mode: 0x{mode:02X} ({mode})")
        
        # Try switching to velocity mode (0x02)
        print(f"\n2. Switching to velocity mode...")
        response = send_mode_switch(ser, motor_id, 0x02)
        time.sleep(0.5)
        
        # Verify switch
        print(f"\n3. Verifying velocity mode switch...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after velocity switch: 0x{mode:02X} ({mode})")
            if mode == 2:
                print("✅ Successfully switched to velocity mode!")
            else:
                print("❌ Failed to switch to velocity mode")
        
        # Try switching to current mode (0x01)
        print(f"\n4. Switching to current mode...")
        response = send_mode_switch(ser, motor_id, 0x01)
        time.sleep(0.5)
        
        # Verify switch
        print(f"\n5. Verifying current mode switch...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after current switch: 0x{mode:02X} ({mode})")
            if mode == 1:
                print("✅ Successfully switched to current mode!")
            else:
                print("❌ Failed to switch to current mode")
        
        # Try switching to position mode (0x03)
        print(f"\n6. Switching to position mode...")
        response = send_mode_switch(ser, motor_id, 0x03)
        time.sleep(0.5)
        
        # Verify switch
        print(f"\n7. Verifying position mode switch...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after position switch: 0x{mode:02X} ({mode})")
            if mode == 3:
                print("✅ Successfully switched to position mode!")
            else:
                print("❌ Failed to switch to position mode")
        
        # Try switching back to velocity mode (0x02)
        print(f"\n8. Switching back to velocity mode...")
        response = send_mode_switch(ser, motor_id, 0x02)
        time.sleep(0.5)
        
        # Verify switch
        print(f"\n9. Verifying return to velocity mode...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Final mode: 0x{mode:02X} ({mode})")
            if mode == 2:
                print("✅ Successfully switched back to velocity mode!")
            else:
                print("❌ Failed to switch back to velocity mode")
        
        ser.close()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_diagnostic()