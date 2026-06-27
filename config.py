# config.py

# MySQL Setup
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Owais's_pass",
    "database": "flask"
}

# Hardware Pins (BCM)
MOTOR_PINS = {
    "FL": 17, # Front-Left
    "FR": 18, # Front-Right
    "BR": 27, # Back-Right
    "BL": 22  # Back-Left
}
SERVO_PIN = 23

# PWM Settings
MIN_US = 1000
MAX_US = 2000
HOVER_BASE_THRUST = 50.0  # Percentage