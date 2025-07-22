# DDSM115 Motor Control - Complete Operation Guide

## Table of Contents
1. Getting Started
2. Connection Setup
3. Motor Control
4. Live Monitoring
5. Safety Features
6. Motor ID Management
7. Troubleshooting

---

## Getting Started

### Initial Setup
1. **Hardware Connection**
   - Connect DDSM115 motor to power supply (12-24V, 18V recommended)
   - Connect USB-to-RS485 converter to computer
   - Wire RS485 A+/A- and B+/B- lines to motor
   - Ensure proper grounding and shielding

2. **Software Launch**
   - Run the application using the `start.sh` script
   - Creates virtual environment and installs dependencies automatically
   - The interface will open with the Connection tab active
   - USB ports will be automatically scanned and populated

### First Connection
1. Select your USB-to-RS485 device from the dropdown
2. Click "Connect" to establish communication
3. Use "Auto Detect" to find your motor ID
4. The status will show "CONNECTED" when successful

---

## Connection Setup

### Port Selection
- **Automatic Detection**: The application scans for USB-to-RS485 devices
- **Manual Selection**: Choose from available serial ports (typically /dev/ttyUSB0)
- **Auto-connect**: Single USB-to-RS485 devices connect automatically

### Motor Detection
- **Auto Detect**: Scans motor IDs 1-10 to find active motors
- **Manual ID**: Set motor ID manually if known (1-10 only)
- **Multiple Motors**: Each motor requires a unique ID

### Connection Status
- **Green "CONNECTED"**: Communication established
- **Red "DISCONNECTED"**: No communication
- **Status Bar**: Shows TX/RX rates and connection health

---

## Motor Control

### Control Modes

#### Velocity Control (Blue Slider)
- **Range**: -330 to +330 RPM
- **Use Case**: Continuous rotation applications
- **Auto-switching**: Automatically activates when velocity slider is used
- **Real-time**: Immediate response to slider changes

#### Position Control (Red Slider)  
- **Range**: 0° to 360°
- **Precision**: 0.1° resolution
- **Use Case**: Precise positioning applications
- **Safety**: Automatically ramps down velocity before switching modes

#### Current Control (Green Slider)
- **Range**: -8A to +8A
- **Use Case**: Torque control applications
- **Safety**: Current limiting protects motor from damage

### Slider Operation
- **Touch-friendly**: Large, color-coded sliders for easy operation
- **Release-based**: Commands sent when slider is released (not during drag)
- **Visual Feedback**: Color-coded backgrounds match graph lines
- **Text Entry**: Manual numeric input with validation

### Mode Switching
- **Automatic**: Modes switch automatically when using different sliders
- **Intelligent**: System handles velocity ramping for safe transitions
- **Visual**: Current mode displayed with matching colors
- **Safety**: Emergency stop works in any mode

---

## Live Monitoring

### Real-time Graph
- **Dual Y-axis**: Left axis for velocity/position, right axis for torque
- **Live Updates**: 20Hz refresh rate for smooth visualization
- **Color Coding**: 
  - Blue: Velocity (RPM)
  - Red: Position (degrees)
  - Cyan: Torque (Amps)
- **Auto-scaling**: Axes automatically adjust to data range
- **Data Source**: Uses same data as Connection tab motor status for consistency
- **No Data Indicator**: Shows "No data received" in red when no motor data available

### Status Display
- **Velocity**: Current motor speed in RPM
- **Position**: Current motor position in degrees
- **Torque**: Current motor torque in Amps
- **Temperature**: Motor temperature with color alerts
- **Communication**: TX/RX rates and connection status

### Data Collection
- **Automatic**: Data collected at 20Hz when motor is connected
- **Shared Source**: Same data pipeline feeds both status display and graph
- **Buffer Management**: 200-point circular buffer for efficient memory usage

---

## Safety Features

### Emergency Stop
- **Big Red Button**: Immediately stops all motor motion
- **All Motors**: Stops motors with IDs 1-10 regardless of current selection
- **Bypass Queue**: Emergency stop bypasses normal command queue
- **Always Active**: Works even during communication errors

### Automatic Safety
- **Velocity Ramping**: Automatic speed reduction before mode changes
- **Temperature Monitoring**: Alerts when motor temperature is high
- **Communication Watchdog**: Detects and recovers from communication errors
- **Error Handling**: Graceful handling of unexpected conditions

### Manual Safety
- **Connection Status**: Always visible connection indicator
- **Mode Display**: Clear indication of current control mode
- **Status Monitoring**: Real-time system health information

---

## Motor ID Management

### Setting Motor ID
- **Widget Location**: Motor Setup section on Connection tab
- **Valid Range**: IDs 1-10 only
- **Protocol**: Uses SET_ID command [0xAA, 0x55, 0x53, new_id, ...]
- **Verification**: Automatically verifies ID change was successful
- **Power Cycle**: May require power cycle for multiple ID changes

### ID Change Process
1. Enter new motor ID (1-10) in Motor Setup widget
2. Click "Set ID" button
3. System sends SET_ID command 5 times as required by protocol
4. Verification feedback request sent with new ID
5. Success/failure status displayed

### Multi-Motor Support
- **Unique IDs**: Each motor must have unique ID on same RS485 bus
- **ID Scanning**: Auto-detect scans all IDs 1-10
- **Individual Control**: Switch between motors using Motor ID dropdown

---

## Troubleshooting

### Graph Issues
- **No data showing**: Check motor connection and ensure data appears in Connection tab
- **"No data received"**: Verify motor communication, check Connection tab status
- **Graph frozen**: Restart application, check matplotlib installation

### Motor ID Issues
- **ID change fails**: Verify motor power, check RS485 connections
- **Multiple changes fail**: Power cycle motor between ID changes
- **Wrong motor responds**: Check for ID conflicts, scan for active motors

### Connection Problems
- **Port not found**: Check USB-RS485 adapter connection, install drivers
- **Connection timeout**: Verify motor power supply, check wiring
- **Intermittent connection**: Check cable integrity, reduce RS485 cable length

### Diagnostics
- **Motor Test**: Comprehensive motor functionality test
- **Communication Test**: Verifies RS485 communication
- **Movement Test**: Confirms motor responds to commands
- **System Health**: Complete system diagnostic report

### Multi-motor Support
- **Motor Scanning**: Automatically detects all connected motors
- **ID Management**: Easy switching between motor IDs
- **Individual Control**: Each motor controlled independently
- **Status Monitoring**: Monitor multiple motors simultaneously

### Robust Operation
- **Error Recovery**: Automatic recovery from communication errors
- **Long-term Stability**: Designed for weeks of continuous operation
- **Exception Handling**: Comprehensive error handling prevents crashes
- **Graceful Shutdown**: Clean disconnection and resource cleanup

---

## Tips for Best Operation

### Performance Optimization
- Use release-based slider control for smooth operation
- Monitor temperature to prevent overheating
- Ensure stable power supply for consistent performance
- Keep RS485 cables short and properly shielded

### Maintenance
- Regularly check connection status
- Monitor motor temperature during operation
- Verify communication rates are stable
- Test emergency stop functionality periodically

### Troubleshooting Quick Start
1. Check all cable connections
2. Verify power supply voltage and capacity
3. Confirm motor ID settings
4. Test with different USB ports if needed
5. Use diagnostic function to identify issues

This interface is designed for both novice and expert users, providing
simple operation with advanced capabilities when needed.