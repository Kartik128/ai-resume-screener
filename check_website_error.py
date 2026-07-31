import asyncio
from playwright.async_api import async_playwright

async def check_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("=== CHECKING PORT 3000 & PORT 3001 & PORT 8099 ===")
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
        page.on("requestfailed", lambda req: print(f"[NETWORK FAILED] {req.method} {req.url} - {req.failure}"))
        page.on("response", lambda res: print(f"[HTTP {res.status}] {res.request.method} {res.url}"))

        for url in ["http://localhost:3000/login", "http://localhost:3001/login"]:
            try:
                print(f"\n🌐 Loading {url}...")
                res = await page.goto(url, timeout=5000)
                print(f"Status: {res.status if res else 'None'}")
                await page.wait_for_timeout(2000)
                await page.screenshot(path=f"/Users/kartikyadavalli/.gemini/antigravity/brain/aa2091e7-21d9-42c0-acf8-77dc9ae28c7a/error_check.png")
            except Exception as e:
                print(f"FAILED to load {url}: {e}")

        await browser.close()

asyncio.run(check_site())
