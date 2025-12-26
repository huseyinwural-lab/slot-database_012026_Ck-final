
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        print("Navigating to login...")
        await page.goto("http://localhost:3000/login")
        await page.wait_for_timeout(5000) # Wait 5s for whatever to load
        
        await page.screenshot(path="/app/artifacts/debug_login.png")
        print("Captured debug_login.png")
        
        content = await page.content()
        print("Page Content First 500 chars:")
        print(content[:500])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
