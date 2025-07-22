# DDSM115 Motor Control System Architecture

## System Overview

The DDSM115 Motor Control System is a comprehensive GUI application for controlling DDSM115 servo motors via RS485 communication. The system follows a layered architecture with clear separation of concerns.

```mermaid
graph TB
    subgraph "User Interface Layer"
        GUI[SimpleDDSM115GUI<br/>Main GUI Application]
        GRAPH[Live Graph Display]
        TABS[Tab System<br/>Connection/Control/About]
    end
    
    subgraph "Application Layer"
        MCQ[MotorCommandQueue<br/>Command Management]
        MDM[MotorDataManager<br/>Data Distribution]
        CB[Callback System]
    end
    
    subgraph "Communication Layer"
        DDSM[DDSM115<br/>Motor Protocol]
        RS485[RS485 Serial<br/>Communication]
    end
    
    subgraph "Hardware Layer"
        USB[USB-RS485 Adapter]
        MOTOR[DDSM115 Motor]
    end
    
    GUI --> MCQ
    GUI --> GRAPH
    GUI --> TABS
    GRAPH --> CB
    MCQ --> CB
    CB --> MDM
    MCQ --> DDSM
    DDSM --> RS485
    RS485 --> USB
    USB --> MOTOR
```

## Component Architecture

### 1. User Interface Layer

#### SimpleDDSM115GUI (Main Application)
- **Purpose**: Main application window and UI management
- **Responsibilities**:
  - Window management and custom controls
  - Tab navigation (Connection, Control, About)
  - User input handling
  - Real-time status display
  - Theme and styling management

#### Live Graph Display
- **Purpose**: Real-time visualization of motor data
- **Features**:
  - Matplotlib integration with Tkinter
  - Dual Y-axis for velocity/position and torque
  - Configurable display options
  - Automatic scaling and updates
  - "No data received" indicator

#### Tab System
- **Connection Tab**: Port selection, motor detection, communication setup
- **Control Tab**: Motor control modes, live graph, command interface
- **About Tab**: System information, diagnostics, documentation

### 2. Application Layer

#### MotorCommandQueue
- **Purpose**: Manages command flow and feedback collection
- **Key Features**:
  - Thread-safe command queuing
  - Automatic feedback collection at 20Hz
  - Callback system for data distribution
  - Error handling and recovery
  - Connection state management

#### MotorDataManager
- **Purpose**: Centralized data distribution hub
- **Architecture**:
  - Observer pattern implementation
  - Queue-based event distribution
  - Support for multiple listeners
  - Thread-safe data access

#### Callback System
- **Purpose**: Event-driven data flow
- **Callbacks**:
  - `on_feedback`: Motor feedback data
  - `on_error`: Error notifications
  - `on_command_sent`: Command confirmations

### 3. Communication Layer

#### DDSM115 Protocol Implementation
- **Purpose**: Motor protocol handling
- **Features**:
  - 10-byte packet format with CRC8
  - Command types: Velocity, Current, Position, Emergency Stop
  - Motor ID management (1-10)
  - Feedback request/response handling
  - Mode switching logic

#### RS485 Serial Communication
- **Configuration**:
  - Baudrate: 115200
  - Timeout: 200ms
  - Half-duplex communication
  - Binary protocol

### 4. Hardware Layer

#### USB-RS485 Adapter
- Converts USB to RS485 signals
- Supports multiple motors on single bus
- Auto-detection via serial port enumeration

#### DDSM115 Motor
- Direct drive servo motor
- 12-24V DC operation
- RS485 communication interface
- Built-in encoder and controller

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant UI as GUI
    participant MCQ as MotorCommandQueue
    participant CB as Callbacks
    participant DDSM as DDSM115
    participant M as Motor
    
    UI->>MCQ: User Command
    MCQ->>DDSM: Queue Command
    DDSM->>M: RS485 Packet
    
    loop Feedback Collection (20Hz)
        MCQ->>DDSM: Request Feedback
        DDSM->>M: Feedback Request
        M->>DDSM: Feedback Data
        DDSM->>MCQ: Process Response
        MCQ->>CB: Trigger Callback
        CB->>UI: Update Display
    end
```

## Threading Model

```mermaid
graph TD
    subgraph "Main Thread"
        GUI[GUI Event Loop]
        UPDATE[Display Updates]
    end
    
    subgraph "Background Threads"
        FEEDBACK[Feedback Worker<br/>20Hz Collection]
        MONITOR[Monitor Loop<br/>Status Updates]
    end
    
    subgraph "Thread Communication"
        QUEUE[Thread-Safe Queues]
        CALLBACK[Callback System]
    end
    
    FEEDBACK --> QUEUE
    MONITOR --> QUEUE
    QUEUE --> CALLBACK
    CALLBACK --> GUI
    GUI --> UPDATE
```

## Class Hierarchy

```mermaid
classDiagram
    class SimpleDDSM115GUI {
        +motor_controller: MotorCommandQueue
        +plot_time: deque
        +plot_velocity: deque
        +plot_position: deque
        +plot_torque: deque
        +create_connection_tab()
        +create_control_tab()
        +create_about_tab()
        +update_graph()
        -_on_motor_feedback()
    }
    
    class MotorCommandQueue {
        +motor: DDSM115
        +is_connected: bool
        +on_feedback: Callable
        +on_error: Callable
        +connect()
        +disconnect()
        +set_velocity()
        +set_position()
        +set_current()
        +emergency_stop()
        +set_motor_id()
        -_feedback_worker()
    }
    
    class DDSM115 {
        +serial_port: Serial
        +current_mode: Dict
        +connect()
        +disconnect()
        +send_packet()
        +request_feedback()
        +set_mode()
        +scan_motors()
        +set_motor_id()
    }
    
    class MotorDataManager {
        +listeners: Dict
        +add_listener()
        +remove_listener()
        +distribute_data()
        -_process_events()
    }
    
    class MotorFeedback {
        +motor_id: int
        +velocity: float
        +position: float
        +torque: float
        +temperature: int
        +raw_data: List
    }
    
    SimpleDDSM115GUI --> MotorCommandQueue
    MotorCommandQueue --> DDSM115
    MotorCommandQueue --> MotorFeedback
    SimpleDDSM115GUI --> MotorDataManager
    MotorDataManager --> MotorFeedback
```

## Key Design Patterns

### 1. Observer Pattern
- Used in callback system and data distribution
- Decouples data producers from consumers
- Enables multiple UI components to receive updates

### 2. Command Pattern
- MotorCommandQueue implements command queuing
- Enables undo/redo capabilities
- Provides command history and logging

### 3. Singleton Pattern
- Serial port management ensures single connection
- Prevents resource conflicts

### 4. Factory Pattern
- Motor creation and initialization
- Configurable motor types and protocols

## Performance Considerations

### Data Collection
- Feedback collection at 20Hz per motor
- Circular buffers (deque) limit memory usage
- Maximum 200 data points for graph display

### Thread Safety
- Queue-based communication between threads
- Minimal lock contention
- GUI updates scheduled on main thread

### Resource Management
- Automatic cleanup on disconnection
- Graceful error handling
- Connection state monitoring

## Security Considerations

### Input Validation
- Motor ID range checking (1-10)
- Command parameter validation
- Serial port access control

### Error Handling
- Timeout protection
- CRC validation
- Connection loss recovery

### Safety Features
- Emergency stop functionality
- Mode switching protection
- Temperature monitoring

## Future Architecture Enhancements

### Planned Improvements
1. Plugin system for custom motor types
2. Remote control API
3. Data logging and replay
4. Multi-motor synchronized control
5. Advanced trajectory planning

### Scalability Considerations
- Support for larger motor networks
- Distributed control architecture
- Cloud-based monitoring
- Mobile app integration