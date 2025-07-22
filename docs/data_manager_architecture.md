# Motor Data Manager Architecture

## Overview

The Motor Data Manager provides a centralized, queue-based architecture for motor communication and data distribution. This design separates data collection from consumption, allowing multiple components to receive motor data independently.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Motor Data Manager                           │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐ │
│  │  Motor Control  │    │           Data Distribution          │ │
│  │                 │    │                                      │ │
│  │ • Serial Comm   │    │  ┌─────────────────────────────────┐ │ │
│  │ • Command Queue │────┤  │         Event Router            │ │ │
│  │ • Feedback      │    │  │  • Motor ID Filtering          │ │ │
│  │ • Error Handle  │    │  │  • Event Type Filtering        │ │ │
│  └─────────────────┘    │  │  • Queue Management             │ │ │
│                         │  └─────────────────────────────────┘ │ │
│                         └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
        ┌─────────────────────┐ ┌──────────────────┐ ┌─────────────────────┐
        │   Graph Listener    │ │  UI Listener     │ │  Custom Listeners   │
        │                     │ │                  │ │                     │
        │ • Plot Data Storage │ │ • Status Updates │ │ • Logging           │
        │ • Multi-Motor Data  │ │ • Command Status │ │ • Alerts            │
        │ • Time Series       │ │ • Connection     │ │ • Data Recording    │
        │ • Auto-scaling      │ │   Status         │ │ • Analysis          │
        └─────────────────────┘ └──────────────────┘ └─────────────────────┘
                    │                   │                   │
                    ▼                   ▼                   ▼
        ┌─────────────────────┐ ┌──────────────────┐ ┌─────────────────────┐
        │  Matplotlib Graph   │ │   Tkinter UI     │ │   Custom Components │
        │                     │ │                  │ │                     │
        │ • Real-time Plot    │ │ • Status Display │ │ • Log Files         │
        │ • Multiple Motors   │ │ • Controls       │ │ • CSV Export        │
        │ • Auto-refresh      │ │ • Motor Select   │ │ • Web Dashboard     │
        └─────────────────────┘ └──────────────────┘ └─────────────────────┘
```

## Key Components

### 1. Motor Data Manager (`MotorDataManager`)

**Responsibilities:**
- Centralized motor communication
- Event generation and distribution
- Motor state tracking
- Command execution
- Connection management

**Key Features:**
- Thread-safe operation
- Automatic motor discovery
- Connection monitoring
- Statistics tracking
- Error handling

### 2. Data Events (`DataEvent`)

**Event Types:**
- `MOTOR_FEEDBACK` - Real-time motor data
- `MOTOR_STATUS_CHANGE` - Connection status changes  
- `MOTOR_ERROR` - Communication or hardware errors
- `COMMAND_SENT` - Successful command execution
- `COMMAND_FAILED` - Failed command execution
- `MOTOR_CONNECTED/DISCONNECTED` - Connection events

### 3. Listeners (`MotorDataListener`)

**Base Functionality:**
- Queue-based event reception
- Motor ID filtering
- Event type filtering
- Thread-safe operation
- Automatic cleanup

**Specialized Listeners:**
- `GraphDataListener` - Optimized for real-time graphing
- `UIStatusListener` - UI status updates
- `LoggingListener` - Event logging
- `AlertListener` - Threshold monitoring
- `DataRecorder` - CSV data recording

## Benefits

### 1. **Separation of Concerns**
- Data collection isolated from UI logic
- Each component has single responsibility
- Easy to test and debug individual components

### 2. **Scalability** 
- Add new listeners without modifying existing code
- Multiple graphs can show different motors simultaneously
- Easy to add new data consumers (web interface, etc.)

### 3. **Robustness**
- Queue buffering prevents data loss
- Individual component failures don't affect others
- Thread-safe operation prevents race conditions

### 4. **Flexibility**
- Listeners can filter by motor ID or event type
- Custom processing logic per listener
- Easy to modify or extend functionality

### 5. **Performance**
- Minimal overhead per listener
- Efficient queue-based distribution
- No blocking between components

## Usage Examples

### Basic Setup

```python
from motor_data_manager import MotorDataManager, GraphDataListener, UIStatusListener

# Create manager
manager = MotorDataManager("/dev/ttyUSB0")

# Create listeners
graph_listener = GraphDataListener()
ui_listener = UIStatusListener()

# Register listeners
manager.register_listener(graph_listener)
manager.register_listener(ui_listener)

# Connect and start monitoring
manager.connect()
```

### Graph Integration

```python
def update_graph(frame):
    # Process new events
    graph_listener.process_events()
    
    # Get data for selected motor
    motor_id = selected_motor_var.get()
    plot_data = graph_listener.get_plot_data(motor_id)
    
    if plot_data and plot_data['time']:
        # Update matplotlib with new data
        times = list(plot_data['time'])
        velocities = list(plot_data['velocity'])
        
        velocity_line.set_data(times, velocities)
        ax.relim()
        ax.autoscale_view()
    else:
        # Show "No data" message
        ax.text(0.5, 0.5, f'No data from Motor {motor_id}', 
               transform=ax.transAxes, ha='center', va='center')
```

### Custom Listener

```python
class CustomListener(MotorDataListener):
    def __init__(self):
        super().__init__("custom", queue_size=100)
        self.set_event_filter([DataEventType.MOTOR_FEEDBACK])
        self.start_processing()
    
    def start_processing(self):
        def process_loop():
            while self.active:
                event = self.get_event(timeout=1.0)
                if event:
                    # Custom processing logic
                    self.handle_motor_data(event)
        
        threading.Thread(target=process_loop, daemon=True).start()
    
    def handle_motor_data(self, event):
        # Your custom logic here
        print(f"Motor {event.motor_id}: {event.data['velocity']} RPM")
```

## Migration Guide

### From Existing GUI

1. **Replace direct motor controller calls:**
```python
# Old way
feedback = motor_controller.request_feedback(motor_id)
self.update_graph(feedback)

# New way  
# Data automatically flows to graph_listener
# Graph update gets data from listener
```

2. **Update graph update method:**
```python
def update_graph(self, frame):
    # Process events from listener
    self.graph_listener.process_events()
    
    # Get data for selected motor
    plot_data = self.graph_listener.get_plot_data(self.selected_motor_id.get())
    
    # Update plot with data
    if plot_data:
        # Update matplotlib
        pass
```

3. **Replace status callbacks:**
```python
# Old way - callbacks
motor_controller.on_feedback = self.on_feedback

# New way - event processing
def update_ui(self):
    self.ui_listener.process_events()
    status = self.ui_listener.get_latest_status(motor_id)
    # Update UI elements
```

## Implementation Files

- `src/motor_data_manager.py` - Core data manager and listener classes
- `src/motor_listeners_example.py` - Example listener implementations
- `src/gui_with_data_manager.py` - Example GUI integration
- `docs/data_manager_architecture.md` - This documentation

## Testing

Run the example implementations:

```bash
# Test the data manager with mock data
cd src
python3 motor_listeners_example.py

# Test the GUI integration  
python3 gui_with_data_manager.py
```

## Future Enhancements

1. **Network Distribution** - Add TCP/UDP listeners for remote monitoring
2. **Database Integration** - Add database storage listener
3. **Web Interface** - Add WebSocket listener for web dashboard
4. **Configuration** - Add configuration file support for listener setup
5. **Plugins** - Add dynamic listener loading system