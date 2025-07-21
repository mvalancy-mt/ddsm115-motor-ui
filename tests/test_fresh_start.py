#!/usr/bin/env python3
"""
Test mode switching from fresh connection (simulating power cycle)
"""

import serial
import time

def crc8_update(crc, data_byte):
    crc = crc ^ data_byte
    for _ in range(8):
        if crc & 0x01:
            crc = (crc >> 1) ^ 0x8C
        else:
            crc >>= 1
    return crc

def calculate_crc(data):
    if len(data) == 8:
        data = data + [0x00]
    crc = 0x00
    for byte in data[:9]:
        crc = crc8_update(crc, byte)
    return crc

def send_command(ser, packet_data):
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
    packet = [motor_id, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, mode_value]
    return send_command(ser, packet)

def send_feedback_request(ser, motor_id):
    packet = [motor_id, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    return send_command(ser, packet)

def test_fresh_start():
    """Test mode switching from fresh connection"""
    print("🔧 Fresh Start Mode Test")
    print("=" * 40)
    
    try:
        print("🔌 Connecting to motor...")
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)
        print(f"✅ Connected to {ser.name}")
        
        motor_id = 4
        
        # Get initial state immediately after connection
        print(f"\n1. Getting fresh initial state...")
        response = send_feedback_request(ser, motor_id)
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Fresh start mode: 0x{mode:02X} ({mode})")
            
            # Test different modes based on starting mode
            if mode == 2:  # If starting in velocity mode
                print("\n✅ Starting in velocity mode - this is good!")
                
                # Try switching to position mode and back
                print("\n2. Switching to position mode...")
                send_mode_switch(ser, motor_id, 0x03)
                time.sleep(0.5)
                
                response = send_feedback_request(ser, motor_id)
                if response and len(response) >= 10:
                    new_mode = response[1]
                    print(f"After position switch: 0x{new_mode:02X} ({new_mode})")
                
                print("\n3. Switching back to velocity mode...")
                send_mode_switch(ser, motor_id, 0x02)
                time.sleep(0.5)
                
                response = send_feedback_request(ser, motor_id)
                if response and len(response) >= 10:
                    final_mode = response[1]
                    print(f"Final mode: 0x{final_mode:02X} ({final_mode})")
                    if final_mode == 2:
                        print("✅ Successfully switched back to velocity!")
                    else:
                        print("❌ Failed to switch back to velocity")
                        
            else:
                print(f"\n⚠️ Not starting in velocity mode (mode {mode})")
                print("This suggests the motor 'remembers' its last mode setting")
        
        ser.close()
        print("\n🔌 Disconnected")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_fresh_start()