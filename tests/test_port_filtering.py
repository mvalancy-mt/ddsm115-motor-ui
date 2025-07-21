#!/usr/bin/env python3
"""
Test port filtering functionality
"""

import serial.tools.list_ports

def test_port_filtering():
    """Test the port filtering logic"""
    print("🧪 Testing USB-to-RS485 port filtering...")
    
    all_ports = serial.tools.list_ports.comports()
    print(f"📋 Found {len(all_ports)} total serial ports:")
    
    for port in all_ports:
        print(f"  - {port.device}: {port.description}")
    
    # Apply the same filtering logic as the GUI
    valid_ports = []
    for port in all_ports:
        port_info = f"{port.device} - {port.description}"
        
        # Skip ports with no description or generic descriptions
        if not port.description or port.description.lower() in ['n/a', 'unknown', '']:
            # Only include ttyUSB* devices even without description
            if 'ttyUSB' in port.device or 'ttyACM' in port.device:
                valid_ports.append((port.device, port_info))
            continue
        
        # Check for common USB-to-RS485 identifiers in description
        usb_rs485_keywords = [
            'usb', 'ftdi', 'ch340', 'ch341', 'cp210', 'pl2303', 'ft232',
            'converter', 'adapter', 'bridge', 'uart', 'rs485', 'rs232'
        ]
        
        description_lower = port.description.lower()
        
        # Include if description contains USB-to-serial keywords
        if any(keyword in description_lower for keyword in usb_rs485_keywords):
            valid_ports.append((port.device, port_info))
    
    print(f"\n✅ Filtered to {len(valid_ports)} valid USB-to-RS485 ports:")
    for device, info in valid_ports:
        print(f"  - {info}")
    
    if len(valid_ports) == 1:
        print(f"\n🔌 Would auto-connect to: {valid_ports[0][1]}")
    elif len(valid_ports) > 1:
        print(f"\n📂 Multiple ports available - user selection required")
    else:
        print(f"\n⚠️ No USB-to-RS485 ports detected")
    
    return len(valid_ports)

if __name__ == "__main__":
    test_port_filtering()