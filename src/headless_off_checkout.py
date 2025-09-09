import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import logging

# Set up logging for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# You can set this to False if you want to see the browser window pop up for debugging.
# Just make sure to change it back to True for faster runs.
headless_mode = False


def add_to_cart_supreme(url):
    """
    Simulates a user adding a product to the cart on a Supreme product page.
    """
    chrome_options = Options()
    if headless_mode:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
        driver.get(url)

        logging.info(f"Supreme: Waiting for page to load content from {url}...")

        # --- Step 1: Find and select a size from the dropdown menu. ---
        size_dropdown_xpath = "//select[@data-testid='size-dropdown']"
        size_dropdown_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, size_dropdown_xpath))
        )

        select = Select(size_dropdown_element)
        selected_size = None
        preferred_sizes = ["Medium", "Small", "Large"]

        for size in preferred_sizes:
            try:
                select.select_by_visible_text(size)
                selected_size = size
                logging.info(f"Supreme: Successfully selected size '{size}'.")
                break
            except Exception:
                logging.warning(f"Supreme: Size '{size}' not found or not selectable. Trying next size...")

        if not selected_size:
            logging.error("Supreme: All preferred sizes are sold out or not available.")
            return False

        # --- Step 2: Find and click the "Add to Cart" button. ---
        add_to_cart_xpath = "//button[@data-testid='add-to-cart-button']"
        add_to_cart_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, add_to_cart_xpath))
        )

        logging.info("Supreme: Successfully found 'Add to Cart' button.")
        add_to_cart_button.click()
        logging.info("Supreme: Successfully clicked the 'Add to Cart' button.")

        # Small delay to see the result before the browser closes.
        time.sleep(2)

        # Now that the item is in the cart, initiate the checkout process
        process_checkout_supreme(driver)

        # Optional: Add a longer sleep to see the checkout page
        time.sleep(10)

        return True

    except Exception as e:
        logging.error(f"Supreme: An error occurred during the 'Add to Cart' process: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def add_to_cart_palace(url):
    """
    Simulates a user adding a product to the cart on a Palace product page.
    """
    chrome_options = Options()
    if headless_mode:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
        driver.get(url)

        logging.info(f"Palace: Waiting for page to load content from {url}...")

        # --- Step 1: Find and select a size from the dropdown menu. ---
        size_dropdown_id = "variant-selector"
        size_dropdown_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, size_dropdown_id))
        )
        select = Select(size_dropdown_element)
        selected_size = None
        preferred_sizes = ["Medium", "Small", "Large"]

        for size in preferred_sizes:
            try:
                select.select_by_visible_text(size)
                selected_size = size
                logging.info(f"Palace: Successfully selected size '{size}'.")
                break
            except Exception:
                logging.warning(f"Palace: Size '{size}' not found or not selectable. Trying next size...")

        if not selected_size:
            logging.error("Palace: All preferred sizes are sold out or not available.")
            return False

        # --- Step 2: Find the "Add to Cart" button. ---
        # The locator has been updated to search for a button with type="submit".
        add_to_cart_xpath = "//button[@type='submit']"
        add_to_cart_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, add_to_cart_xpath))
        )

        logging.info("Palace: Successfully found 'Add to Cart' button.")
        add_to_cart_button.click()
        logging.info("Palace: Successfully clicked the 'Add to Cart' button.")

        # Small delay to see the result before the browser closes.
        time.sleep(2)

        # Now that the item is in the cart, initiate the checkout process
        process_checkout_palace(driver)

        # Optional: Add a longer sleep to see the checkout page
        time.sleep(10)

        return True

    except Exception as e:
        logging.error(f"Palace: An error occurred during the 'Add to Cart' process: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def process_checkout_supreme(driver):
    """
    Handles the checkout process for Supreme by finding and clicking the "Checkout Now" button.
    """
    try:
        logging.info("Supreme: Attempting to find and click the 'Checkout Now' link...")
        # A more robust locator combining data-testid and aria-label.
        checkout_link_xpath = "//a[@data-testid='mini-cart-checkout-link'][@aria-label='Supreme Checkout']"
        checkout_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, checkout_link_xpath))
        )
        checkout_link.click()
        logging.info("Supreme: Successfully clicked 'Checkout Now' link.")

        # Add a delay for the page to load
        time.sleep(5)

        # Now, fill the form
        fill_checkout_form(driver, user_data)

        return True
    except Exception as e:
        logging.error(f"Supreme: An error occurred during the checkout process: {e}")
        return False


def process_checkout_palace(driver):
    """
    Handles the checkout process for Palace by accepting terms and clicking the checkout button.
    """
    try:
        logging.info("Palace: Attempting to accept terms and click the 'Checkout' button...")
        # Step 1: Find and click the 'terms-checkbox'
        terms_checkbox_id = "terms-checkbox"
        terms_checkbox = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, terms_checkbox_id))
        )
        if not terms_checkbox.is_selected():
            terms_checkbox.click()
            logging.info("Palace: Successfully checked the 'agree to terms' checkbox.")

        # Step 2: Find and click the 'Checkout' button
        checkout_button_xpath = "//button[@aria-label='checkout-btn']"
        checkout_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, checkout_button_xpath))
        )
        checkout_button.click()
        logging.info("Palace: Successfully clicked the 'Checkout' button.")

        # Add a delay for the page to load
        time.sleep(5)

        # Now, fill the form
        fill_checkout_form(driver, user_data)

        return True
    except Exception as e:
        logging.error(f"Palace: An error occurred during the checkout process: {e}")
        return False


def fill_checkout_form(driver, user_data):
    """
    Fills out the shipping, contact, and credit card information on the checkout page.
    """
    logging.info("Starting to fill the checkout form...")
    try:
        # Fill in contact information
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "first_name"))).send_keys(
            user_data["Mishak"])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "last_name"))).send_keys(
            user_data["Sam-Hinton"])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(user_data["mishaksamhinton.nsa@gmail.com"])

        # Fill in delivery address
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "address1"))).send_keys(
            user_data["295 Dr MLK Blvd Jr."])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "city"))).send_keys(user_data["Newark"])

        # Select country from dropdown
        country_select = Select(WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "country"))))
        country_select.select_by_visible_text(user_data["United States"])

        # Select state from dropdown
        state_select = Select(WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "state"))))
        state_select.select_by_visible_text(user_data["New Jersey"])

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "zip_code"))).send_keys(
            user_data["07102"])

        # Fill in credit card information (Note: this is a simplified example)
        # In a real bot, you'd need to handle iframes for secure payment fields.
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "card_number"))).send_keys(
            user_data["1111222233334444"])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "card_exp"))).send_keys(
            user_data["12/28"])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "card_cvv"))).send_keys(
            user_data["730"])

        logging.info("Successfully filled the checkout form.")

    except Exception as e:
        logging.error(f"An error occurred while filling the form: {e}")


if __name__ == "__main__":
    # USER-CONFIGURABLE DATA: REPLACE THIS WITH YOUR OWN INFORMATION
    user_data = {
        "first_name": "Mishak",
        "last_name": "Sam-Hinton",
        "email": "mishaksamhinton.nsa@gmail.com",
        "address1": "295 Dr MLK Blvd Jr.",
        "city": "Newark",
        "country": "United States",
        "state": "New Jersey",
        "zip_code": "07102",
        "card_number": "1111222233334444",
        "card_exp": "12/26",
        "card_cvv": "123"
    }

    # A list of Supreme product URLs to test.
    supreme_product_urls = [
        "https://www.supremenewyork.com/shop/shirts/t82n1yq8v/t3g7f08s9",
        "https://us.supreme.com/products/65purvj_v03ui65a",
        "https://us.supreme.com/products/ugosvcu7uwonvtyn"
    ]

    logging.info(f"\n--- Starting Supreme 'Add to Cart' and Checkout process on multiple URLs ---")
    for url in supreme_product_urls:
        supreme_success = add_to_cart_supreme(url)
        if supreme_success:
            logging.info(f"✅ Supreme 'Add to Cart' process complete for URL: {url}")
        else:
            logging.info(f"❌ Supreme 'Add to Cart' process failed for URL: {url}")

    # A list of Palace product URLs to test.
    palace_product_urls = [
        "https://shop.palaceskateboards.com/products/p46-b-2200-c0c1b0a8c2",
        "https://shop-usa.palaceskateboards.com/products/bqp678j2rrbk",
        "https://shop-usa.palaceskateboards.com/products/esu046j91buz"
    ]

    logging.info(f"\n--- Starting Palace 'Add to Cart' and Checkout process on multiple URLs ---")
    for url in palace_product_urls:
        palace_success = add_to_cart_palace(url)
        if palace_success:
            logging.info(f"✅ Palace 'Add to Cart' process complete for URL: {url}")
        else:
            logging.info(f"❌ Palace 'Add to Cart' process failed for URL: {url}")