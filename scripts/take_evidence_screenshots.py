
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set Viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Login
        print("Logging in...")
        await page.goto("http://localhost:3000/login")
        await page.fill('input[type="email"]', "admin@casino.com")
        await page.fill('input[type="password"]', "Admin123!")
        await page.click('button[type="submit"]')
        await page.wait_for_url("http://localhost:3000/")
        print("Login successful.")

        # 1. Robots Page
        print("Navigating to Robots Page...")
        await page.goto("http://localhost:3000/robots")
        await page.wait_for_selector("table", state="visible") # Wait for table
        await page.screenshot(path="/app/artifacts/screenshots/robot_catalog.png")
        print("Captured robot_catalog.png")

        # 2. Game Config -> Robot Tab
        print("Navigating to Games Page...")
        await page.goto("http://localhost:3000/games")
        
        # Find the first "Config" button. 
        # Based on GameManagement.jsx: Button variant="outline" with Settings2 icon and text "Config"
        # We can use text="Config"
        await page.wait_for_selector('button:has-text("Config")', state="visible")
        
        print("Opening Game Config...")
        await page.click('button:has-text("Config") >> nth=0') # Click the first one

        # Wait for Dialog
        await page.wait_for_selector('div[role="dialog"]', state="visible")
        
        # Click "Math Engine" tab
        # Based on GameConfigPanel.jsx: <TabsTrigger value="robot">Math Engine</TabsTrigger>
        print("Switching to Math Engine tab...")
        await page.click('button[role="tab"]:has-text("Math Engine")')
        
        # Wait for tab content
        try:
            await page.wait_for_selector('text=Active Robot Strategy', timeout=5000)
        except Exception as e:
            print("Could not find specific text, taking screenshot anyway.")
        
        # Small delay for animation
        await page.wait_for_timeout(1000)

        await page.screenshot(path="/app/artifacts/screenshots/game_robot_binding.png")
        print("Captured game_robot_binding.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
