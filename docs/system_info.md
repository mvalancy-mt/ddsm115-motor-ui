# DDSM115 Motor Control Interface

## Version 1.0.0

**Created by Matthew Valancy**

---

## Overview

A comprehensive interface for controlling DDSM115 servo motors with real-time monitoring and intuitive controls.

### Key Features

- **Real-time Motor Control**: Intuitive sliders for velocity, position, and current control
- **Live Data Visualization**: Dynamic graphs showing motor performance metrics  
- **Automatic Mode Switching**: Seamless transitions between control modes
- **Emergency Safety**: Instant stop functionality for all connected motors
- **Dark Theme Interface**: Optimized for extended use in various lighting conditions
- **Robust Communication**: RS485 protocol with error handling and recovery
- **Multi-motor Support**: Control multiple motors with automatic detection

### Technical Capabilities

- **Control Modes**:
  - Velocity Control: -143 to +143 RPM
  - Position Control: 0° to 360° with 0.1° precision
  - Current Control: -8A to +8A for torque applications

- **Real-time Monitoring**:
  - Motor velocity, position, and torque
  - Temperature monitoring with alerts
  - Communication statistics (TX/RX rates)
  - Connection status and diagnostics

- **Safety Features**:
  - Emergency stop for immediate motor shutdown
  - Automatic velocity ramping for safe mode transitions
  - Connection monitoring with auto-reconnect
  - Error handling and graceful degradation

### Communication Protocol

The application uses RS485 communication with custom packet protocols:
- 10-byte command packets for motor control
- Real-time feedback monitoring at 20Hz
- Automatic motor ID detection and configuration
- Robust error handling and retry mechanisms

### Use Cases

- **Robotics**: Precise control for robotic joints and actuators
- **Industrial Automation**: Conveyor systems and positioning applications
- **Electric Vehicles**: Hub motor control for e-bikes and scooters
- **Research & Development**: Motor characterization and testing
- **Educational**: Learning motor control principles and RS485 communication

### System Requirements

- Python 3.8+ with tkinter, matplotlib, and pyserial
- USB-to-RS485 converter for communication
- DDSM115 motor with proper power supply (24-48V)
- Operating system: Windows, Linux, or macOS

---

This application represents a complete solution for DDSM115 motor control,
combining ease of use with professional-grade functionality.