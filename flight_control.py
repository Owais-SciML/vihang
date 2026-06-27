# flight_control.py
import numpy as np
import time
import threading
from hal import HardwareController
from config import MOTOR_PINS, SERVO_PIN, HOVER_BASE_THRUST

class VectorPID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp, self.Ki, self.Kd = np.array(Kp), np.array(Ki), np.array(Kd)
        self.integral = np.zeros(3)
        self.last_error = np.zeros(3)

    def compute(self, target, current, dt):
        error = target - current
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        self.last_error = error
        return (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

class FlightController:
    def __init__(self):
        self.hal = HardwareController(MOTOR_PINS, SERVO_PIN)
        self.pid = VectorPID([2.0, 1.0, 1.0], [0.1, 0.01, 0.01], [1.5, 0.8, 0.8])
        
        # State: [Altitude, Roll, Pitch]
        self.target_state = np.array([10.0, 0.0, 0.0])
        self.current_state = np.array([10.0, 0.0, 0.0]) 
        
        # Mixer maps [Alt_Corr, Roll_Corr, Pitch_Corr] -> [FL, FR, BR, BL]
        self.MIXER = np.array([
            [1,  1,  1],  # FL
            [1, -1,  1],  # FR
            [1, -1, -1],  # BR
            [1,  1, -1]   # BL
        ])
        
        self.running = False
        self.servo_angle = 0.0

    def process_command(self, direction):
        """Translates high-level web commands into target state changes."""
        if direction == "up":       self.target_state[0] += 1.0
        elif direction == "down":   self.target_state[0] -= 1.0
        elif direction == "right":  self.target_state[1] += 5.0
        elif direction == "left":   self.target_state[1] -= 5.0
        elif direction == "forward":self.target_state[2] += 5.0
        elif direction == "backward":self.target_state[2] -= 5.0
        
        # Auxiliary servo control for wings/camera
        if direction == "right": self.servo_angle += 10
        elif direction == "left": self.servo_angle -= 10
        self.hal.set_servo_angle(self.servo_angle)

    def control_loop(self):
        self.running = True
        last_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                if dt < 0.02: # Target ~50Hz loop
                    time.sleep(0.02 - dt)
                    continue
                last_time = current_time

                # In a real system, self.current_state would be updated here by reading an IMU/Kalman filter.
                
                # 1. Compute PID corrections
                corrections = self.pid.compute(self.target_state, self.current_state, dt)
                
                # 2. Mix outputs for 4 motors
                motor_cmds = HOVER_BASE_THRUST + (self.MIXER @ corrections)
                
                # 3. Apply limits and write to HAL
                self.hal.set_motor_thrust("FL", motor_cmds[0])
                self.hal.set_motor_thrust("FR", motor_cmds[1])
                self.hal.set_motor_thrust("BR", motor_cmds[2])
                self.hal.set_motor_thrust("BL", motor_cmds[3])

        except Exception as e:
            print(f"Flight control error: {e}")
        finally:
            self.hal.stop_all()

    def start(self):
        threading.Thread(target=self.control_loop, daemon=True).start()

    def stop(self):
        self.running = False