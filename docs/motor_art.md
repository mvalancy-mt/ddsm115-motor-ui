# DDSM115 HUB MOTOR
## Servo Motor Controller

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                      DDSM115 HUB MOTOR                                           ║
║                                   Servo Motor Controller                                         ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

                                    ╭─────────────────────╮
                                    │    RS485 Interface │
                                    │   ┌─────────────┐   │
                                    │   │  TX    RX   │   │
                            ┌───────┤   │   A+  A-    │   ├───────┐
                            │       │   │   B+  B-    │   │       │
                    ┌───────┴───┐   │   └─────────────┘   │   ┌───┴───────┐
                    │    CAN    │   ╰─────────────────────╯   │  ENCODER  │
                    │  BUS I/O  │                             │   HALL    │
                    └───────────┘        ╭───────────╮        │  SENSORS  │
                                         │  CONTROL  │        └───────────┘
                 ╔══════════════════════════════════════════════════════════════════════╗
                 ║                      MOTOR HOUSING (HUB)                             ║
                 ║   ╔════════════════════════════════════════════════════════════╗     ║
                 ║   ║                    STATOR WINDINGS                         ║     ║
                 ║   ║                                                            ║     ║
                 ║   ║    Phase A  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐  Phase A             ║     ║
                 ║   ║             │ │ │ │ │ │ │ │ │ │ │ │ │                      ║     ║
                 ║   ║    Phase B  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤  Phase B             ║     ║
                 ║   ║             │ │ │ │ │ │ │ │ │ │ │ │ │                      ║     ║
                 ║   ║    Phase C  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘  Phase C             ║     ║
                 ║   ║                                                            ║     ║
                 ║   ║              ╔═══════════════════════╗                     ║     ║
                 ║   ║              ║     ROTOR MAGNET      ║                     ║     ║
                 ║   ║              ║                       ║                     ║     ║
                 ║   ║              ║   N  S  N  S  N  S    ║                     ║     ║
                 ║   ║              ║   │  │  │  │  │  │    ║                     ║     ║
                 ║   ║              ║   └──┼──┼──┼──┼──┘    ║                     ║     ║
                 ║   ║              ║      │  │  │  │       ║                     ║     ║
                 ║   ║              ║   ┌──┼──┼──┼──┼──┐    ║                     ║     ║
                 ║   ║              ║   │  │  │  │  │  │    ║                     ║     ║
                 ║   ║              ║   S  N  S  N  S  N    ║                     ║     ║
                 ║   ║              ║                       ║                     ║     ║
                 ║   ║              ╚═══════════════════════╝                     ║     ║
                 ║   ║                                                            ║     ║
                 ║   ╚════════════════════════════════════════════════════════════╝     ║
                 ╚══════════════════════════════════════════════════════════════════════╝
                                                    ║                                       
                                                    ║                                       
                                               ┌────▼────┐                                 
                                               │  WHEEL  │                               
                                               │  MOUNT  │                              
                                               └─────────┘                               
```

## Official Technical Specifications

*Source: [Waveshare DDSM115 Official Documentation](https://www.waveshare.com/wiki/DDSM115)*

| Parameter | Value |
|-----------|-------|
| **Performance** | |
| No-load speed | 200±10rpm |
| No-load current | ≦0.25A |
| Rated speed | 115rpm |
| Rated torque | 0.96Nm |
| Rated current | 1.5A |
| Maximum efficiency | ≥60% |
| Locked-rotor torque | 2.0Nm |
| Locked-rotor current | ≦2.7A |
| **Electrical** | |
| Rated voltage | 18V DC (5S LiPo) |
| Voltage range | 12-24V DC |
| Torque constant | 0.75Nm/A |
| Speed constant | 11.1rpm/V |
| **Mechanical** | |
| Total weight | 765±15g |
| Single-wheel load | 10kg |
| Noise level | ≦50dB |
| Operating temperature | -20~45℃ |
| Degree of protection | IP54 |
| **Control & Communication** | |
| Encoder resolution | 4096 |
| Relative accuracy | 1024 |
| Communication | RS485 (Custom protocol) |
| Control modes | Velocity, Position, Current (Torque) |
| Motor type | Brushless DC (BLDC) Hub Motor |