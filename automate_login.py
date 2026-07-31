import asyncio
import subprocess
import sys
import os
import time
from playwright.async_api import async_playwright

async def run():
    print("🚀 Starting Backend Uvicorn Server process on port 8099...")
    backend_env = os.environ.copy()
    backend_env.pop("PYTHONHOME", None)
    backend_env.pop("PYTHONPATH", None)
    
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8099"],
        cwd="backend",
        env=backend_env
    )
    time.sleep(3) # Give Uvicorn time to start

    try:
        async with async_playwright() as p:
            print("🌐 Opening http://localhost:3000/login in Chromium...")
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            page = await browser.new_page()

            page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}"))
            page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
            page.on("requestfailed", lambda req: print(f"[NETWORK FAILED] {req.method} {req.url} - {req.failure}"))
            page.on("response", lambda res: print(f"[HTTP {res.status}] {res.request.method} {res.url}"))

            await page.goto("http://localhost:3000/login")
            await page.wait_for_timeout(2000)

            print("🔑 Filling email: admin@company.com & password: admin...")
            await page.fill('input[type="email"]', 'admin@company.com')
            await page.fill('input[type="password"]', 'admin')

            print("👆 Clicking Sign In button...")
            await page.click('button[type="submit"]')

            # Wait for dashboard navigation
            await page.wait_for_timeout(5000)

            current_url = page.url
            print(f"\n📍 Final Browser URL: {current_url}")

            await page.screenshot(path="/Users/kartikyadavalli/.gemini/antigravity/brain/aa2091e7-21d9-42c0-acf8-77dc9ae28c7a/live_dashboard.png")
            print("📸 Saved live_dashboard.png")

            await browser.close()
    finally:
        print("🛑 Stopping Uvicorn server process...")
        server_proc.terminate()

asyncio.run(run())
