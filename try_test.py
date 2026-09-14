from flask import Flask, request, jsonify, render_template_string
import requests
import time
from urllib.parse import urlparse

app = Flask(__name__)

# ============================================================
# SAFE LOCAL AUTHENTICATION TESTER
# Converted from the provided PHP laboratory interface.
# This version keeps the UI/CSS/JS style, but uses controlled
# repeated invalid requests instead of password guessing.
# ============================================================

DEFAULT_TARGET = "http://127.0.0.1:5000/login"
DEFAULT_LOGIN_TYPE = "email"
DEFAULT_LOGIN_VALUE = "admin@barangayassist.local"
TEST_PASSWORD = "WrongPassword_For_Lab_Test_123!"

# Candidate configuration preserved from the original PHP lab.
# These values are shown as lab metadata; the Python tester does not
# automatically cycle through them.
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
    "student123",
]
NUMERIC_PASSWORD_START = 0
NUMERIC_PASSWORD_END = 5000
NUMERIC_PASSWORD_WIDTH = 6
CANDIDATE_COUNT = len(COMMON_PASSWORDS) + (NUMERIC_PASSWORD_END - NUMERIC_PASSWORD_START + 1)
CONTROLLED_ATTEMPTS = 5

ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}


def localhost_only(url):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in ALLOWED_HOSTS


def test_login(url, login_type, login_value, password):
    if login_type == "username":
        post_data = {"username": login_value, "password": password}
    elif login_type == "email":
        post_data = {"email": login_value, "password": password}
    else:
        return {
            "success": False,
            "locked": False,
            "http_code": 0,
            "redirect": "",
            "response": "",
            "error": "Invalid login type."
        }

    try:
        started = time.perf_counter()

        response = requests.post(
            url,
            data=post_data,
            allow_redirects=False,
            timeout=(5, 10),
            headers={"User-Agent": "Cyber-Lab-Localhost-Tester/1.0"}
        )

        elapsed = time.perf_counter() - started
        body_lower = response.text.lower()

        locked = any(text in body_lower for text in [
            "account temporarily locked",
            "account is locked",
            "locked for 60 seconds",
            "too many failed attempts",
            "temporarily locked"
        ])

        # A redirect alone is NOT treated as successful authentication.
        return {
            "success": False,
            "locked": locked,
            "http_code": response.status_code,
            "redirect": response.headers.get("Location", ""),
            "response": response.text,
            "elapsed": elapsed,
            "error": ""
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "locked": False,
            "http_code": 0,
            "redirect": "",
            "response": "",
            "elapsed": 0,
            "error": str(exc)
        }


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER LAB // Authentication Tester</title>

<style>
* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    min-height: 100%;
    font-family: "Courier New", Consolas, monospace;
    background: #020604;
    color: #00ff88;
}

body {
    overflow-x: hidden;
    background:
        radial-gradient(circle at 50% 0%, rgba(0,255,120,0.08), transparent 40%),
        radial-gradient(circle at 0% 100%, rgba(0,180,255,0.06), transparent 35%),
        #020604;
}

body::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.08;
    background-image:
        linear-gradient(rgba(0,255,120,0.15) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,120,0.15) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: gridMove 12s linear infinite;
}

@keyframes gridMove {
    from { background-position: 0 0, 0 0; }
    to { background-position: 0 40px, 40px 0; }
}

.wrapper {
    position: relative;
    z-index: 1;
    width: min(1400px, 94%);
    margin: 30px auto 50px;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 22px;
    border: 1px solid rgba(0,255,120,0.35);
    background: rgba(0,10,6,0.88);
    box-shadow: 0 0 30px rgba(0,255,120,0.08);
    border-radius: 8px 8px 0 0;
}

.logo {
    display: flex;
    align-items: center;
    gap: 14px;
}

.logo-icon {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #00ff88;
    color: #00ff88;
    font-size: 20px;
    box-shadow: 0 0 15px rgba(0,255,120,0.4);
}

.logo-title {
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 2px;
    color: #00ff88;
}

.logo-sub {
    color: #4f9f78;
    font-size: 11px;
    margin-top: 3px;
    letter-spacing: 1px;
}

.local-status {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 8px 13px;
    border: 1px solid rgba(0,255,120,0.35);
    color: #00ff88;
    font-size: 11px;
    letter-spacing: 1px;
    background: rgba(0,255,120,0.04);
}

.status-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #00ff88;
    box-shadow: 0 0 12px #00ff88;
    animation: pulse 1.4s infinite;
}

@keyframes pulse {
    0%,100% { opacity: 1; }
    50% { opacity: .35; }
}

.content {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 18px;
    margin-top: 18px;
}

@media(max-width:900px) {
    .content {
        grid-template-columns: 1fr;
    }
}

.panel {
    border: 1px solid rgba(0,255,120,0.25);
    background: rgba(1,12,8,0.90);
    box-shadow: 0 0 25px rgba(0,255,120,0.04);
    border-radius: 6px;
    overflow: hidden;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    padding: 12px 15px;
    border-bottom: 1px solid rgba(0,255,120,0.18);
    background: rgba(0,255,120,0.035);
    font-size: 11px;
    letter-spacing: 1.5px;
}

.panel-header span:first-child { color: #00ff88; }
.panel-header span:last-child { color: #276b4c; }

.config {
    padding: 18px;
}

.field {
    margin-bottom: 17px;
}

.field label {
    display: block;
    margin-bottom: 7px;
    color: #52b88a;
    font-size: 10px;
    letter-spacing: 1px;
}

input, select {
    width: 100%;
    padding: 12px 13px;
    border: 1px solid rgba(0,255,120,0.25);
    outline: none;
    background: #020805;
    color: #00ff88;
    font-family: inherit;
    font-size: 12px;
    border-radius: 3px;
    transition: .2s;
}

input:focus, select:focus {
    border-color: #00ff88;
    box-shadow: 0 0 12px rgba(0,255,120,0.18);
}

select option {
    background: #020805;
    color: #00ff88;
}

.buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 20px;
}

button {
    padding: 13px;
    border: 1px solid #00ff88;
    background: rgba(0,255,120,0.07);
    color: #00ff88;
    font-family: inherit;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
    cursor: pointer;
    border-radius: 3px;
    transition: .2s;
}

button:hover {
    background: rgba(0,255,120,0.18);
    box-shadow: 0 0 18px rgba(0,255,120,0.25);
}

button:disabled {
    opacity: .45;
    cursor: not-allowed;
}

#stopBtn {
    border-color: #ff3355;
    color: #ff3355;
    background: rgba(255,30,70,0.05);
}

#stopBtn:hover {
    background: rgba(255,30,70,0.12);
    box-shadow: 0 0 18px rgba(255,30,70,0.2);
}

.stats {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 10px;
    padding: 15px;
}

.stat {
    border: 1px solid rgba(0,255,120,0.16);
    background: rgba(0,0,0,0.25);
    padding: 13px;
    text-align: center;
}

.stat-label {
    color: #347858;
    font-size: 9px;
    letter-spacing: 1px;
    margin-bottom: 7px;
}

.stat-value {
    color: #00ff88;
    font-size: 18px;
    font-weight: bold;
}

.terminal-panel {
    min-height: 650px;
}

.terminal-bar {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 9px 12px;
    border-bottom: 1px solid rgba(0,255,120,0.15);
    background: #050807;
}

.terminal-circle {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #244c37;
}

.terminal-title {
    margin-left: 8px;
    color: #3d805f;
    font-size: 10px;
}

.terminal {
    margin: 0;
    height: 560px;
    overflow-y: auto;
    padding: 18px;
    background: #010302;
    color: #00ff88;
    font-size: 12px;
    line-height: 1.7;
    white-space: pre-wrap;
    text-shadow: 0 0 5px rgba(0,255,120,0.45);
    scrollbar-width: thin;
    scrollbar-color: #0c603b #010302;
}

.terminal .failed-line {
    color: #ff4d6d !important;
    font-weight: 700;
    text-shadow: 0 0 6px rgba(255,77,109,0.45);
}

.terminal .success-line {
    color: #00ffff !important;
    font-weight: 800;
    text-shadow: 0 0 8px rgba(0,255,255,0.65);
}

.terminal .attempt-line {
    font-weight: 700;
}

.warning {
    margin: 0 0 18px;
    padding: 11px;
    border: 1px solid rgba(255,190,0,0.3);
    background: rgba(255,180,0,0.04);
    color: #c9a84b;
    font-size: 10px;
    line-height: 1.6;
}

.footer {
    margin-top: 18px;
    padding: 14px;
    text-align: center;
    border: 1px solid rgba(0,255,120,0.15);
    color: #286044;
    font-size: 10px;
    letter-spacing: 1px;
    background: rgba(0,10,6,0.7);
}

.falling-code {
    position: fixed;
    top: 0;
    bottom: 0;
    width: 170px;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
    opacity: 0.42;
    font-family: "Courier New", Consolas, monospace;
    color: #00ff88;
    text-shadow: 0 0 7px rgba(0,255,120,0.55);
}

.falling-code.left { left: 0; }
.falling-code.right { right: 0; }

.falling-column {
    position: absolute;
    top: -220px;
    white-space: pre;
    font-size: 12px;
    line-height: 1.55;
    animation: codeFall linear infinite;
}

@keyframes codeFall {
    from { transform: translateY(-260px); }
    to { transform: translateY(calc(100vh + 300px)); }
}

@media(max-width:1100px) {
    .falling-code {
        width: 95px;
        opacity: 0.25;
    }
}

@media(max-width:900px) {
    .falling-code { display: none; }
}

@media(max-width:700px) {
    .stats {
        grid-template-columns: repeat(2,1fr);
    }
}
</style>
</head>

<body>
<div class="falling-code left" id="fallingLeft"></div>
<div class="falling-code right" id="fallingRight"></div>

<div class="wrapper">

    <div class="header">
        <div class="logo">
            <div class="logo-icon">&gt;_</div>
            <div>
                <div class="logo-title">CYBER LAB</div>
                <div class="logo-sub">AUTHENTICATION SECURITY TESTER</div>
            </div>
        </div>

        <div class="local-status">
            <span class="status-dot"></span>
            LOCALHOST ONLY
        </div>
    </div>

    <div class="content">

        <div>

            <div class="panel">
                <div class="panel-header">
                    <span>TARGET CONFIGURATION</span>
                    <span>[CONFIG]</span>
                </div>

                <div class="config">

                    <div class="field">
                        <label>TARGET LOGIN URL</label>
                        <input type="text" id="target"
                               value="{{ target }}">
                    </div>

                    <div class="field">
                        <label>LOGIN IDENTIFIER</label>
                        <select id="loginType">
                            <option value="username" {% if login_type == "username" %}selected{% endif %}>
                                USERNAME
                            </option>
                            <option value="email" {% if login_type == "email" %}selected{% endif %}>
                                EMAIL
                            </option>
                        </select>
                    </div>

                    <div class="field">
                        <label>LOGIN VALUE</label>
                        <input type="text" id="loginValue"
                               value="{{ login_value }}">
                    </div>

                    <div class="field">
                        <label>TEST PASSWORD</label>
                        <input type="password" id="testPassword"
                               value="{{ test_password }}"
                               autocomplete="off">
                    </div>

                    <div class="warning">
                        ⚠ AUTHORIZED LAB USE ONLY
                        <br>
                        This Python tester is restricted to localhost.
                        <br><br>
                        The test sends a fixed number of controlled invalid
                        login requests to measure authentication protection.
                    </div>

                    <div class="buttons">
                        <button id="startBtn">▶ START TEST</button>
                        <button id="stopBtn">■ STOP</button>
                    </div>

                </div>
            </div>

            <div class="panel" style="margin-top:18px;">
                <div class="panel-header">
                    <span>SYSTEM STATUS</span>
                    <span>[ONLINE]</span>
                </div>

                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">TEST REQUESTS</div>
                        <div class="stat-value" id="candidateStat">5</div>
                    </div>

                    <div class="stat">
                        <div class="stat-label">ATTEMPTS</div>
                        <div class="stat-value" id="attemptStat">0</div>
                    </div>

                    <div class="stat">
                        <div class="stat-label">FAILED</div>
                        <div class="stat-value" id="failedStat">0</div>
                    </div>

                    <div class="stat">
                        <div class="stat-label">STATUS</div>
                        <div class="stat-value" id="statusStat">IDLE</div>
                    </div>
                </div>
            </div>

        </div>

        <div class="panel terminal-panel">
            <div class="terminal-bar">
                <span class="terminal-circle"></span>
                <span class="terminal-circle"></span>
                <span class="terminal-circle"></span>
                <span class="terminal-title">
                    CYBER-LAB TERMINAL // localhost
                </span>
            </div>

            <div class="terminal" id="output">╔════════════════════════════════════════════╗
║        CYBER AUTHENTICATION LAB            ║
║        LOCALHOST TESTING TERMINAL          ║
╚════════════════════════════════════════════╝

root@localhost:~$ system-check
[+] Environment : LOCALHOST
[+] Security    : LOCAL TARGET ONLY
[+] Status      : READY

root@localhost:~$ waiting for test...</div>
        </div>

    </div>

    <div class="footer">
        CYBERSECURITY LABORATORY
        //
        AUTHENTICATION SECURITY ANALYSIS
        //
        LOCAL ENVIRONMENT
    </div>

</div>

<script>
let running = false;
let controller = null;

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const output = document.getElementById("output");
const status = document.getElementById("statusStat");
const attempts = document.getElementById("attemptStat");
const failedStat = document.getElementById("failedStat");

function addLine(text, className = "") {
    const line = document.createElement("div");
    line.textContent = text;
    if (className) line.className = className;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

startBtn.addEventListener("click", async function () {
    if (running) return;

    const target = document.getElementById("target").value.trim();
    const loginType = document.getElementById("loginType").value;
    const loginValue = document.getElementById("loginValue").value.trim();
    const testPassword = document.getElementById("testPassword").value;

    if (!target || !loginValue) {
        addLine("[ERROR] Target and login value are required.", "failed-line");
        return;
    }

    running = true;
    controller = new AbortController();

    startBtn.disabled = true;
    attempts.textContent = "0";
    failedStat.textContent = "0";
    status.textContent = "RUNNING";
    status.style.color = "#00bfff";

    output.textContent = "root@localhost:~$ ./auth-test\n\n";
    addLine("[*] Initializing controlled authentication test...");
    addLine("[*] Target      : " + target);
    addLine("[*] Identifier  : " + loginType);
    addLine("[*] Login Value : " + loginValue);
    addLine("[*] Test Password: " + testPassword);
    addLine("[*] Requests    : 5 fixed invalid attempts");
    addLine("[*] Environment : LOCALHOST");
    addLine("---------------------------------------------");

    const params = new URLSearchParams({
        target: target,
        login_type: loginType,
        login_value: loginValue,
        test_password: testPassword
    });

    try {
        const response = await fetch("/api/test?" + params.toString(), {
            method: "GET",
            cache: "no-store",
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        const data = await response.json();

        data.lines.forEach(item => {
            addLine(item.text, item.class_name || "");
        });

        attempts.textContent = data.attempts;
        failedStat.textContent = data.failed;

        if (data.locked) {
            status.textContent = "LOCKED";
            status.style.color = "#ffcc00";
        } else if (data.error) {
            status.textContent = "ERROR";
            status.style.color = "#ff3355";
        } else {
            status.textContent = "DONE";
            status.style.color = "#00ff88";
        }

    } catch (error) {
        if (error.name === "AbortError") {
            addLine("[!] PROCESS STOPPED BY USER.", "failed-line");
            status.textContent = "STOPPED";
            status.style.color = "#ff3355";
        } else {
            addLine("[ERROR] " + error.message, "failed-line");
            status.textContent = "ERROR";
            status.style.color = "#ff3355";
        }
    }

    running = false;
    controller = null;
    startBtn.disabled = false;
});

stopBtn.addEventListener("click", function () {
    if (controller && running) {
        controller.abort();
    }
    running = false;
});

document.getElementById("loginType").addEventListener("change", function () {
    const loginValue = document.getElementById("loginValue");

    if (this.value === "email") {
        loginValue.placeholder = "example@gmail.com";
    } else {
        loginValue.placeholder = "Enter username";
    }
});

(function () {
    const characters =
        "01ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz<>[]{}#$%&@";

    function randomCode(length) {
        let result = "";

        for (let i = 0; i < length; i++) {
            result += characters.charAt(
                Math.floor(Math.random() * characters.length)
            );

            if (i % 3 === 2) {
                result += "\n";
            }
        }

        return result;
    }

    function createColumns(containerId, count) {
        const container = document.getElementById(containerId);
        if (!container) return;

        for (let i = 0; i < count; i++) {
            const column = document.createElement("div");
            column.className = "falling-column";
            column.textContent =
                randomCode(95 + Math.floor(Math.random() * 55));

            column.style.left = (5 + Math.random() * 88) + "%";
            column.style.animationDuration =
                (7 + Math.random() * 10) + "s";
            column.style.animationDelay =
                (-Math.random() * 12) + "s";
            column.style.opacity =
                (0.25 + Math.random() * 0.65).toFixed(2);
            column.style.fontSize =
                (9 + Math.random() * 5) + "px";

            container.appendChild(column);
        }
    }

    createColumns("fallingLeft", 7);
    createColumns("fallingRight", 7);
})();
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML,
        target=DEFAULT_TARGET,
        login_type=DEFAULT_LOGIN_TYPE,
        login_value=DEFAULT_LOGIN_VALUE,
        test_password=TEST_PASSWORD
    )


@app.route("/api/test")
def api_test():
    target = request.args.get("target", DEFAULT_TARGET).strip()
    login_type = request.args.get("login_type", DEFAULT_LOGIN_TYPE).strip()
    login_value = request.args.get("login_value", DEFAULT_LOGIN_VALUE).strip()
    test_password = request.args.get("test_password", TEST_PASSWORD)

    if not test_password:
        return jsonify({"error": "Test password cannot be empty."}), 400

    if not localhost_only(target):
        return jsonify({
            "error": "Only localhost targets are allowed.",
            "attempts": 0,
            "failed": 0,
            "locked": False,
            "lines": [
                {
                    "text": "[ERROR] ACCESS DENIED — localhost targets only.",
                    "class_name": "failed-line"
                }
            ]
        }), 403

    if login_type not in {"username", "email"}:
        return jsonify({
            "error": "Invalid login type.",
            "attempts": 0,
            "failed": 0,
            "locked": False,
            "lines": [
                {
                    "text": "[ERROR] Invalid login type.",
                    "class_name": "failed-line"
                }
            ]
        }), 400

    lines = []
    failed = 0
    locked = False
    start_time = time.perf_counter()

    for attempt in range(1, CONTROLLED_ATTEMPTS + 1):
        result = test_login(
            target,
            login_type,
            login_value,
            test_password
        )

        if result["error"]:
            lines.append({
                "text": f"[{attempt:04d}] ERROR | {result['error']}",
                "class_name": "failed-line"
            })
            elapsed = time.perf_counter() - start_time
            lines.append({"text": ""})
            lines.append({
                "text": f"[+] Login Identifier : {login_value}"
            })
            lines.append({
                "text": f"[+] Test Password    : {test_password}"
            })
            lines.append({
                "text": f"[+] Attempts         : {attempt}"
            })
            lines.append({
                "text": f"[+] Elapsed Time     : {elapsed:.2f} seconds"
            })
            lines.append({
                "text": "[+] Result           : CONNECTION ERROR — target server is not reachable.",
                "class_name": "failed-line"
            })
            return jsonify({
                "attempts": attempt,
                "failed": failed,
                "locked": False,
                "error": result["error"],
                "lines": lines
            })

        code = result["http_code"]

        if result["locked"]:
            locked = True
            lines.append({
                "text": f"[{attempt:04d}] [HTTP {code}] >>> ACCOUNT LOCKED <<<",
                "class_name": "success-line"
            })
            break

        failed += 1

        redirect = result["redirect"]
        redirect_text = f" | Redirect: {redirect}" if redirect else ""

        lines.append({
            "text": (
                f"[{attempt:04d}] [HTTP {code}] FAILED"
                f"{redirect_text}"
                f" | {result['elapsed']:.3f}s"
            ),
            "class_name": "failed-line"
        })

        time.sleep(0.05)

    elapsed = time.perf_counter() - start_time

    lines.append({"text": ""})
    lines.append({
        "text": "╔════════════════════════════════════════════╗"
    })

    if locked:
        lines.append({
            "text": "║          PROTECTION DETECTED               ║",
            "class_name": "success-line"
        })
    else:
        lines.append({
            "text": "║       CONTROLLED TEST COMPLETE             ║"
        })

    lines.append({
        "text": "╚════════════════════════════════════════════╝"
    })
    lines.append({
        "text": f"[+] Login Identifier : {login_value}"
    })
    lines.append({
        "text": f"[+] Test Password    : {test_password}"
    })
    lines.append({
        "text": f"[+] Attempts         : {failed}"
    })
    lines.append({
        "text": f"[+] Elapsed Time     : {elapsed:.2f} seconds"
    })

    if locked:
        lines.append({
            "text": "[+] Result           : Temporary lockout detected.",
            "class_name": "success-line"
        })
    else:
        lines.append({
            "text": "[+] Result           : No lockout detected during 5 controlled attempts."
        })

    return jsonify({
        "attempts": failed,
        "failed": failed,
        "locked": locked,
        "error": "",
        "lines": lines
    })


if __name__ == "__main__":
    print("=" * 52)
    print("CYBER LAB // AUTHENTICATION TESTER")
    print("Python conversion of the provided PHP laboratory UI/structure")
    print("LOCALHOST ONLY")
    print("=" * 52)
    print("Open: http://127.0.0.1:5001")
    print("Target: http://127.0.0.1:5000/login")
    print("=" * 52)

    app.run(host="127.0.0.1", port=5001, debug=False)