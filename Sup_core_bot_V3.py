# checkout_bot.py
# This script uses Selenium to automate filling out a checkout form.
# This is a template; you must update the element locators for your target website.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import logging

# Set up logging for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s - %(funcName)s')


def complete_checkout(driver, user_info):
    """
    Automates the checkout process by filling out form fields and submitting the order.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        user_info (dict): A dictionary containing all the user's information.
    """
    logging.info("\n--- Starting checkout process ---")

    try:
        # Step 1: Wait for the form fields to be present.
        logging.info("Waiting for checkout fields to be present...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "email"))
        )

        # Step 2: Fill out the contact and delivery fields using the provided user_info.
        logging.info("Filling in contact and delivery information...")

        # Email field using its ID
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys(user_info['email'])

        # First name field using its name attribute
        first_name_field = driver.find_element(By.NAME, "firstName")
        first_name_field.send_keys(user_info['first_name'])

        # Last name field using its name attribute
        last_name_field = driver.find_element(By.NAME, "lastName")
        last_name_field.send_keys(user_info['last_name'])

        # Country/Region select dropdown using its name
        country_select = Select(driver.find_element(By.NAME, "countryCode"))
        country_select.select_by_value(user_info['country_code'])  # e.g., 'US' or 'CA'

        # Address field using its ID
        address_field = driver.find_element(By.ID, "shipping-address1")
        address_field.send_keys(user_info['address'])

        # Apt/unit field using its name attribute
        apt_field = driver.find_element(By.NAME, "address2")
        apt_field.send_keys(user_info['apt_unit'])

        # City field using its name attribute
        city_field = driver.find_element(By.NAME, "city")
        city_field.send_keys(user_info['city'])

        # State select dropdown using its name
        state_select = Select(driver.find_element(By.NAME, "zone"))
        state_select.select_by_value(user_info['state_code'])  # e.g., 'NY' or 'CA'

        # Postal code field using its name attribute
        postal_code_field = driver.find_element(By.NAME, "postalCode")
        postal_code_field.send_keys(user_info['postal_code'])

        # Phone number field using its name attribute
        phone_field = driver.find_element(By.NAME, "phone")
        phone_field.send_keys(user_info['phone'])

        # Step 3: Handle credit card information.
        # NOTE: This is for demonstration purposes only. Never store real credit card info.
        logging.info("Filling in payment information...")

        # The credit card fields are often inside iframes for security.
        # We must switch to each iframe individually.

        # Find and switch to the iframe for the credit card number field
        card_number_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Card number']"))
        )
        driver.switch_to.frame(card_number_iframe)
        card_number_field = driver.find_element(By.ID, "number")
        card_number_field.send_keys(user_info['card_number'])
        driver.switch_to.default_content()  # Switch back to the main page

        # Find and switch to the iframe for the expiry date field
        expiry_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[@title='Field container for: Expiration date (MM/YY)']"))
        )
        driver.switch_to.frame(expiry_iframe)
        expiry_field = driver.find_element(By.ID, "expiry")
        expiry_field.send_keys(user_info['expiry_date'])
        driver.switch_to.default_content()  # Switch back to the main page

        # Find and switch to the iframe for the security code field
        cvv_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Security code']"))
        )
        driver.switch_to.frame(cvv_iframe)
        cvv_field = driver.find_element(By.ID, "verification_value")
        cvv_field.send_keys(user_info['cvv'])
        driver.switch_to.default_content()  # Switch back to the main page

        # Find and switch to the iframe for the name on card field
        name_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Name on card']"))
        )
        driver.switch_to.frame(name_iframe)
        name_on_card_field = driver.find_element(By.ID, "name")
        name_on_card_field.send_keys(user_info['name_on_card'])
        driver.switch_to.default_content()  # Switch back to the main page

        # Step 4: Click the "Place Order" button.
        # You will need to find the correct locator for this button.
        # logging.info("Submitting the order...")
        # place_order_button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.ID, "checkout_button"))
        # )
        # place_order_button.click()

        # logging.info("Order submitted! Waiting for confirmation...")
        # time.sleep(10) # Wait for the order confirmation page to load

        return True

    except Exception as e:
        logging.error(f"An error occurred during checkout: {e}")
        return False


if __name__ == "__main__":
    # Define a simple user profile with fake data.
    user_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'test@example.com',
        'country_code': 'US',  # Use 'CA' or 'MX' if needed
        'address': '123 Main St',
        'apt_unit': 'Apt 4B',
        'city': 'Anytown',
        'state_code': 'NY',
        'postal_code': '12345',
        'phone': '555-123-4567',
        'card_number': '1111222233334444',
        'expiry_date': '1225',
        'cvv': '123',
        'name_on_card': 'John Doe'
    }

    # Set up Chrome for a live test.
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)

    # TODO: Replace with the actual checkout URL of the website.
    checkout_url = "https://www.example.com/checkout"

    driver.get(checkout_url)

    success = complete_checkout(driver, user_data)

    driver.quit()

    if success:
        logging.info("\n✅ Checkout process completed successfully.")
    else:
        logging.info("\n❌ Checkout process failed. Please check the logs and element locators.")