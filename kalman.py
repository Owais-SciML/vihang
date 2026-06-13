import numpy as np

# ==========================================
# 1. THE BRAIN: VECTORIZED PID CONTROLLER
# ==========================================
class VectorPID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = np.array(Kp)
        self.Ki = np.array(Ki)
        self.Kd = np.array(Kd)
        self.integral = np.zeros(3)
        self.last_error = np.zeros(3)

    def compute(self, target, current, dt):
        error = target - current
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        self.last_error = error
        return (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

# ==========================================
# 2. FLIGHT CONTROLLER & MATRICES
# ==========================================
target_state = np.array([10.0, 0.0, 0.0])
current_state = np.array([8.5, 15.0, -5.0]) 

velocity = np.zeros(3)

# Tuned to prevent twitchy overcorrections
pid = VectorPID(
    Kp=[2.0, 1.0, 1.0],
    Ki=[0.1, 0.01, 0.01],
    Kd=[1.5, 0.8, 0.8]
)

hover_base_thrust = 50.0

# MIXER MATRIX (4x3): Maps [Alt_Corr, Roll_Corr, Pitch_Corr] -> [Motor A, B, C, D]
MIXER = np.array([
    [1,  1,  1],  # Motor A (Front-Left)
    [1, -1,  1],  # Motor B (Front-Right)
    [1, -1, -1],  # Motor C (Back-Right)
    [1,  1, -1]   # Motor D (Back-Left)
])

# PHYSICS MATRIX (3x4): Maps [Motor A, B, C, D] -> [Lift, Roll_Moment, Pitch_Moment]
# **FIXED**: The signs correctly counteract the tilt!
PHYSICS = np.array([
    [ 1,  1,  1,  1], # Lift Force
    [ 1, -1, -1,  1], # Roll Moment  (A - B - C + D) -> Right motors push angle negative
    [ 1,  1, -1, -1]  # Pitch Moment (A + B - C - D) -> Front motors push angle positive
])

# Physics constants
dt = 0.05 # Smaller time step for stable physics integration
damping = 0.9
force_scalars = np.array([0.05, 0.2, 0.2]) 
noise_std_dev = np.array([0.02, 0.05, 0.05])

# ==========================================
# 3. THE DYNAMIC SIMULATION LOOP
# ==========================================
print("--- WIND GUST DETECTED ---")
print(f"Initial State: {current_state}\n")

step = 0
success = False

while True:
    step += 1
    
    noisy_sensors = current_state + np.random.normal(0, noise_std_dev)
    corrections = pid.compute(target_state, noisy_sensors, dt)
    motor_cmds = hover_base_thrust + (MIXER @ corrections)
    
    forces = PHYSICS @ motor_cmds
    forces[0] -= hover_base_thrust * 4 
    
    velocity = (velocity + (forces * force_scalars) * dt) * damping
    current_state += velocity * dt
    
    if step % 10 == 0:
        print(f"Loop {step:02d} | Alt: {current_state[0]:5.2f}m | Roll: {current_state[1]:5.2f}° | Pitch: {current_state[2]:5.2f}°")
        
    # Check if error is successfully neutralized
    if np.all(np.abs(target_state - current_state) < 0.2):
        success = True
        break
        
    if step > 200:
        break

if success:
    print("\n---  STABILIZATION COMPLETE ---")
else:
    print("\n---  SIMULATION FAILED (DIVERGED) ---")

print(f"Final State:   {np.round(current_state, 2)}")
print(f"Motors Output: {np.round(motor_cmds, 1)}")
