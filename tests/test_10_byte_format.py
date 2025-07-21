#!/usr/bin/env python3
"""
Test using exact 10-byte format from rasheeddo repository
"""

import serial
import time
import struct

def test_10_byte_mode_switch():
    """Test mode switching using exact 10-byte format"""
    print("🔧 Testing 10-Byte Mode Switch Format")
    print("=" * 50)
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)
        print(f"Connected to {ser.name}")
        
        motor_id = 4
        
        # Function to send feedback request (our format works for this)
        def send_feedback_request():
            packet = [motor_id, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            crc = 0x00
            for byte in packet:
                crc = crc ^ byte
                for _ in range(8):
                    if crc & 0x01:
                        crc = (crc >> 1) ^ 0x8C
                    else:
                        crc >>= 1
            packet.append(crc)
            
            hex_str = ' '.join(f'{b:02X}' for b in packet)
            print(f"TX (feedback): {hex_str}")
            
            ser.reset_input_buffer()
            ser.write(bytes(packet))
            ser.flush()
            time.sleep(0.2)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                hex_response = ' '.join(f'{b:02X}' for b in response)
                print(f"RX: {hex_response}")
                return response
            else:
                print("RX: No response")
                return None
        
        # Function to send mode switch using 10-byte format (no CRC)
        def send_10_byte_mode_switch(mode_value):
            # Using exact format from rasheeddo: ID 0xA0 00 00 00 00 00 00 00 MODE
            packet_data = struct.pack(">BBBBBBBBBB", motor_id, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, mode_value)
            
            hex_str = ' '.join(f'{b:02X}' for b in packet_data)
            print(f"TX (10-byte): {hex_str}")
            
            ser.reset_input_buffer()
            ser.write(packet_data)
            ser.flush()
            time.sleep(0.5)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                hex_response = ' '.join(f'{b:02X}' for b in response)
                print(f"RX: {hex_response}")
                return response
            else:
                print("RX: No response")
                return None
        
        # Get initial state
        print("1. Getting initial state...")
        response = send_feedback_request()
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Initial mode: 0x{mode:02X} ({mode})")
        
        # Try switching to velocity mode using 10-byte format
        print("\n2. Switching to velocity mode (10-byte format)...")
        send_10_byte_mode_switch(0x02)
        
        # Verify switch
        print("\n3. Verifying velocity mode switch...")
        response = send_feedback_request()
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after velocity switch: 0x{mode:02X} ({mode})")
            if mode == 2:
                print("✅ Successfully switched to velocity mode!")
            else:
                print("❌ Failed to switch to velocity mode")
        
        # Try switching to current mode
        print("\n4. Switching to current mode (10-byte format)...")
        send_10_byte_mode_switch(0x01)
        
        # Verify switch
        print("\n5. Verifying current mode switch...")
        response = send_feedback_request()
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after current switch: 0x{mode:02X} ({mode})")
            if mode == 1:
                print("✅ Successfully switched to current mode!")
            else:
                print("❌ Failed to switch to current mode")
        
        # Try switching back to position mode
        print("\n6. Switching back to position mode (10-byte format)...")
        send_10_byte_mode_switch(0x03)
        
        # Verify switch
        print("\n7. Verifying position mode switch...")
        response = send_feedback_request()
        if response and len(response) >= 10:
            mode = response[1]
            print(f"Mode after position switch: 0x{mode:02X} ({mode})")
            if mode == 3:
                print("✅ Successfully switched to position mode!")
            else:
                print("❌ Failed to switch to position mode")
        
        ser.close()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_10_byte_mode_switch()