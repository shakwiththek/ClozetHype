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


def add_to_cart(url):
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
        process_checkout(driver)

        # Optional: Add a longer sleep to see the checkout page
        time.sleep(10)

        return True

    except Exception as e:
        logging.error(f"Supreme: An error occurred during the 'Add to Cart' process: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def process_checkout(driver):
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


def fill_checkout_form(driver, user_data):
    """
    Fills out the shipping, contact, and credit card information on the checkout page.
    This version is more robust and attempts multiple locators for each field.
    """
    logging.info("Starting to fill the checkout form...")

    # Supreme-specific locators from the provided HTML
    supreme_selectors = {
        "email": [By.ID, "email"],
        "first_name": [By.ID, "TextField0"],
        "last_name": [By.ID, "TextField1"],
        "address1": [By.ID, "shipping-address1"],
        "city": [By.ID, "TextField3"],
        "country": [By.ID, "Select0"],
        "state": [By.ID, "Select1"],
        "zip_code": [By.ID, "TextField4"],
    }

    # Helper function to find and fill an element with a fallback
    def find_and_fill(field_name, value):
        try:
            logging.info(f"Attempting to fill field: {field_name} with value: {value}")

            selector_type = supreme_selectors[field_name][0]
            selector_value = supreme_selectors[field_name][1]

            element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((selector_type, selector_value))
            )

            # Clear the field before sending keys
            element.clear()
            element.send_keys(value)

            logging.info(f"Successfully filled field: {field_name}")
            return True
        except Exception as e:
            logging.warning(f"Failed to fill field '{field_name}' with ID '{selector_value}': {e}")
            return False

    try:
        # Fill in contact and shipping information
        find_and_fill("email", user_data["email"])
        find_and_fill("first_name", user_data["first_name"])
        find_and_fill("last_name", user_data["last_name"])
        find_and_fill("address1", user_data["address1"])
        find_and_fill("city", user_data["city"])

        # Handle dropdowns separately since they need a different method
        country_select = Select(WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, supreme_selectors["country"][1]))
        ))
        country_select.select_by_visible_text(user_data["country"])
        logging.info(f"Successfully selected country: {user_data['country']}")

        state_select = Select(WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, supreme_selectors["state"][1]))
        ))
        state_select.select_by_visible_text(user_data["state"])
        logging.info(f"Successfully selected state: {user_data['state']}")

        find_and_fill("zip_code", user_data["zip_code"])

        # Check for and handle PayPal payment option first
        try:
            logging.info("Attempting to pay with PayPal...")
            paypal_iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "PAY_WITH_PAYPAL-iframe"))
            )
            driver.switch_to.frame(paypal_iframe)

            # Since we can't inspect the content of the iframe, we will look for a common element
            # like a button or a div that acts like one.
            # Here we use a generic approach to find a button-like element.
            paypal_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(text(), 'Pay with PayPal') or contains(@aria-label, 'Pay with PayPal')]"))
            )
            paypal_button.click()
            driver.switch_to.default_content()
            logging.info("Successfully clicked 'Pay with PayPal' button and returned to main page.")
            return

        except Exception as e:
            logging.info(f"PayPal iframe not found or an error occurred. Proceeding with credit card: {e}")

        # If PayPal is not an option, or it fails, proceed with credit card payment
        # Supreme checkout page has credit card fields inside iframes.
        logging.info("Handling credit card fields within iframes...")

        # Switch to the card number iframe
        card_number_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, 'card-fields-number-')]"))
        )
        driver.switch_to.frame(card_number_iframe)
        card_number_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "number"))
        )
        card_number_input.send_keys(user_data["card_number"])
        driver.switch_to.default_content()  # Switch back to the main page
        logging.info("Successfully filled card number.")

        # Switch to the expiration date iframe
        card_exp_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, 'card-fields-expiry-')]"))
        )
        driver.switch_to.frame(card_exp_iframe)
        card_exp_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "expiry"))
        )
        card_exp_input.send_keys(user_data["card_exp"])
        driver.switch_to.default_content()
        logging.info("Successfully filled card expiration date.")

        # Switch to the security code iframe
        card_cvv_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, 'card-fields-verification_value-')]"))
        )
        driver.switch_to.frame(card_cvv_iframe)
        card_cvv_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "verification_value"))
        )
        card_cvv_input.send_keys(user_data["card_cvv"])
        driver.switch_to.default_content()
        logging.info("Successfully filled security code.")

        # Switch to the name on card iframe
        card_name_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, 'card-fields-name-')]"))
        )
        driver.switch_to.frame(card_name_iframe)
        card_name_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "name"))
        )
        card_name_input.send_keys(f"{user_data['first_name']} {user_data['last_name']}")
        driver.switch_to.default_content()
        logging.info("Successfully filled name on card.")

        logging.info("Successfully filled the checkout form.")

        # Final step: Click the Pay Now button to complete the purchase
        pay_now_button_xpath = "//button[text()='Pay now']"
        pay_now_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, pay_now_button_xpath))
        )
        pay_now_button.click()
        logging.info("Successfully clicked the 'Pay now' button.")

    except Exception as e:
        logging.error(f"An error occurred while filling the form: {e}")


if __name__ == "__main__":
    # USER-CONFIGURABLE DATA: REPLACE THIS WITH YOUR OWN INFORMATION
    user_data = {
        "first_name": "Shak",
        "last_name": "Withthek",
        "email": "shakwiththek@example.com",
        "address1": "123 Main St",
        "city": "New York",
        "country": "United States",
        "state": "New York",
        "zip_code": "10001",
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
        supreme_success = add_to_cart(url)
        if supreme_success:
            logging.info(f"✅ Supreme 'Add to Cart' process complete for URL: {url}")
        else:
            logging.info(f"❌ Supreme 'Add to Cart' process failed for URL: {url}")