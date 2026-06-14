from flask import Flask, request, redirect, url_for, render_template_string, session, flash, jsonify
import smtplib
import numpy as np
import time
import mysql.connector

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret"  # change for production

# --- Global variable as requested ---
receiver_email = None  # will be set when user submits login form

# --- SMTP sender credentials ---
email = "hackkali1295@gmail.com"
smtp_password = "sdbq syla dpib nhqa" 

# --- MySQL Configuration ---
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password_here",  # <-- Put your MySQL password here
    "database": "flask"
}

# --- Templates ---
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <title>Login</title>
</head>
<body>
  <h2>Enter Email & Name</h2>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul style="color:red;">
      {% for m in messages %}<li>{{m}}</li>{% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="post" action="{{ url_for('send_otp') }}">
    Email:<br>
    <input type="email" name="email" required><br><br>
    Name:<br>
    <input type="text" name="name" required><br><br>
    <button type="submit">Authenticate</button>
  </form>
</body>
</html>
"""

VERIFY_HTML = """
<!doctype html>
<html>
<head>
  <title>Enter OTP</title>
</head>
<body>
  <h2>Verify OTP</h2>
  <p>OTP sent to: <strong>{{ email_display }}</strong></p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul style="color:red;">
      {% for m in messages %}<li>{{m}}</li>{% endfor %}
      </ul>
    {% endif %}
  {% endwith %}

  <form method="post" action="{{ url_for('verify_otp') }}">
    <input type="hidden" name="email" value="{{ email_display }}">
    Enter OTP: <input type="text" name="otp" pattern="\\d{6}" required><br><br>
    <button type="submit">Continue</button>
  </form>

  <form method="get" action="{{ url_for('change_email') }}" style="margin-top:1rem;">
    <button type="submit">Change email</button>
  </form>
</body>
</html>
"""

MAIN_HTML = """
<!doctype html>
<html>
<head>
  <title>Main Page</title>
  <style>
    .control-panel { margin: 20px 0; }
    .btn { padding: 10px 20px; margin: 5px; font-size: 16px; cursor: pointer; }
    #terminal-box { margin-top: 20px; padding: 10px; background: #222; color: #00ff00; width: 300px; min-height: 50px; font-family: monospace; }
  </style>
</head>
<body>
  <h2>Main Page</h2>
  <p>Welcome, {{ name }} ({{ email }})</p>
  
  <div class="control-panel">
    <button class="btn" onclick="sendCommand('up')">Up</button>
    <button class="btn" onclick="sendCommand('down')">Down</button>
    <button class="btn" onclick="sendCommand('left')">Left</button>
    <button class="btn" onclick="sendCommand('right')">Right</button>
  </div>

  <h3>Webpage Console Output:</h3>
  <div id="terminal-box">Waiting for command...</div>

  <p style="margin-top: 30px;"><a href="{{ url_for('logout') }}">Logout</a></p>

  <script>
    function sendCommand(direction) {
      fetch('/control?direction=' + direction)
        .then(response => response.json())
        .then(data => {
          document.getElementById('terminal-box').innerText = data.message;
        })
        .catch(error => console.error('Error:', error));
    }
  </script>
</body>
</html>
"""

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)

@app.route("/send_otp", methods=["POST"])
def send_otp():
    global receiver_email
    name = request.form.get("name", "").strip()
    recv = request.form.get("email", "").strip().lower()

    if not name or not recv:
        flash("Name and email required")
        return redirect(url_for("index"))

    receiver_email = recv
    session["pending_name"] = name
    session["pending_email"] = recv

    otp = np.random.randint(100000, 1000000)  # 6-digit
    session["pending_otp"] = str(int(otp))  
    session["otp_time"] = int(time.time())   

    subject = "ALert !!! "
    message = "your otp is : ", otp
    message = ''.join(map(str, message))
    text = f"Subject: {subject}\n\n{message}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, smtp_password)
        server.sendmail(email, receiver_email, text)
        server.quit()
        print("Email has been sent to " + receiver_email)
    except Exception as e:
        flash(f"Failed to send OTP email: {e}")
        return redirect(url_for("index"))

    return redirect(url_for("verify"))

@app.route("/verify", methods=["GET"])
def verify():
    email_display = session.get("pending_email")
    if not email_display:
        return redirect(url_for("index"))
    return render_template_string(VERIFY_HTML, email_display=email_display)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    entered = request.form.get("otp", "").strip()
    stored = session.get("pending_otp")
    if not stored:
        flash("No OTP pending. Please authenticate again.")
        return redirect(url_for("index"))

    if entered == stored:
        verified_name = session.get("pending_name")
        verified_email = session.get("pending_email")

        # --- Save to MySQL Database ---
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Parametric query to prevent SQL Injection. 
            # ON DUPLICATE KEY UPDATE handles existing entries gracefully.
            query = """
                INSERT INTO user (name, email) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE name = %s
            """
            cursor.execute(query, (verified_name, verified_email, verified_name))
            conn.commit()
            
            print(f"Successfully database-logged: {verified_name} ({verified_email})")
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            flash("Database verification log failed, but you are logged in.")
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

        # OTP correct => mark logged in and go to main
        session["logged_in"] = True
        session["name"] = verified_name
        session["email"] = verified_email
        session.pop("pending_otp", None)
        return redirect(url_for("main"))
    else:
        flash("Incorrect OTP. Please try again.")
        return redirect(url_for("verify"))

@app.route("/change_email", methods=["GET"])
def change_email():
    session.pop("pending_email", None)
    session.pop("pending_name", None)
    session.pop("pending_otp", None)
    return redirect(url_for("index"))

@app.route("/main", methods=["GET"])
def main():
    if not session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template_string(MAIN_HTML, name=session.get("name"), email=session.get("email"))

@app.route("/control", methods=["GET"])
def control():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    direction = request.args.get("direction", "")
    message = ""

    if direction == "up":
        message = "throtle up"
    elif direction == "down":
        message = "throtle down"
    elif direction == "right":
        message = "servo right"
    elif direction == "left":
        message = "servo left"
    else:
        message = "unknown command"

    print(message)
    return jsonify({"message": message})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)