import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_with_selenium(url):
    """
    Scrapes a dynamic website using Selenium to render JavaScript content.
    It then uses BeautifulSoup to parse the rendered HTML.
    """
    # Set up Chrome options for a headless browser (running without a visible UI)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize the WebDriver
    try:
        driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
        driver.get(url)

        print(f"Waiting for page to load content from {url}...")

        # Wait for the body element to be present, which indicates the page has loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Get the page source after JavaScript has rendered the content
        html_content = driver.page_source

        # Now, we can use BeautifulSoup to parse the rendered HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # You would add your specific parsing logic here.
        # This example just prints the title.
        title = soup.find('title').text
        print(f"Successfully scraped page with title: {title}")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None
    finally:
        # It's crucial to close the driver to free up resources
        if 'driver' in locals() and driver:
            driver.quit()

# --- Main execution block ---
if __name__ == "__main__":
    # Use a dynamic website URL for demonstration
    # Note: This is a placeholder, you'll need to find a specific product page with dynamic content.
    dynamic_url = "https://www.google.com"
    scrape_with_selenium(dynamic_url)






