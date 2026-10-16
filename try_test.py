from flask import Flask, request, Response, render_template_string
import requests
import time
from urllib.parse import urlparse

app = Flask(__name__)

# ============================================================
# EXACT PYTHON TRANSLATION OF lab_test.php
# Same variables, same combined wordlist, same single-request
# streaming loop, same message text. Only the language changed
# (PHP -> Python/Flask); the logic and flow are unchanged.
# ============================================================

target = "http://127.0.0.1:5000/login"
login_type = "email"
login_value = "admin@barangayassist.local"
password_field = "password"

common_passwords = [
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

numeric_passwords = []
for i in range(0, 5001):
    numeric_passwords.append(str(i).zfill(6))

password_list = common_passwords + numeric_passwords

# array_unique(array_values(...)) equivalent — de-dupe, keep order
seen = set()
deduped = []
for p in password_list:
    if p not in seen:
        seen.add(p)
        deduped.append(p)
password_list = deduped

parsed_url = urlparse(target)
host = parsed_url.hostname or ""

allowed_hosts = ["localhost", "127.0.0.1", "::1"]

if host not in allowed_hosts:
    # Matches the PHP script's hard stop for non-localhost targets.
    # (In Python this is enforced per-request inside the /login-test
    # route below, since Flask doesn't halt at import time.)
    pass


def test_login(url, login_type, login_value, password_field, password):

    post_data = {}

    if login_type == "username":
        post_data["username"] = login_value
    elif login_type == "email":
        post_data["email"] = login_value
    else:
        return {
            "success": False,
            "http_code": 0,
            "error": "Invalid login type."
        }

    post_data[password_field] = password

    try:
        response = requests.post(
            url,
            data=post_data,
            allow_redirects=False,
            timeout=(5, 10),
            headers={"User-Agent": "Cyber-Lab-Localhost-Tester/1.0"}
        )
    except requests.RequestException as exc:
        return {
            "success": False,
            "http_code": 0,
            "error": str(exc)
        }

    http_code = response.status_code
    redirect = response.headers.get("Location", "")

    success = False
    if 300 <= http_code < 400:
        success = True

    body_lower = (response.text or "").lower()
    is_locked = (
        "account temporarily locked" in body_lower or
        "account is locked" in body_lower or
        "locked for 60 seconds" in body_lower or
        "too many failed attempts" in body_lower
    )

    return {
        "success": success,
        "locked": is_locked,
        "http_code": http_code,
        "redirect": redirect,
        "response": response.text,
        "error": ""
    }


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER LAB // Authentication Tester</title>
<style>
* { box-sizing: border-box; }
html, body { margin:0; padding:0; width:100%; min-height:100%; font-family:"Courier New",Consolas,monospace; background:#020604; color:#00ff88; }
body { overflow-x:hidden; background:
    radial-gradient(circle at 50% 0%, rgba(0,255,120,0.08), transparent 40%),
    radial-gradient(circle at 0% 100%, rgba(0,180,255,0.06), transparent 35%), #020604; }
body::before { content:""; position:fixed; inset:0; pointer-events:none; opacity:.08;
    background-image: linear-gradient(rgba(0,255,120,0.15) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,120,0.15) 1px, transparent 1px);
    background-size:40px 40px; animation:gridMove 12s linear infinite; }
@keyframes gridMove { from{background-position:0 0,0 0;} to{background-position:0 40px,40px 0;} }
.wrapper { position:relative; z-index:1; width:min(1400px,94%); margin:30px auto 50px; }
.header { display:flex; justify-content:space-between; align-items:center; padding:18px 22px;
    border:1px solid rgba(0,255,120,0.35); background:rgba(0,10,6,0.88);
    box-shadow:0 0 30px rgba(0,255,120,0.08); border-radius:8px 8px 0 0; }
.logo { display:flex; align-items:center; gap:14px; }
.logo-icon { width:42px; height:42px; display:flex; align-items:center; justify-content:center;
    border:1px solid #00ff88; color:#00ff88; font-size:20px; box-shadow:0 0 15px rgba(0,255,120,0.4); }
.logo-title { font-size:18px; font-weight:bold; letter-spacing:2px; color:#00ff88; }
.logo-sub { color:#4f9f78; font-size:11px; margin-top:3px; letter-spacing:1px; }
.local-status { display:flex; align-items:center; gap:9px; padding:8px 13px;
    border:1px solid rgba(0,255,120,0.35); color:#00ff88; font-size:11px; letter-spacing:1px;
    background:rgba(0,255,120,0.04); }
.status-dot { width:9px; height:9px; border-radius:50%; background:#00ff88;
    box-shadow:0 0 12px #00ff88; animation:pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.35;} }
.content { display:grid; grid-template-columns:380px 1fr; gap:18px; margin-top:18px; }
@media(max-width:900px){ .content{ grid-template-columns:1fr; } }
.panel { border:1px solid rgba(0,255,120,0.25); background:rgba(1,12,8,0.90);
    box-shadow:0 0 25px rgba(0,255,120,0.04); border-radius:6px; overflow:hidden; }
.panel-header { display:flex; justify-content:space-between; padding:12px 15px;
    border-bottom:1px solid rgba(0,255,120,0.18); background:rgba(0,255,120,0.035);
    font-size:11px; letter-spacing:1.5px; }
.panel-header span:first-child{ color:#00ff88; }
.panel-header span:last-child{ color:#276b4c; }
.config { padding:18px; }
.field { margin-bottom:17px; }
.field label { display:block; margin-bottom:7px; color:#52b88a; font-size:10px; letter-spacing:1px; }
input, select { width:100%; padding:12px 13px; border:1px solid rgba(0,255,120,0.25); outline:none;
    background:#020805; color:#00ff88; font-family:inherit; font-size:12px; border-radius:3px; transition:.2s; }
input:focus, select:focus { border-color:#00ff88; box-shadow:0 0 12px rgba(0,255,120,0.18); }
select option { background:#020805; color:#00ff88; }
.buttons { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px; }
button { padding:13px; border:1px solid #00ff88; background:rgba(0,255,120,0.07); color:#00ff88;
    font-family:inherit; font-weight:bold; font-size:11px; letter-spacing:1px; cursor:pointer;
    border-radius:3px; transition:.2s; }
button:hover { background:rgba(0,255,120,0.18); box-shadow:0 0 18px rgba(0,255,120,0.25); }
#stopBtn { border-color:#ff3355; color:#ff3355; background:rgba(255,30,70,0.05); }
#stopBtn:hover { background:rgba(255,30,70,0.12); box-shadow:0 0 18px rgba(255,30,70,0.2); }
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; padding:15px; }
.stat { border:1px solid rgba(0,255,120,0.16); background:rgba(0,0,0,0.25); padding:13px; text-align:center; }
.stat-label { color:#347858; font-size:9px; letter-spacing:1px; margin-bottom:7px; }
.stat-value { color:#00ff88; font-size:18px; font-weight:bold; }
.terminal-panel { min-height:650px; }
.terminal-bar { display:flex; align-items:center; gap:7px; padding:9px 12px;
    border-bottom:1px solid rgba(0,255,120,0.15); background:#050807; }
.terminal-circle { width:9px; height:9px; border-radius:50%; background:#244c37; }
.terminal-title { margin-left:8px; color:#3d805f; font-size:10px; }
.terminal { margin:0; height:560px; overflow-y:auto; padding:18px; background:#010302; color:#00ff88;
    font-size:12px; line-height:1.7; white-space:pre-wrap; text-shadow:0 0 5px rgba(0,255,120,0.45);
    scrollbar-width:thin; scrollbar-color:#0c603b #010302; }
.terminal::before { content:"root@localhost:~$ "; color:#00bfff; }
.terminal .failed-line { color:#ff4d6d !important; font-weight:700; text-shadow:0 0 6px rgba(255,77,109,0.45); }
.terminal .success-line { color:#00ffff !important; font-weight:800; text-shadow:0 0 8px rgba(0,255,255,0.65); }
.terminal .attempt-line { font-weight:700; }
.warning { margin:0 0 18px; padding:11px; border:1px solid rgba(255,190,0,0.3);
    background:rgba(255,180,0,0.04); color:#c9a84b; font-size:10px; line-height:1.6; }
.footer { margin-top:18px; padding:14px; text-align:center; border:1px solid rgba(0,255,120,0.15);
    color:#286044; font-size:10px; letter-spacing:1px; background:rgba(0,10,6,0.7); }
</style>
</head>
<body>
<div class="wrapper">

    <div class="header">
        <div class="logo">
            <div class="logo-icon">&gt;_</div>
            <div>
                <div class="logo-title">CYBER LAB</div>
                <div class="logo-sub">AUTHENTICATION SECURITY TESTER</div>
            </div>
        </div>
        <div class="local-status"><span class="status-dot"></span>LOCALHOST ONLY</div>
    </div>

    <div class="content">
        <div>
            <div class="panel">
                <div class="panel-header"><span>TARGET CONFIGURATION</span><span>[CONFIG]</span></div>
                <div class="config">
                    <div class="field">
                        <label>TARGET LOGIN URL</label>
                        <input type="text" id="target" value="{{ target }}">
                    </div>
                    <div class="field">
                        <label>LOGIN IDENTIFIER</label>
                        <select id="loginType">
                            <option value="username" {% if login_type == "username" %}selected{% endif %}>USERNAME</option>
                            <option value="email" {% if login_type == "email" %}selected{% endif %}>EMAIL</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>LOGIN VALUE</label>
                        <input type="text" id="loginValue" value="{{ login_value }}">
                    </div>
                    <div class="warning">
                        ⚠ AUTHORIZED LAB USE ONLY
                        <br>
                        This tester is restricted to localhost environments.
                    </div>
                    <div class="buttons">
                        <button id="startBtn">▶ START TEST</button>
                        <button id="stopBtn">■ STOP</button>
                    </div>
                </div>
            </div>

            <div class="panel" style="margin-top:18px;">
                <div class="panel-header"><span>SYSTEM STATUS</span><span>[ONLINE]</span></div>
                <div class="stats">
                    <div class="stat"><div class="stat-label">CANDIDATES</div><div class="stat-value">{{ candidate_count }}</div></div>
                    <div class="stat"><div class="stat-label">ATTEMPTS</div><div class="stat-value" id="attemptStat">0</div></div>
                    <div class="stat"><div class="stat-label">FAILED</div><div class="stat-value" id="failedStat">0</div></div>
                    <div class="stat"><div class="stat-label">STATUS</div><div class="stat-value" id="statusStat">IDLE</div></div>
                </div>
            </div>
        </div>

        <div class="panel terminal-panel">
            <div class="terminal-bar">
                <span class="terminal-circle"></span><span class="terminal-circle"></span><span class="terminal-circle"></span>
                <span class="terminal-title">CYBER-LAB TERMINAL // localhost</span>
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

    <div class="footer">CYBERSECURITY LABORATORY // AUTHENTICATION SECURITY ANALYSIS // LOCAL ENVIRONMENT</div>
</div>

<script>
let running = false;
let controller = null;

document.getElementById("startBtn").addEventListener("click", async function () {

    if (running) {
        return;
    }

    running = true;

    const output = document.getElementById("output");
    const status = document.getElementById("statusStat");
    const attemptsEl = document.getElementById("attemptStat");
    const failedEl = document.getElementById("failedStat");

    output.textContent = "root@localhost:~$ ./auth-test\n\n";
    attemptsEl.textContent = "0";
    failedEl.textContent = "0";
    status.textContent = "RUNNING";
    status.style.color = "#00bfff";

    const target = document.getElementById("target").value;
    const loginType = document.getElementById("loginType").value;
    const loginValue = document.getElementById("loginValue").value;

    output.textContent += "[*] Initializing test...\n";
    output.textContent += "[*] Target      : " + target + "\n";
    output.textContent += "[*] Identifier  : " + loginType + "\n";
    output.textContent += "[*] Login Value : " + loginValue + "\n";
    output.textContent += "[*] Environment : LOCALHOST\n";
    output.textContent += "---------------------------------------------\n";

    output.scrollTop = output.scrollHeight;

    let attemptCount = 0;
    let failedCount = 0;

    try {
        controller = new AbortController();

        const response = await fetch(
            "/login-test?start=1&_=" + Date.now(),
            { method: "GET", cache: "no-store", signal: controller.signal }
        );

        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        if (!response.body) {
            throw new Error("Streaming response is not available.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const result = await reader.read();
            if (result.done) break;

            const chunk = decoder.decode(result.value, { stream: true });
            if (!chunk) continue;

            const lines = chunk.split("\n");

            lines.forEach(function (lineText, index) {
                if (index === lines.length - 1 && lineText === "") return;

                const line = document.createElement("div");
                line.textContent = lineText;

                if (lineText.indexOf(">>> SUCCESS <<<") !== -1) {
                    line.className = "success-line";
                } else if (lineText.indexOf(">>> ACCOUNT LOCKED <<<") !== -1) {
                    line.className = "success-line";
                } else if (lineText.indexOf("FAILED") !== -1) {
                    line.className = "failed-line";
                    failedCount++;
                } else if (lineText.match(/^\[\d+\]/)) {
                    line.className = "attempt-line";
                }

                output.appendChild(line);
            });

            const attemptMatches = chunk.match(/\[(\d+)\]/g);
            if (attemptMatches && attemptMatches.length) {
                const last = attemptMatches[attemptMatches.length - 1];
                const number = last.replace(/\D/g, "");
                attemptCount = parseInt(number, 10);
                attemptsEl.textContent = attemptCount;
            }

            failedEl.textContent = failedCount;

            if (chunk.indexOf("SUCCESS") !== -1) {
                status.textContent = "SUCCESS";
                status.style.color = "#00ff88";
            } else if (chunk.indexOf("ACCOUNT LOCKED") !== -1) {
                status.textContent = "LOCKED";
                status.style.color = "#ffcc00";
            }

            output.scrollTop = output.scrollHeight;
        }

    } catch (error) {
        if (error.name === "AbortError") {
            output.textContent += "\n\n[!] PROCESS STOPPED BY USER.\n";
            status.textContent = "STOPPED";
            status.style.color = "#ff3355";
        } else {
            output.textContent += "\n\n[ERROR] " + error.message + "\n";
            status.textContent = "ERROR";
            status.style.color = "#ff3355";
        }
        output.scrollTop = output.scrollHeight;
    }

    running = false;
    controller = null;

    if (status.textContent === "RUNNING") {
        status.textContent = "DONE";
        status.style.color = "#00ff88";
    }
});

document.getElementById("stopBtn").addEventListener("click", function () {
    if (controller && running) {
        controller.abort();
    }
    running = false;
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML,
        target=target,
        login_type=login_type,
        login_value=login_value,
        candidate_count=len(password_list)
    )


@app.route("/login-test")
def login_test():
    """
    Exact Python equivalent of the `if (isset($_GET["start"]))` block
    in lab_test.php: a single request that streams plain-text progress
    line by line while looping through the FULL combined wordlist,
    stopping immediately on ACCOUNT LOCKED or SUCCESS, same as the PHP.
    """

    if "start" not in request.args:
        return "", 404

    # Same allowed_hosts check as the PHP script (403 ACCESS DENIED).
    parsed = urlparse(target)
    if (parsed.hostname or "") not in allowed_hosts:
        return (
            "ACCESS DENIED — This laboratory tool only accepts localhost targets.",
            403
        )

    def generate():
        start_time = time.perf_counter()

        yield "╔════════════════════════════════════════════╗\n"
        yield "║        CYBER AUTHENTICATION LAB            ║\n"
        yield "║        LOCALHOST TESTING TERMINAL          ║\n"
        yield "╚════════════════════════════════════════════╝\n\n"

        yield "[+] Initializing laboratory test...\n"
        yield f"[+] Target      : {target}\n"
        yield f"[+] Identifier  : {login_type}\n"
        yield f"[+] Login Value : {login_value}\n"
        yield f"[+] Password    : {password_field}\n"
        yield f"[+] Candidates  : {len(password_list)}\n"
        yield "[+] Environment : LOCALHOST\n"
        yield "\n"
        yield "──────────────────────────────────────────────\n\n"

        attempt = 0

        for password in password_list:
            attempt += 1

            result = test_login(target, login_type, login_value, password_field, password)
            http_code = result["http_code"]

            if result.get("locked"):
                yield "[{:04d}] {:<18} [HTTP {}]  ".format(attempt, password, http_code)
                yield ">>> ACCOUNT LOCKED <<<\n\n"
                elapsed = time.perf_counter() - start_time
                yield "╔════════════════════════════════════════════╗\n"
                yield "║             PROTECTION DETECTED            ║\n"
                yield "╚════════════════════════════════════════════╝\n\n"
                yield f"[+] Login Identifier      : {login_value}\n"
                yield f"[+] Attempts Before Stop : {attempt}\n"
                yield "[+] Result                : Account temporarily locked.\n"
                yield "[+] Tester stopped because login protection was detected.\n"
                yield "[+] Wait for the lockout period before testing again.\n"
                yield f"[+] Elapsed Time          : {elapsed:.2f} seconds\n\n"
                yield "[+] PROTECTED LOGIN TEST COMPLETE.\n"
                return

            if result.get("error"):
                yield "[ERROR] "
                yield result["error"]
                yield "\n"
                break

            if result["success"]:
                yield "[{:04d}] {:<18} [HTTP {}]  ".format(attempt, password, http_code)
                yield ">>> SUCCESS <<<\n\n"
                elapsed = time.perf_counter() - start_time
                yield "╔════════════════════════════════════════════╗\n"
                yield "║              AUTHENTICATION               ║\n"
                yield "║                 MATCH                     ║\n"
                yield "╚════════════════════════════════════════════╝\n\n"
                yield f"[+] Login Identifier : {login_value}\n"
                yield f"[+] Candidate        : {password}\n"
                yield f"[+] HTTP Status      : {http_code}\n"
                yield f"[+] Attempts         : {attempt}\n"
                yield f"[+] Elapsed Time     : {elapsed:.2f} seconds\n"
                yield "\n"
                yield "[+] TEST COMPLETE.\n"
                return

            yield "[{:04d}] {:<18} [HTTP {}]  FAILED\n".format(attempt, password, http_code)

            time.sleep(0.05)  # usleep(50000) in the PHP version

        elapsed = time.perf_counter() - start_time

        yield "\n"
        yield "──────────────────────────────────────────────\n"
        yield "[!] TEST FINISHED\n"
        yield "[!] No configured candidate was detected\n"
        yield "[!] as a successful authentication.\n\n"
        yield f"[+] Attempts : {attempt}\n"
        yield f"[+] Time     : {elapsed:.2f} seconds\n"
        yield "──────────────────────────────────────────────\n"

    return Response(
        generate(),
        mimetype="text/plain; charset=UTF-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    print("=" * 52)
    print("CYBER LAB // AUTHENTICATION TESTER")
    print("Exact Python translation of lab_test.php")
    print("LOCALHOST ONLY")
    print("=" * 52)
    print("Open: http://127.0.0.1:5001")
    print(f"Target: {target}")
    print("=" * 52)

    app.run(host="127.0.0.1", port=5001, debug=False)