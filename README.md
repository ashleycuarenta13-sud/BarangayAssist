from flask import Flask, request, render_template_string
import requests
import time
from urllib.parse import urlparse

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TARGET = "http://127.0.0.1:5000/login"
DEFAULT_LOGIN_TYPE = "email"
DEFAULT_LOGIN_VALUE = "admin@barangayassist.local"

CONTROLLED_ATTEMPTS = 5

ALLOWED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1"
}

COMMON_PASSWORDS = [
    "1234",
    "12345",
    "123456",
    "12345678",
    "password",
    "password123",
    "admin",
    "admin123",
    "admin1234",
    "qwerty",
    "welcome",
    "student",
    "student123"
]

NUMERIC_PASSWORD_START = 0
NUMERIC_PASSWORD_END = 5000
NUMERIC_PASSWORD_WIDTH = 6

CANDIDATE_COUNT = (
    len(COMMON_PASSWORDS)
    + (NUMERIC_PASSWORD_END - NUMERIC_PASSWORD_START + 1)
)


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>CYBER LAB // Authentication Tester</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            min-height: 100vh;
            background:
                linear-gradient(rgba(5, 20, 15, 0.96), rgba(3, 12, 9, 0.98)),
                repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(40, 255, 150, 0.025) 3px
                );
            color: #d9ffe9;
            font-family: Consolas, "Courier New", monospace;
        }

        .container {
            width: min(1100px, 94%);
            margin: 30px auto;
        }

        .header {
            border: 1px solid #2f8f67;
            padding: 22px;
            background: rgba(8, 35, 25, 0.85);
            box-shadow: 0 0 25px rgba(30, 180, 110, 0.12);
        }

        .logo {
            color: #5cffaa;
            font-size: 24px;
            font-weight: bold;
        }

        .subtitle {
            margin-top: 7px;
            color: #7eaf98;
            font-size: 13px;
        }

        .status {
            margin-top: 15px;
            color: #55ff9a;
            font-size: 12px;
        }

        .status span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #55ff9a;
            border-radius: 50%;
            margin-right: 7px;
            box-shadow: 0 0 8px #55ff9a;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-top: 18px;
        }

        .panel {
            border: 1px solid #245d47;
            background: rgba(7, 28, 20, 0.9);
            padding: 20px;
        }

        .panel h2 {
            color: #d9a441;
            font-size: 15px;
            margin-bottom: 18px;
            letter-spacing: 1px;
        }

        label {
            display: block;
            margin-bottom: 7px;
            color: #8fc9aa;
            font-size: 12px;
        }

        input,
        select {
            width: 100%;
            padding: 11px;
            margin-bottom: 15px;
            border: 1px solid #28694e;
            outline: none;
            background: #061811;
            color: #d9ffe9;
            font-family: inherit;
        }

        input:focus,
        select:focus {
            border-color: #55d991;
            box-shadow: 0 0 8px rgba(85, 217, 145, 0.15);
        }

        .warning {
            padding: 12px;
            margin-bottom: 16px;
            border-left: 3px solid #d9a441;
            background: rgba(217, 164, 65, 0.08);
            color: #d8c38e;
            font-size: 11px;
            line-height: 1.6;
        }

        button {
            width: 100%;
            padding: 13px;
            border: 1px solid #55d991;
            background: #0b3827;
            color: #7cffb0;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #105236;
            box-shadow: 0 0 15px rgba(85, 217, 145, 0.2);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 18px;
        }

        .stat {
            border: 1px solid #245d47;
            background: rgba(7, 28, 20, 0.9);
            padding: 15px;
            text-align: center;
        }

        .stat-number {
            color: #5cffaa;
            font-size: 22px;
            font-weight: bold;
        }

        .stat-label {
            color: #719b86;
            font-size: 10px;
            margin-top: 5px;
        }

        .terminal {
            margin-top: 18px;
            border: 1px solid #245d47;
            background: #020805;
        }

        .terminal-header {
            padding: 10px 14px;
            border-bottom: 1px solid #183e2f;
            color: #76a58d;
            font-size: 11px;
        }

        #output {
            height: 350px;
            overflow-y: auto;
            padding: 15px;
            color: #8dffb9;
            font-size: 12px;
            line-height: 1.7;
            white-space: pre-wrap;
        }

        .footer {
            margin-top: 18px;
            text-align: center;
            color: #466b58;
            font-size: 10px;
        }

        @media (max-width: 750px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <div class="logo">CYBER LAB // AUTHENTICATION TESTER</div>

        <div class="subtitle">
            IT107 Activity 2 — Authentication & Rate-Limiting Laboratory Analysis
        </div>

        <div class="status">
            <span></span>
            LOCALHOST ONLY // CONTROLLED TEST MODE
        </div>
    </div>

    <div class="grid">

        <div class="panel">

            <h2>// TARGET CONFIGURATION</h2>

            <label>Target URL</label>
            <input
                id="target"
                value="{{ target }}"
                placeholder="http://127.0.0.1:5000/login"
            >

            <label>Identifier Type</label>
            <select id="login_type">
                <option value="email"
                    {% if login_type == "email" %}selected{% endif %}>
                    email
                </option>

                <option value="username"
                    {% if login_type == "username" %}selected{% endif %}>
                    username
                </option>
            </select>

            <label>Login Value</label>
            <input
                id="login_value"
                value="{{ login_value }}"
            >

            <label>TEST PASSWORD</label>
            <input
                id="test_password"
                type="text"
                value="WrongPassword_For_Lab_Test_123!"
            >

        </div>

        <div class="panel">

            <h2>// TEST INFORMATION</h2>

            <div class="warning">
                CONTROLLED TEST MODE<br><br>
                This tester sends exactly 5 intentionally invalid
                login requests. It does not automatically cycle
                through passwords or attempt credential discovery.
            </div>

            <div style="color:#769d88;font-size:11px;line-height:1.8;">
                Candidate list reference:
                <strong style="color:#5cffaa;">
                    {{ candidate_count }}
                </strong>
                entries from the laboratory activity.
                <br><br>

                Actual requests:
                <strong style="color:#5cffaa;">
                    {{ controlled_attempts }}
                </strong>
            </div>

            <br>

            <button id="startBtn" onclick="startTest()">
                START CONTROLLED TEST
            </button>

        </div>

    </div>

    <div class="stats">

        <div class="stat">
            <div class="stat-number" id="attempts">0</div>
            <div class="stat-label">ATTEMPTS</div>
        </div>

        <div class="stat">
            <div class="stat-number" id="failed">0</div>
            <div class="stat-label">FAILED</div>
        </div>

        <div class="stat">
            <div class="stat-number" id="elapsed">0.00s</div>
            <div class="stat-label">ELAPSED</div>
        </div>

        <div class="stat">
            <div class="stat-number" id="lockout">NO</div>
            <div class="stat-label">LOCKOUT</div>
        </div>

    </div>

    <div class="terminal">

        <div class="terminal-header">
            TERMINAL OUTPUT
        </div>

        <div id="output">
Ready.
        </div>

    </div>

    <div class="footer">
        IT107 AUTHENTICATION & RATE-LIMITING LABORATORY
    </div>

</div>


<script>

async function startTest() {

    const button = document.getElementById("startBtn");
    const output = document.getElementById("output");

    const target = document.getElementById("target").value;
    const login_type = document.getElementById("login_type").value;
    const login_value = document.getElementById("login_value").value;
    const test_password = document.getElementById("test_password").value;

    output.textContent = "";

    document.getElementById("attempts").textContent = "0";
    document.getElementById("failed").textContent = "0";
    document.getElementById("elapsed").textContent = "0.00s";
    document.getElementById("lockout").textContent = "NO";

    button.disabled = true;
    button.textContent = "TEST RUNNING...";

    output.textContent +=
        "==================================================\\n";

    output.textContent +=
        "CYBER LAB // CONTROLLED AUTHENTICATION TEST\\n";

    output.textContent +=
        "==================================================\\n\\n";

    output.textContent +=
        "[TARGET] " + target + "\\n";

    output.textContent +=
        "[IDENTIFIER] " + login_type + "\\n";

    output.textContent +=
        "[LOGIN VALUE] " + login_value + "\\n";

    output.textContent +=
        "[MODE] 5 CONTROLLED INVALID REQUESTS\\n\\n";

    try {

        const response = await fetch("/api/test", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                target: target,
                login_type: login_type,
                login_value: login_value,
                test_password: test_password
            })

        });

        const data = await response.json();

        document.getElementById("attempts").textContent =
            data.attempts;

        document.getElementById("failed").textContent =
            data.failed;

        document.getElementById("elapsed").textContent =
            data.elapsed.toFixed(2) + "s";

        document.getElementById("lockout").textContent =
            data.lockout ? "YES" : "NO";

        for (const item of data.results) {

            let line =
                "ATTEMPT " +
                String(item.attempt).padStart(3, "0") +
                " | HTTP " +
                item.status +
                " | " +
                item.result;

            if (item.redirect) {
                line += " | REDIRECT";
            }

            output.textContent += line + "\\n";

            await new Promise(resolve =>
                setTimeout(resolve, 80)
            );
        }

        output.textContent +=
            "\\n--------------------------------------------------\\n";

        output.textContent +=
            "TOTAL ATTEMPTS : " + data.attempts + "\\n";

        output.textContent +=
            "FAILED         : " + data.failed + "\\n";

        output.textContent +=
            "ELAPSED TIME   : " + data.elapsed.toFixed(2) + " seconds\\n";

        output.textContent +=
            "LOCKOUT        : " +
            (data.lockout ? "DETECTED" : "NOT DETECTED") +
            "\\n";

        output.textContent +=
            "--------------------------------------------------\\n";

        if (data.error) {
            output.textContent +=
                "\\nERROR: " + data.error + "\\n";
        }

    } catch (error) {

        output.textContent +=
            "\\nCONNECTION ERROR — tester server problem.\\n";

        output.textContent +=
            error.toString() + "\\n";
    }

    button.disabled = false;
    button.textContent = "START CONTROLLED TEST";
}

</script>

</body>
</html>
"""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_localhost(url):
    """
    Allow testing only against localhost.
    """

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname

        return hostname in ALLOWED_HOSTS

    except Exception:
        return False


def detect_lockout(text):
    """
    Detect common lockout/rate-limit messages.
    """

    text_lower = text.lower()

    keywords = [
        "too many attempts",
        "too many failed",
        "temporarily locked",
        "account locked",
        "account is locked",
        "try again later",
        "rate limit",
        "temporarily blocked",
        "too many requests",
        "locked out"
    ]

    return any(keyword in text_lower for keyword in keywords)


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():

    return render_template_string(
        HTML,
        target=DEFAULT_TARGET,
        login_type=DEFAULT_LOGIN_TYPE,
        login_value=DEFAULT_LOGIN_VALUE,
        candidate_count=CANDIDATE_COUNT,
        controlled_attempts=CONTROLLED_ATTEMPTS
    )


@app.route("/api/test", methods=["POST"])
def api_test():

    data = request.get_json(silent=True) or {}

    target = data.get("target", "").strip()
    login_type = data.get("login_type", "email").strip()
    login_value = data.get("login_value", "").strip()
    test_password = data.get("test_password", "")

    if not target:
        return {
            "error": "Target URL is required.",
            "attempts": 0,
            "failed": 0,
            "elapsed": 0,
            "lockout": False,
            "results": []
        }

    if not validate_localhost(target):
        return {
            "error": "Only localhost targets are allowed.",
            "attempts": 0,
            "failed": 0,
            "elapsed": 0,
            "lockout": False,
            "results": []
        }

    if login_type not in ("email", "username"):
        return {
            "error": "Identifier type must be email or username.",
            "attempts": 0,
            "failed": 0,
            "elapsed": 0,
            "lockout": False,
            "results": []
        }

    if not login_value:
        return {
            "error": "Login value is required.",
            "attempts": 0,
            "failed": 0,
            "elapsed": 0,
            "lockout": False,
            "results": []
        }

    if not test_password:
        return {
            "error": "Test password is required.",
            "attempts": 0,
            "failed": 0,
            "elapsed": 0,
            "lockout": False,
            "results": []
        }

    results = []
    failed = 0
    lockout = False

    start_time = time.perf_counter()

    session = requests.Session()

    for attempt_number in range(1, CONTROLLED_ATTEMPTS + 1):

        payload = {
            login_type: login_value,
            "password": test_password
        }

        try:

            response = session.post(
                target,
                data=payload,
                allow_redirects=False,
                timeout=5
            )

            status = response.status_code

            is_locked = detect_lockout(response.text)

            if is_locked:
                result = "LOCKOUT / RATE LIMIT DETECTED"
                lockout = True

            elif 200 <= status < 300:
                result = "RESPONSE RECEIVED"

            elif 300 <= status < 400:
                result = "LOGIN REJECTED / REDIRECT"

            elif status == 401 or status == 403:
                result = "AUTHORIZATION REJECTED"

            elif status == 429:
                result = "RATE LIMIT DETECTED"
                lockout = True

            else:
                result = "REQUEST COMPLETED"

            if not is_locked:
                failed += 1

            results.append({
                "attempt": attempt_number,
                "status": status,
                "result": result,
                "redirect": bool(
                    response.headers.get("Location")
                )
            })

            # If a lockout is detected, we can stop sending
            # additional requests.
            if lockout:
                break

        except requests.exceptions.ConnectionError:

            elapsed = time.perf_counter() - start_time

            results.append({
                "attempt": attempt_number,
                "status": "N/A",
                "result": "CONNECTION ERROR"
            })

            return {
                "error":
                    "Target server is not reachable. "
                    "Make sure app.py is running on port 5000.",
                "attempts": attempt_number,
                "failed": failed,
                "elapsed": elapsed,
                "lockout": False,
                "results": results
            }

        except requests.exceptions.Timeout:

            results.append({
                "attempt": attempt_number,
                "status": "TIMEOUT",
                "result": "REQUEST TIMEOUT"
            })

            failed += 1

        except requests.exceptions.RequestException as error:

            results.append({
                "attempt": attempt_number,
                "status": "ERROR",
                "result": str(error)
            })

            failed += 1

    elapsed = time.perf_counter() - start_time

    return {
        "attempts": len(results),
        "failed": failed,
        "elapsed": elapsed,
        "lockout": lockout,
        "results": results
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CYBER LAB // AUTHENTICATION TESTER")
    print("=" * 60)

    print("Tester URL : http://127.0.0.1:5001")
    print("Target     : http://127.0.0.1:5000/login")
    print("Mode       : 5 controlled invalid attempts")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False
    )