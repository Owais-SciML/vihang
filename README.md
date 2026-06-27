# Autonomous Flying Car - Telemetry & Control Portal

An engineered, full-stack remote monitoring web application portal and localized hardware control system. Built with Python, Flask, and MySQL, this system aggregates live telemetry streams and translates high-level web commands into real-time physical actuations for BLDC motors and servos.

## System Architecture

To ensure flight stability, the architecture strictly separates web server operations from high-frequency hardware control loops:

1. **Web / API Layer (Flask):** Handles secure authentication (OTP via SMTP), MySQL database logging, and exposes RESTful API endpoints for telemetry polling and command ingestion.
2. **Flight Control Thread:** A dedicated daemon thread running a 50Hz control loop. It processes a Vectorized PID controller, utilizes a custom motor mixer matrix for 4-axis flight dynamics, and manages the target-vs-current state.
3. **Hardware Abstraction Layer (HAL):** Utilizes `pigpio` to translate mathematical thrust/angle calculations into precise microsecond PWM pulses for Electronic Speed Controllers (ESCs) and Servos.
4. **Telemetry Ingestion:** A modular subsystem designed to aggregate active sensor data feeds (IMU, Altimeter) into the main control loop.

## Features
* **Secure Access:** Two-factor OTP authentication with active session logging to MySQL.
* **Live Dashboard:** Asynchronous JavaScript UI for real-time telemetry monitoring (Altitude, Pitch, Roll) without page reloads.
* **Asynchronous Hardware Control:** Non-blocking API routes that update flight target states safely.
* **Vectorized PID & Mixing:** Mathematical translation of high-level directions (Pitch/Roll/Yaw) to specific 4-motor outputs.

## Hardware Requirements
* Raspberry Pi (Running Raspberry Pi OS)
* 4x Electronic Speed Controllers (ESCs) + BLDC Motors
* Servos (for auxiliary control/vectoring)
* *Optional:* MPU6050 IMU for real hardware telemetry.

## Software Prerequisites
* Python 3.8+
* MySQL Server
* `pigpiod` daemon running on the host machine

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Owais-SciML/vihang
   cd vihang
