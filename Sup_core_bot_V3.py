# timed_supreme_bot_V24.py
# This script automates multiple, concurrent checkouts with staggered starts,
# using only Chrome for each process to ensure a consistent and reliable environment.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from multiprocessing import Process
import time
import logging
import datetime
import pytz
import random

# Set up logging for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s - %(funcName)s')


# --- New CAPTCHA Handling Logic ---
def check_and_handle_captcha(driver):
    """
    Checks for the presence of a Cloudflare or similar CAPTCHA challenge.
    If detected, the script will pause and prompt the user for manual intervention.
    """
    try:
        # Look for a common CAPTCHA iframe or div
        captcha_locator = (By.XPATH, "//iframe[contains(@src, 'captcha')] | //div[@id='cf-turnstile-container']")

        # We use a short timeout here to avoid significant delays if no CAPTCHA is present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(captcha_locator)
        )

        logging.warning("🚨 CAPTCHA challenge detected!")
        logging.info("Please solve the CAPTCHA manually in the browser window.")
        # This input call will pause the script and wait for user input
        input("Press Enter to continue the bot after solving the CAPTCHA...")
        logging.info("Continuing bot operations...")

        # New: Wait for the CAPTCHA page to disappear after the user has finished.
        logging.info("Waiting for CAPTCHA page to disappear...")
        WebDriverWait(driver, 30).until(
            EC.invisibility_of_element_located(captcha_locator)
        )
        logging.info("CAPTCHA page is gone. Proceeding...")

    except TimeoutException:
        logging.info("No CAPTCHA challenge detected. Proceeding...")
    except Exception as e:
        logging.error(f"An unexpected error occurred during CAPTCHA check: {e}")


# --- Browser Setup Logic ---
def setup_browser():
    """
    Sets up and returns a Selenium WebDriver instance for Chrome.
    """
    logging.info("Setting up Chrome...")
    chrome_options = ChromeOptions()
    # The headless argument has been removed to make the browser visible for debugging.
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Chrome driver initialized.")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Chrome: {e}")
        raise RuntimeError("Chrome setup failed.")


def add_to_cart(driver, product_url):
    """
    Navigates to a single product page, selects a size, and adds the item to the cart.
    The function now retries continuously until the add-to-cart button is found.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        product_url (str): The URL of the product to add.
    """
    logging.info(f"Navigating to product page: {product_url}")
    try:
        driver.get(product_url)

        # Check for CAPTCHA immediately after page load
        check_and_handle_captcha(driver)

        try:
            sold_out_locator = (By.CSS_SELECTOR, 'button[data-testid="sold-out-button"][disabled]')
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(sold_out_locator))
            logging.warning("❌ This item is sold out. Skipping to the next product.")
            return False
        except TimeoutException:
            logging.info("Item is available. Proceeding with add to cart logic.")
        except Exception as e:
            logging.error(f"An error occurred during the sold out check: {e}")

        while True:
            try:
                size_dropdown_locator = (By.CSS_SELECTOR, 'select[data-testid="size-dropdown"]')

                sizes_to_try = ["Small", "Medium"]
                selected_size = False

                for size in sizes_to_try:
                    try:
                        select_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(size_dropdown_locator)
                        )
                        select = Select(select_element)
                        select.select_by_visible_text(size)
                        logging.info(f"Successfully selected size '{size}'.")
                        selected_size = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        logging.warning(f"Size '{size}' not found. Trying next size...")
                        continue

                if not selected_size:
                    logging.error("All preferred sizes are sold out or not available. Cannot add to cart.")
                    time.sleep(2)
                    driver.refresh()
                    continue

                add_to_cart_locator = (By.CSS_SELECTOR, 'button[data-testid="add-to-cart-button"]')

                add_to_cart_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(add_to_cart_locator)
                )

                logging.info("Add to cart button found! Clicking...")
                add_to_cart_button.click()
                logging.info("Item successfully added to cart.")

                return True

            except TimeoutException:
                logging.info("Add to cart button not found yet. Refreshing and retrying...")
                driver.refresh()
                time.sleep(1)
            except Exception as e:
                logging.error(f"An unexpected error occurred during add_to_cart: {e}")
                return False

    except Exception as e:
        logging.error(f"Failed to add product at {product_url}: {e}")
        return False


def complete_checkout(driver, user_info):
    """
    Automates the checkout process. Uses PayPal for the user 'Mishak' and
    credit card for all other users.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        user_info (dict): A dictionary containing all the user's information.
    """
    logging.info("\n--- Starting checkout process ---")

    # The CAPTCHA check is moved to the top to handle security pages first
    check_and_handle_captcha(driver)

    try:
        # Check if the user is Mishak and should use PayPal
        if user_info['email'] == 'mishaksamhinton.nsa@gmail.com':
            logging.info("User is Mishak. Proceeding with PayPal checkout.")
            paypal_radio_button_locator = (By.ID, "basic-PAYPAL_EXPRESS")

            try:
                # Wait for the PayPal radio button to be clickable before clicking
                paypal_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(paypal_radio_button_locator)
                )
                logging.info("Found PayPal radio button. Clicking...")
                paypal_radio.click()
                logging.info("PayPal radio button clicked.")

                # Wait for the iframe to be present and switch to it
                paypal_iframe_locator = (By.ID, "PAY_WITH_PAYPAL-iframe")
                paypal_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(paypal_iframe_locator)
                )
                driver.switch_to.frame(paypal_iframe)

                # Wait for and click the "Pay with PayPal" button inside the iframe
                paypal_button_locator = (By.XPATH, "//*[@id='paypal-button-container']//div[@role='button']")
                paypal_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(paypal_button_locator)
                )
                paypal_button.click()
                logging.info("PayPal button clicked inside iframe. Proceeding to PayPal login page.")

                # Switch back to the main document
                driver.switch_to.default_content()

                # The script will stop here to allow manual completion of the PayPal flow
                logging.info("Bot has handed over control for PayPal login. Please complete the process manually.")
                return True

            except TimeoutException:
                logging.error("Timed out waiting for PayPal elements. Cannot proceed with PayPal checkout.")
                return False
            except Exception as e:
                logging.error(f"An error occurred during PayPal checkout: {e}")
                return False

        # If not Mishak, proceed with the original credit card checkout logic
        else:
            logging.info("User is not Mishak. Proceeding with credit card checkout.")
            logging.info("Waiting for checkout fields to be present...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )

            logging.info("Filling in contact and delivery information...")

            email_field = driver.find_element(By.ID, "email")
            email_field.send_keys(user_info['email'])
            first_name_field = driver.find_element(By.NAME, "firstName")
            first_name_field.send_keys(user_info['first_name'])
            last_name_field = driver.find_element(By.NAME, "lastName")
            last_name_field.send_keys(user_info['last_name'])
            country_select = Select(driver.find_element(By.NAME, "countryCode"))
            country_select.select_by_value(user_info['country_code'])
            address_field = driver.find_element(By.ID, "shipping-address1")
            address_field.send_keys(user_info['address'])
            apt_field = driver.find_element(By.NAME, "address2")
            apt_field.send_keys(user_info['apt_unit'])
            city_field = driver.find_element(By.NAME, "city")
            city_field.send_keys(user_info['city'])
            state_select = Select(driver.find_element(By.NAME, "zone"))
            state_select.select_by_value(user_info['state_code'])
            postal_code_field = driver.find_element(By.NAME, "postalCode")
            postal_code_field.send_keys(user_info['postal_code'])
            phone_field = driver.find_element(By.NAME, "phone")
            phone_field.send_keys(user_info['phone'])

            # --- Save Address Checkbox Logic ---
            try:
                save_address_checkbox = driver.find_element(By.ID, "save_shipping_information")
                if not save_address_checkbox.is_selected():
                    save_address_checkbox.click()
                    logging.info("Successfully clicked the 'Save Address' checkbox.")
                else:
                    logging.info("'Save Address' checkbox was already selected.")
            except NoSuchElementException:
                logging.warning("The 'Save Address' checkbox was not found. Skipping.")
            except Exception as e:
                logging.error(f"An unexpected error occurred while handling the 'Save Address' checkbox: {e}")
            # --- End of Save Address Checkbox Logic ---

            logging.info("Filling in payment information...")

            # --- Refactored Card Info Section for Robustness ---

            # Card Number
            try:
                card_number_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Card number']"))
                )
                driver.switch_to.frame(card_number_iframe)
                card_number_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "number"))
                )
                card_number_field.send_keys(user_info['card_number'])
                logging.info("Card number filled successfully.")
            except TimeoutException:
                logging.error("Timed out waiting for the card number field. Cannot proceed.")
                return False
            except Exception as e:
                logging.error(f"Error filling card number: {e}")
                return False
            finally:
                driver.switch_to.default_content()

            # Expiry Date
            try:
                expiry_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//iframe[@title='Field container for: Expiration date (MM/YY)']"))
                )
                driver.switch_to.frame(expiry_iframe)
                expiry_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "expiry"))
                )
                expiry_field.send_keys(user_info['expiry_date'])
                logging.info("Expiry date filled successfully.")
            except TimeoutException:
                logging.error("Timed out waiting for the expiry date field. Cannot proceed.")
                return False
            except Exception as e:
                logging.error(f"Error filling expiry date: {e}")
                return False
            finally:
                driver.switch_to.default_content()

            # CVV
            try:
                cvv_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Security code']"))
                )
                driver.switch_to.frame(cvv_iframe)
                cvv_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "verification_value"))
                )
                cvv_field.send_keys(user_info['cvv'])
                logging.info("CVV filled successfully.")
            except TimeoutException:
                logging.error("Timed out waiting for the CVV field. Cannot proceed.")
                return False
            except Exception as e:
                logging.error(f"Error filling CVV: {e}")
                return False
            finally:
                driver.switch_to.default_content()

            # Name on Card
            try:
                name_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Name on card']"))
                )
                driver.switch_to.frame(name_iframe)
                name_on_card_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "name"))
                )
                name_on_card_field.send_keys(user_info['name_on_card'])
                logging.info("Name on card filled successfully.")
            except TimeoutException:
                logging.error("Timed out waiting for the name on card field. Cannot proceed.")
                return False
            except Exception as e:
                logging.error(f"Error filling name on card: {e}")
                return False
            finally:
                driver.switch_to.default_content()

            # --- End of Refactored Card Info Section ---

            logging.info("Submitting the order...")
            place_order_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "checkout-pay-button"))
            )
            place_order_button.click()

            try:
                logging.info("Verifying order status...")
                success_locator = (By.XPATH, "//*[contains(text(), 'Order Confirmed')]")
                failure_locator = (By.XPATH,
                                   "//*[contains(text(), 'Payment Failed') or contains(text(), 'Declined') or contains(text(), 'error')]")

                WebDriverWait(driver, 10).until(
                    EC.text_to_be_present_in_element(success_locator, 'Order Confirmed') or
                    EC.text_to_be_present_in_element(failure_locator, 'Payment Failed') or
                    EC.text_to_be_present_in_element(failure_locator, 'Declined')
                )

                if len(driver.find_elements(success_locator[0], success_locator[1])) > 0:
                    logging.info("✅ Payment was successful! Order confirmed.")
                    return True
                else:
                    logging.error("❌ Payment failed. An error message was detected on the page.")
                    return False

            except TimeoutException:
                logging.error("Timeout while waiting for order confirmation or failure message.")
                logging.error("Could not verify order status. Please check the website manually.")
                return False

    except Exception as e:
        logging.error(f"An error occurred during checkout: {e}")
        return False


def wait_for_drop_time(pre_test_url, enabled=True):
    """
    Waits until the designated drop time and performs a pre-test at 10:59 AM.

    Args:
        pre_test_url (str): The URL to use for the pre-test.
        enabled (bool): If False, the function will return immediately for testing.
    """
    if not enabled:
        logging.info("Timer is disabled for testing. Skipping wait period.")
        return

    eastern = pytz.timezone('US/Eastern')

    while True:
        now_eastern = datetime.datetime.now(eastern)

        target_time = now_eastern.replace(hour=11, minute=0, second=0, microsecond=0)

        pre_test_time = now_eastern.replace(hour=10, minute=59, second=0, microsecond=0)

        if now_eastern >= target_time:
            logging.info("Target drop time (11:00 AM EST) reached. Starting the bot.")
            break

        elif now_eastern >= pre_test_time and now_eastern < pre_test_time.replace(minute=59, second=5):
            logging.info("It's 10:59 AM. Performing a quick pre-test...")
            try:
                driver = webdriver.Chrome(service=ChromeService(), options=ChromeOptions())
                driver.get(pre_test_url)
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="add-to-cart-button"]'))
                )
                logging.info("Pre-test successful! The site is live and ready.")
            except Exception as e:
                logging.warning(f"Pre-test failed: {e}. Check the URL or locators.")
            finally:
                driver.quit()
            time.sleep(5)

        else:
            time_until_drop = target_time - now_eastern
            logging.info(f"Waiting for drop time... {time_until_drop} remaining.")
            time.sleep(5)


def run_bot(user_data, product_url):
    """
    This function contains the full bot logic for a single user.
    It will be executed in a separate process for each user.
    """
    user_id = user_data['email']
    logging.info(f"\n--- Starting process for user {user_id} with browser: Chrome ---")

    try:
        driver = setup_browser()
        if not driver:
            logging.error(f"Driver setup failed for user {user_id}. Terminating process.")
            return
    except Exception as e:
        logging.error(f"Failed to set up browser for user {user_id}: {e}")
        return

    if not add_to_cart(driver, product_url):
        logging.error(f"Failed to add item to cart for user {user_id}. Terminating process.")
        driver.quit()
        return

    try:
        logging.info(f"Navigating to checkout for user {user_id}...")

        # Check for CAPTCHA before attempting checkout
        check_and_handle_captcha(driver)

        # Directly look for the "checkout now" button using the provided XPath.
        checkout_locator = (By.XPATH, '//*[@id="MainContent"]/div[1]/div[1]/div[2]/a[2]')

        # Wait for the checkout button to become clickable.
        # This is more direct and reliable than waiting for the "add to cart" button to disappear.
        checkout_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(checkout_locator)
        )
        checkout_button.click()
        logging.info(f"Successfully clicked the checkout button for user {user_id}.")
    except TimeoutException:
        logging.error(f"Timed out waiting for the checkout button for user {user_id}. Cannot proceed.")
        driver.quit()
        return

    if complete_checkout(driver, user_data):
        logging.info(f"✅ Checkout successful for user {user_id}.")
    else:
        logging.error(f"❌ Checkout failed for user {user_id}.")

    # Pause the script for 30 seconds to allow manual inspection
    logging.info(
        "Pausing for 30 seconds to allow you to check the order status. The window will close after the pause.")
    time.sleep(30)

    driver.quit()


if __name__ == "__main__":
    user_profiles = [
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'country_code': 'US',
            'address': '456 Oak Ave',
            'apt_unit': 'Unit 1C',
            'city': 'Somewhere',
            'state_code': 'CA',
            'postal_code': '90210',
            'phone': '555-987-6543',
            'card_number': '4444333322221111',
            'expiry_date': '0526',
            'cvv': '456',
            'name_on_card': 'Jane Smith'
        },
        {
            'first_name': 'Mishak',
            'last_name': 'Sam-Hinton',
            'email': 'mishaksamhinton.nsa@gmail.com',
            'country_code': 'US',
            'address': '295 Dr MLK Blvd Jr.',
            'apt_unit': 'Floor 1',
            'city': 'Newark',
            'state_code': 'NJ',
            'postal_code': '07102',
            'phone': '201-300-9652',
            'card_number': '5555666677778888',
            'expiry_date': '0824',
            'cvv': '789',
            'name_on_card': 'Mishak Sam-Hinton'
        },
        {
            'first_name': 'Mishak',
            'last_name': 'Sam-Hinton',
            'email': 'mishaksamhinton.nsa@gmail.com',
            'country_code': 'US',
            'address': '295 Dr MLK Blvd Jr.',
            'apt_unit': 'Floor 1',
            'city': 'Newark',
            'state_code': 'NJ',
            'postal_code': '07102',
            'phone': '201-300-9652',
            'card_number': '',  # This is intentionally left blank for PayPal users
            'expiry_date': '',
            'cvv': '',
            'name_on_card': ''
        }
    ]

    product_url_to_buy = "https://us.supreme.com/products/ugosvcu7uwonvtyn?new=1"

    wait_for_drop_time(product_url_to_buy, enabled=False)

    processes = []
    logging.info("Starting multiple processes to run checkouts in parallel...")
    for user_data in user_profiles:
        p = Process(target=run_bot, args=(user_data, product_url_to_buy))
        processes.append(p)
        p.start()
        sleep_time = random.uniform(0.05, 0.1)
        logging.info(f"Staggering next launch by {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)

    for p in processes:
        p.join()

    logging.info("\n--- All parallel checkouts have been processed. ---")





