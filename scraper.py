import undetected_chromedriver as uc
import time

# Setup with options to keep browser stable
options = uc.ChromeOptions()
options.add_argument('--disable-popup-blocking')
options.add_argument('--no-first-run')

driver = uc.Chrome(options=options, use_subprocess=True)

# Open the page
url = "https://trends.google.com/trends/explore?date=now%207-d&geo=AU&q=ai&hl=en-AU"
driver.get(url)

# Wait then refresh
time.sleep(4)
driver.refresh()

# Wait for page to load
time.sleep(8)

# Scroll down slowly
for i in range(5):
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(0.5)

time.sleep(2)

# Take screenshot
driver.save_screenshot("google_trends.png")
print("Screenshot saved as google_trends.png")

# Close properly
try:
    driver.close()
    driver.quit()
except:
    pass