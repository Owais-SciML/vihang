# app.py
from flask import Flask, request, jsonify, render_template, session
from flight_control import FlightController
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "random_secret_key_#@$Owais"

# Initialize and start the background flight controller
fc = FlightController()
fc.start()

@app.route("/control", methods=["GET"])
def control():
    # if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401

    direction = request.args.get("direction", "").lower()
    valid_commands = ["up", "down", "left", "right", "forward", "backward"]
    
    if direction in valid_commands:
        fc.process_command(direction)
        msg = f"Command '{direction}' executed. Target state updated."
    else:
        msg = "Unknown command"
        
    return jsonify({
        "message": msg,
        "target_state": fc.target_state.tolist(),
        "servo_angle": fc.servo_angle
    })

@app.route("/telemetry", methods=["GET"])
def telemetry():
    """Endpoint for the frontend to poll live sensor data."""
    return jsonify({
        "altitude": fc.current_state[0],
        "roll": fc.current_state[1],
        "pitch": fc.current_state[2],
        "target_alt": fc.target_state[0]
    })

# ... (Keep your existing Auth, MySQL logging, and OTP routes here) ...

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=False) 
        # debug=False is crucial here; Flask debug mode restarts the script and will crash pigpio.
    finally:
        fc.stop()