from playwright.sync_api import sync_playwright

def verify_theme():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to http://localhost:8501...")
            page.goto("http://localhost:8501", timeout=60000)

            # Wait for the main app container to load
            print("Waiting for .stApp...")
            page.wait_for_selector(".stApp", timeout=60000)

            # Wait a bit for styles to apply
            page.wait_for_timeout(5000)

            # Check background color of .stApp
            bg_color = page.evaluate("getComputedStyle(document.querySelector('.stApp')).backgroundColor")
            print(f"Background color: {bg_color}")

            # Check text color
            text_color = page.evaluate("getComputedStyle(document.querySelector('.stApp')).color")
            print(f"Text color: {text_color}")

            # Take screenshot
            print("Taking screenshot...")
            page.screenshot(path="verification/theme_verification.png", full_page=True)
            print("Screenshot saved to verification/theme_verification.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_theme()