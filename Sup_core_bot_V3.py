# timed_supreme_bot_V18.py
# This script automates multiple, concurrent checkouts with staggered starts
# and includes a fix for the updated checkout button selector.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
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
                    time.sleep(5)
                    driver.refresh()
                    continue

                add_to_cart_locator = (By.CSS_SELECTOR, 'button[data-testid="add-to-cart-button"]')

                add_to_cart_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(add_to_cart_locator)
                )

                logging.info("Add to cart button found! Clicking...")
                add_to_cart_button.click()
                logging.info("Item successfully added to cart.")

                time.sleep(1)

                return True

            except TimeoutException:
                logging.info("Add to cart button not found yet. Refreshing and retrying...")
                driver.refresh()
                time.sleep(2)
            except Exception as e:
                logging.error(f"An unexpected error occurred during add_to_cart: {e}")
                return False

    except Exception as e:
        logging.error(f"Failed to add product at {product_url}: {e}")
        return False


def complete_checkout(driver, user_info):
    """
    Automates the checkout process, including payment submission and result verification.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        user_info (dict): A dictionary containing all the user's information.
    """
    logging.info("\n--- Starting checkout process ---")

    try:
        logging.info("Waiting for checkout fields to be present...")
        WebDriverWait(driver, 15).until(
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

        logging.info("Filling in payment information...")
        card_number_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Card number']"))
        )
        driver.switch_to.frame(card_number_iframe)
        card_number_field = driver.find_element(By.ID, "number")
        card_number_field.send_keys(user_info['card_number'])
        driver.switch_to.default_content()

        expiry_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[@title='Field container for: Expiration date (MM/YY)']"))
        )
        driver.switch_to.frame(expiry_iframe)
        expiry_field = driver.find_element(By.ID, "expiry")
        expiry_field.send_keys(user_info['expiry_date'])
        driver.switch_to.default_content()

        cvv_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Security code']"))
        )
        driver.switch_to.frame(cvv_iframe)
        cvv_field = driver.find_element(By.ID, "verification_value")
        cvv_field.send_keys(user_info['cvv'])
        driver.switch_to.default_content()

        name_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Name on card']"))
        )
        driver.switch_to.frame(name_iframe)
        name_on_card_field = driver.find_element(By.ID, "name")
        name_on_card_field.send_keys(user_info['name_on_card'])
        driver.switch_to.default_content()

        logging.info("Submitting the order...")
        place_order_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "checkout-pay-button"))
        )
        place_order_button.click()

        try:
            logging.info("Verifying order status...")
            success_locator = (By.XPATH, "//*[contains(text(), 'Order Confirmed')]")
            failure_locator = (By.XPATH,
                               "//*[contains(text(), 'Payment Failed') or contains(text(), 'Declined') or contains(text(), 'error')]")

            WebDriverWait(driver, 15).until(
                EC.text_to_be_present_in_element_text(success_locator, 'Order Confirmed') or
                EC.text_to_be_present_in_element_text(failure_locator, 'Payment Failed') or
                EC.text_to_be_present_in_element_text(failure_locator, 'Declined')
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
                driver = webdriver.Chrome(service=ChromeService(), options=Options())
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
    logging.info(f"\n--- Starting process for user {user_id} ---")

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)

    if not add_to_cart(driver, product_url):
        logging.error(f"Failed to add item to cart for user {user_id}. Terminating process.")
        driver.quit()
        return

    try:
        logging.info(f"Navigating to checkout for user {user_id} via 'checkout now' button...")
        # NEW: Using a more stable XPath to locate the checkout link by its text.
        checkout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'checkout')]"))
        )
        checkout_button.click()
        logging.info(f"Successfully clicked the 'checkout now' button for user {user_id}.")
    except TimeoutException:
        logging.error(f"Timed out waiting for the 'checkout now' button for user {user_id}. Cannot proceed.")
        driver.quit()
        return

    if complete_checkout(driver, user_data):
        logging.info(f"✅ Checkout successful for user {user_id}.")
    else:
        logging.error(f"❌ Checkout failed for user {user_id}.")

    driver.quit()


if __name__ == "__main__":
    user_profiles = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'country_code': 'US',
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
        },
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
            'first_name': 'Michael',
            'last_name': 'Brown',
            'email': 'michael.brown@example.com',
            'country_code': 'US',
            'address': '789 Pine Blvd',
            'apt_unit': 'Apt 2D',
            'city': 'Someville',
            'state_code': 'TX',
            'postal_code': '75001',
            'phone': '555-555-5555',
            'card_number': '5555666677778888',
            'expiry_date': '0824',
            'cvv': '789',
            'name_on_card': 'Michael Brown'
        },
        {
            'first_name': 'Emily',
            'last_name': 'Davis',
            'email': 'emily.davis@example.com',
            'country_code': 'US',
            'address': '321 Elm Way',
            'apt_unit': '',
            'city': 'Anytown',
            'state_code': 'WA',
            'postal_code': '98101',
            'phone': '555-111-2222',
            'card_number': '9999000011112222',
            'expiry_date': '1027',
            'cvv': '012',
            'name_on_card': 'Emily Davis'
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
        sleep_time = random.uniform(0.1, 0.5)
        logging.info(f"Staggering next launch by {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)

    for p in processes:
        p.join()

    logging.info("\n--- All parallel checkouts have been processed. ---")
