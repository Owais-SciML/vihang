# hal.py
import pigpio
from config import MIN_US, MAX_US

class HardwareController:
    def __init__(self, motor_pins, servo_pin):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not running. Run: sudo pigpiod")
        
        self.motors = motor_pins
        self.servo = servo_pin
        
        # Initialize pins
        for pin in self.motors.values():
            self.pi.set_servo_pulsewidth(pin, MIN_US)
        self.pi.set_servo_pulsewidth(self.servo, 0)

    def set_motor_thrust(self, motor_key, percentage):
        """Map 0-100% thrust to PWM pulse width."""
        p = max(0.0, min(100.0, float(percentage)))
        pulse = int(MIN_US + (p / 100.0) * (MAX_US - MIN_US))
        self.pi.set_servo_pulsewidth(self.motors[motor_key], pulse)

    def set_servo_angle(self, angle):
        """Map -90 to +90 degrees to servo pulse width."""
        MIN_PW, MAX_PW = 600, 2300
        angle = max(-90.0, min(90.0, float(angle)))
        pw = int(MIN_PW + (angle + 90) * (MAX_PW - MIN_PW) / 180)
        self.pi.set_servo_pulsewidth(self.servo, pw)

    def stop_all(self):
        for pin in self.motors.values():
            self.pi.set_servo_pulsewidth(pin, MIN_US)
        self.pi.set_servo_pulsewidth(self.servo, 0)
        self.pi.stop()