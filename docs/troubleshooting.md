# DDSM115 Troubleshooting Guide

## Quick Diagnostic Checklist

### ❌ Cannot Connect to Motor
**Symptoms**: Connection status shows "DISCONNECTED", no response from motor

**Solutions**:
1. **Check Physical Connections**
   - Verify USB-to-RS485 adapter is plugged in
   - Confirm RS485 wiring: A+ to A+, A- to A-, B+ to B+, B- to B-
   - Ensure motor power supply is connected and switched on
   - Check for loose connections and proper grounding

2. **Verify Port Selection**
   - Try "Refresh Ports" to rescan available ports
   - Select correct USB-to-RS485 device from dropdown
   - Try different USB ports on computer
   - Check if device appears in system device manager

3. **Test Communication Settings**
   - Verify motor is configured for correct baud rate (115200)
   - Check motor ID settings (default usually 1)
   - Try different motor IDs using "Auto Detect"

---

### ⚠️ Motor Detected But Not Responding
**Symptoms**: Motor found during scan but doesn't move when commanded

**Solutions**:
1. **Check Motor State**
   - Use "Diagnose" function to test motor systematically
   - Verify motor is enabled (not in fault state)
   - Check temperature - motor may be in thermal protection

2. **Power Supply Issues**
   - Verify power supply can provide sufficient current (8A+ continuous)
   - Check voltage is within motor specifications (12-24V)
   - Ensure power supply connections are secure

3. **Mechanical Issues**
   - Check for mechanical binding or excessive load
   - Verify motor shaft/wheel can rotate freely
   - Ensure motor mounting is secure

---

### 📊 Graph Not Updating or Freezing
**Symptoms**: Live graph stops updating, shows flat lines

**Solutions**:
1. **Check Communication**
   - Verify TX/RX rates in status bar are non-zero
   - Look for communication error messages
   - Try disconnecting and reconnecting

2. **Software Issues**
   - Close and restart the application
   - Check available system memory
   - Try reducing graph update rate

---

### 🎛️ Sliders Not Working Properly
**Symptoms**: Moving sliders doesn't control motor, or control is erratic

**Solutions**:
1. **Check Mode Switching**
   - Verify current mode display matches expected control
   - Allow time for mode transitions to complete
   - Try manual mode switching before using sliders

2. **Communication Timing**
   - Use release-based control (don't drag continuously)
   - Allow brief pauses between commands
   - Check for command queue overload in status

---

### 🌡️ Temperature Warnings
**Symptoms**: High temperature readings, thermal protection activation

**Solutions**:
1. **Immediate Actions**
   - Reduce motor load or duty cycle
   - Allow motor to cool before continuing operation
   - Check for adequate ventilation around motor

2. **Long-term Solutions**
   - Verify motor is not overloaded for application
   - Check ambient temperature conditions
   - Consider active cooling for high-duty applications

---

### ⚡ Emergency Stop Not Working
**Symptoms**: E-stop button doesn't immediately stop motor

**Solutions**:
1. **Immediate Safety**
   - Remove power from motor immediately
   - Check physical emergency stop switches if installed
   - Verify motor brake engagement (if equipped)

2. **Software Issues**
   - Restart application to clear any software locks
   - Check communication is working before relying on software E-stop
   - Verify emergency stop bypasses normal command queue

---

## When to Contact Support

Contact technical support if:
- Multiple troubleshooting steps don't resolve the issue
- Hardware damage is suspected
- Motor behavior is inconsistent with specifications
- Safety-critical applications require verification

For official documentation and support, visit the manufacturer page:
**Waveshare DDSM115**: https://www.waveshare.com/wiki/DDSM115

Remember: When in doubt, prioritize safety. Use physical emergency stops
and power disconnection for immediate safety in any uncertain situation.