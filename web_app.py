from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="EmergencyCharge AI",
    description="Emergency laptop-to-phone charging assistant",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EmergencyCharge AI</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                font-family: Arial, sans-serif;
                color: #f4f7ff;
                background: #080d19;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }
            .card {
                width: 100%;
                max-width: 720px;
                padding: 42px;
                border: 1px solid #263550;
                border-radius: 22px;
                background: #101a2b;
                box-shadow: 0 20px 70px #0008;
            }
            .badge {
                display: inline-block;
                padding: 8px 12px;
                border-radius: 20px;
                background: #153a32;
                color: #66f0bc;
                font-size: 12px;
                letter-spacing: 1px;
            }
            h1 { font-size: clamp(32px, 6vw, 48px); margin-bottom: 12px; }
            h1 span { color: #67a8ff; }
            p { color: #b7c3d9; line-height: 1.7; }
            .devices {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin: 28px 0;
            }
            .device {
                padding: 20px;
                border: 1px solid #2a3a55;
                border-radius: 14px;
                background: #0b1322;
            }
            .icon { font-size: 30px; }
            .device h3 { margin-bottom: 8px; }
            button {
                width: 100%;
                padding: 15px;
                border: 0;
                border-radius: 10px;
                background: #438cff;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
            #status {
                margin-top: 18px;
                padding: 14px;
                border-radius: 10px;
                background: #0b1322;
                font-size: 14px;
            }
            .note { font-size: 12px; margin-top: 22px; }
            @media (max-width: 500px) {
                .card { padding: 24px; }
                .devices { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <main class="card">
            <div class="badge">EMERGENCY POWER TECHNOLOGY</div>
            <h1>EmergencyCharge <span>AI</span></h1>
            <p>
                A concept for safer emergency phone charging using
                your laptop, with power checks and safety-aware decisions.
            </p>

            <div class="devices">
                <div class="device">
                    <div class="icon">💻</div>
                    <h3>Laptop</h3>
                    <p>Potential power source</p>
                </div>
                <div class="device">
                    <div class="icon">📱</div>
                    <h3>Phone</h3>
                    <p>Device to be charged</p>
                </div>
            </div>

            <button onclick="checkStatus()">Check System Status</button>
            <div id="status">System ready for a demo status check.</div>

            <p class="note">
                Demo interface only. This hosted page cannot directly
                inspect your laptop hardware or initiate charging.
            </p>
        </main>

        <script>
            async function checkStatus() {
                const box = document.getElementById("status");
                box.textContent = "Checking application status...";

                try {
                    const response = await fetch("/api/health");
                    if (!response.ok) throw new Error("Request failed");
                    const data = await response.json();
                    box.textContent = data.message;
                } catch (error) {
                    box.textContent =
                        "Could not check status. Please try again.";
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "message": "EmergencyCharge AI web app is running."
    }
