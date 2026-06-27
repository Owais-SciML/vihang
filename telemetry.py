# telemetry.py
import smbus # type: ignore
import math
import time

class TelemetrySystem:
    def __init__(self):
        # Setup I2C bus (Standard for Raspberry Pi)
        self.bus = smbus.SMBus(1)
        
        # Default I2C address for MPU6050 IMU
        self.device_address = 0x68 
        
        try:
            # Wake up the MPU6050 (writes 0 to the power management register)
            self.bus.write_byte_data(self.device_address, 0x6B, 0)
            self.sensor_ready = True
            print("IMU Connected successfully.")
        except Exception as e:
            print(f"Failed to connect to IMU: {e}. Check I2C wiring.")
            self.sensor_ready = False

    def _read_raw_data(self, addr):
        """Helper to read 16-bit raw data from the I2C register."""
        high = self.bus.read_byte_data(self.device_address, addr)
        low = self.bus.read_byte_data(self.device_address, addr+1)
        
        # Combine high and low bytes
        value = ((high << 8) | low)
        
        # Get signed value from MPU6050
        if value > 32768:
            value = value - 65536
        return value

    def get_live_data(self):
        """Grabs live Pitch and Roll from the drone's hardware."""
        if not self.sensor_ready:
            # Safe fallback if wires disconnect mid-flight
            return [0.0, 0.0, 0.0] 

        try:
            # Read Accelerometer raw values
            acc_x = self._read_raw_data(0x3B)
            acc_y = self._read_raw_data(0x3D)
            acc_z = self._read_raw_data(0x3F)

            # Convert to G-force
            Ax = acc_x / 16384.0
            Ay = acc_y / 16384.0
            Az = acc_z / 16384.0

            # Calculate exact Roll and Pitch in degrees
            roll = math.degrees(math.atan2(Ay, Az))
            pitch = math.degrees(math.atan2(-Ax, math.sqrt(Ay**2 + Az**2)))
            
            # Note: A basic IMU doesn't do altitude. You'd need a BMP280 barometer for that.
            altitude = 0.0 

            return [altitude, roll, pitch]
            
        except Exception as e:
            print(f"Sensor read error: {e}")
            return [0.0, 0.0, 0.0]