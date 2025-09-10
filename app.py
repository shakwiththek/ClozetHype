# Sup_core_bot_UI.py
# This script creates a simple web-based user interface for the Supreme bot
# using Flask for the backend and a combined HTML/JS/CSS for the frontend.

from flask import Flask, request, jsonify, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from multiprocessing import Process, Queue
import time
import datetime
import pytz
import random
import logging
import json

app = Flask(__name__)
# A queue to hold log messages for real-time display in the UI
log_queue = Queue()


# Configure a simple logger to send messages to the queue
class QueueHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))


logger = logging.getLogger('bot_logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = QueueHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


# --- BOT LOGIC (adapted to be a single function) ---
def run_bot(user_data, product_url):
    """
    This function contains the full bot logic for a single user.
    It will be executed in a separate process for each user.
    """
    user_id = user_data['email']
    logger.info(f"\n--- Starting process for user {user_id} with browser: Chrome ---")

    try:
        driver = setup_browser()
        if not driver:
            logger.error(f"Driver setup failed for user {user_id}. Terminating process.")
            return
    except Exception as e:
        logger.error(f"Failed to set up browser for user {user_id}: {e}")
        return

    if not add_to_cart(driver, product_url):
        logger.error(f"Failed to add item to cart for user {user_id}. Terminating process.")
        driver.quit()
        return

    try:
        logger.info(f"Navigating to checkout for user {user_id}...")

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
        logger.info(f"Successfully clicked the checkout button for user {user_id}.")
    except TimeoutException:
        logger.error(f"Timed out waiting for the checkout button for user {user_id}. Cannot proceed.")
        driver.quit()
        return

    if complete_checkout(driver, user_data):
        logger.info(f"✅ Checkout successful for user {user_id}.")
    else:
        logger.error(f"❌ Checkout failed for user {user_id}.")

    # Pause the script for 30 seconds to allow manual inspection
    logger.info(
        "Pausing for 30 seconds to allow you to check the order status. The window will close after the pause.")
    time.sleep(30)

    driver.quit()

# --- New CAPTCHA Handling Logic ---
def check_and_handle_captcha(driver):
    try:
        captcha_locator = (By.XPATH, "//iframe[contains(@src, 'captcha')] | //div[@id='cf-turnstile-container']")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(captcha_locator)
        )
        logger.warning("🚨 CAPTCHA challenge detected!")
        logger.info("Please solve the CAPTCHA manually in the browser window.")
        input("Press Enter to continue the bot after solving the CAPTCHA...")
        logger.info("Continuing bot operations...")
        logger.info("Waiting for CAPTCHA page to disappear...")
        WebDriverWait(driver, 30).until(
            EC.invisibility_of_element_located(captcha_locator)
        )
        logger.info("CAPTCHA page is gone. Proceeding...")
    except TimeoutException:
        logger.info("No CAPTCHA challenge detected. Proceeding...")
    except Exception as e:
        logger.error(f"An unexpected error occurred during CAPTCHA check: {e}")

# --- Browser Setup Logic ---
def setup_browser():
    logger.info("Setting up Chrome...")
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome driver initialized.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome: {e}")
        return None

def add_to_cart(driver, product_url):
    logger.info(f"Navigating to product page: {product_url}")
    try:
        driver.get(product_url)
        check_and_handle_captcha(driver)
        try:
            sold_out_locator = (By.CSS_SELECTOR, 'button[data-testid="sold-out-button"][disabled]')
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(sold_out_locator))
            logger.warning("❌ This item is sold out. Skipping to the next product.")
            return False
        except TimeoutException:
            logger.info("Item is available. Proceeding with add to cart logic.")
        except Exception as e:
            logger.error(f"An error occurred during the sold out check: {e}")
        while True:
            try:
                size_dropdown_locator = (By.CSS_SELECTOR, 'select[data-testid="size-dropdown"]')
                sizes_to_try = ["Small", "Medium"]
                selected_size = False
                for size in sizes_to_try:
                    try:
                        select_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(size_dropdown_locator))
                        select = Select(select_element)
                        select.select_by_visible_text(size)
                        logger.info(f"Successfully selected size '{size}'.")
                        selected_size = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        logger.warning(f"Size '{size}' not found. Trying next size...")
                        continue
                if not selected_size:
                    logger.error("All preferred sizes are sold out or not available. Cannot add to cart.")
                    time.sleep(2)
                    driver.refresh()
                    continue
                add_to_cart_locator = (By.CSS_SELECTOR, 'button[data-testid="add-to-cart-button"]')
                add_to_cart_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(add_to_cart_locator))
                logger.info("Add to cart button found! Clicking...")
                add_to_cart_button.click()
                logger.info("Item successfully added to cart.")
                return True
            except TimeoutException:
                logger.info("Add to cart button not found yet. Refreshing and retrying...")
                driver.refresh()
                time.sleep(1)
            except Exception as e:
                logger.error(f"An unexpected error occurred during add_to_cart: {e}")
                return False
    except Exception as e:
        logger.error(f"Failed to add product at {product_url}: {e}")
        return False

def complete_checkout(driver, user_info):
    logger.info("\n--- Starting checkout process ---")
    check_and_handle_captcha(driver)
    try:
        if user_info['email'] == 'mishaksamhinton.nsa@gmail.com':
            logger.info("User is Mishak. Proceeding with PayPal checkout.")
            paypal_radio_button_locator = (By.ID, "basic-PAYPAL_EXPRESS")
            try:
                paypal_radio = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(paypal_radio_button_locator))
                logger.info("Found PayPal radio button. Clicking...")
                paypal_radio.click()
                logger.info("PayPal radio button clicked.")
                paypal_iframe_locator = (By.ID, "PAY_WITH_PAYPAL-iframe")
                paypal_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(paypal_iframe_locator))
                driver.switch_to.frame(paypal_iframe)
                paypal_button_locator = (By.XPATH, "//*[@id='paypal-button-container']//div[@role='button']")
                paypal_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(paypal_button_locator))
                paypal_button.click()
                logger.info("PayPal button clicked inside iframe. Proceeding to PayPal login page.")
                driver.switch_to.default_content()
                logger.info("Bot has handed over control for PayPal login. Please complete the process manually.")
                return True
            except TimeoutException:
                logger.error("Timed out waiting for PayPal elements. Cannot proceed with PayPal checkout.")
                return False
            except Exception as e:
                logger.error(f"An error occurred during PayPal checkout: {e}")
                return False
        else:
            logger.info("User is not Mishak. Proceeding with credit card checkout.")
            logger.info("Waiting for checkout fields to be present...")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
            logger.info("Filling in contact and delivery information...")
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
            try:
                save_address_checkbox = driver.find_element(By.ID, "save_shipping_information")
                if not save_address_checkbox.is_selected():
                    save_address_checkbox.click()
                    logger.info("Successfully clicked the 'Save Address' checkbox.")
                else:
                    logger.info("'Save Address' checkbox was already selected.")
            except NoSuchElementException:
                logger.warning("The 'Save Address' checkbox was not found. Skipping.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while handling the 'Save Address' checkbox: {e}")
            logger.info("Filling in payment information...")
            try:
                card_number_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Card number']")))
                driver.switch_to.frame(card_number_iframe)
                card_number_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "number")))
                card_number_field.send_keys(user_info['card_number'])
                logger.info("Card number filled successfully.")
            except TimeoutException:
                logger.error("Timed out waiting for the card number field. Cannot proceed.")
                return False
            except Exception as e:
                logger.error(f"Error filling card number: {e}")
                return False
            finally:
                driver.switch_to.default_content()
            try:
                expiry_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Expiration date (MM/YY)']")))
                driver.switch_to.frame(expiry_iframe)
                expiry_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "expiry")))
                expiry_field.send_keys(user_info['expiry_date'])
                logger.info("Expiry date filled successfully.")
            except TimeoutException:
                logger.error("Timed out waiting for the expiry date field. Cannot proceed.")
                return False
            except Exception as e:
                logger.error(f"Error filling expiry date: {e}")
                return False
            finally:
                driver.switch_to.default_content()
            try:
                cvv_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Security code']")))
                driver.switch_to.frame(cvv_iframe)
                cvv_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "verification_value")))
                cvv_field.send_keys(user_info['cvv'])
                logger.info("CVV filled successfully.")
            except TimeoutException:
                logger.error("Timed out waiting for the CVV field. Cannot proceed.")
                return False
            except Exception as e:
                logger.error(f"Error filling CVV: {e}")
                return False
            finally:
                driver.switch_to.default_content()
            try:
                name_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='Field container for: Name on card']")))
                driver.switch_to.frame(name_iframe)
                name_on_card_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "name")))
                name_on_card_field.send_keys(user_info['name_on_card'])
                logger.info("Name on card filled successfully.")
            except TimeoutException:
                logger.error("Timed out waiting for the name on card field. Cannot proceed.")
                return False
            except Exception as e:
                logger.error(f"Error filling name on card: {e}")
                return False
            finally:
                driver.switch_to.default_content()
            logger.info("Submitting the order...")
            place_order_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "checkout-pay-button")))
            place_order_button.click()
            try:
                logger.info("Verifying order status...")
                success_locator = (By.XPATH, "//*[contains(text(), 'Order Confirmed')]")
                failure_locator = (By.XPATH, "//*[contains(text(), 'Payment Failed') or contains(text(), 'Declined') or contains(text(), 'error')]")
                WebDriverWait(driver, 10).until(
                    EC.text_to_be_present_in_element(success_locator, 'Order Confirmed') or
                    EC.text_to_be_present_in_element(failure_locator, 'Payment Failed') or
                    EC.text_to_be_present_in_element(failure_locator, 'Declined')
                )
                if len(driver.find_elements(success_locator[0], success_locator[1])) > 0:
                    logger.info("✅ Payment was successful! Order confirmed.")
                    return True
                else:
                    logger.error("❌ Payment failed. An error message was detected on the page.")
                    return False
            except TimeoutException:
                logger.error("Timeout while waiting for order confirmation or failure message.")
                logger.error("Could not verify order status. Please check the website manually.")
                return False
    except Exception as e:
        logger.error(f"An error occurred during checkout: {e}")
        return False

def wait_for_drop_time(pre_test_url, enabled=True):
    if not enabled:
        logger.info("Timer is disabled for testing. Skipping wait period.")
        return
    eastern = pytz.timezone('US/Eastern')
    while True:
        now_eastern = datetime.datetime.now(eastern)
        target_time = now_eastern.replace(hour=11, minute=0, second=0, microsecond=0)
        pre_test_time = now_eastern.replace(hour=10, minute=59, second=0, microsecond=0)
        if now_eastern >= target_time:
            logger.info("Target drop time (11:00 AM EST) reached. Starting the bot.")
            break
        elif now_eastern >= pre_test_time and now_eastern < pre_test_time.replace(minute=59, second=5):
            logger.info("It's 10:59 AM. Performing a quick pre-test...")
            try:
                driver = webdriver.Chrome(service=ChromeService(), options=ChromeOptions())
                driver.get(pre_test_url)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="add-to-cart-button"]')))
                logger.info("Pre-test successful! The site is live and ready.")
            except Exception as e:
                logger.warning(f"Pre-test failed: {e}. Check the URL or locators.")
            finally:
                driver.quit()
            time.sleep(5)
        else:
            time_until_drop = target_time - now_eastern
            logger.info(f"Waiting for drop time... {time_until_drop} remaining.")
            time.sleep(5)

# --- FLASK WEB SERVER ROUTES ---

# HTML template for the UI
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Supreme Bot UI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen flex items-center justify-center p-4">

<div class="bg-gray-800 p-8 rounded-lg shadow-2xl w-full max-w-2xl">
    <h1 class="text-3xl font-semibold mb-6 text-center text-red-500">Supreme Bot</h1>
    <p class="text-center text-sm mb-6 text-gray-400">
        Configure your checkout details below and watch the magic happen.
    </p>

    <!-- User Information Form -->
    <form id="bot-form" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label for="first_name" class="block text-sm font-medium text-gray-400">First Name</label>
                <input type="text" id="first_name" name="first_name" class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 shadow-sm" required>
            </div>
            <div>
                <label for="last_name" class="block text-sm font-medium text-gray-400">Last Name</label>
                <input type="text" id="last_name" name="last_name" class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 shadow-sm" required>
            </div>
        </div>
        <div>
            <label for="email" class="block text-sm font-medium text-gray-400">Email</label>
            <input type="email" id="email" name="email" class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 shadow-sm" required>
        </div>
        <div>
            <label for="product_url" class="block text-sm font-medium text-gray-400">Product URL</label>
            <input type="url" id="product_url" name="product_url" class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 shadow-sm" required>
        </div>
        <!-- Other fields (address, payment, etc.) should be added here for a complete UI -->
    </form>

    <div class="flex justify-center mt-6">
        <button id="run-button" class="w-full md:w-auto px-6 py-3 rounded-full text-white font-bold bg-red-600 hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900 shadow-lg">
            Run Bot
        </button>
    </div>

    <!-- Bot Log Area -->
    <div id="log-container" class="mt-8 bg-gray-900 rounded-md p-4 max-h-60 overflow-y-auto">
        <h2 class="text-xl font-semibold mb-2 text-red-500">Bot Logs</h2>
        <pre id="log-output" class="text-xs text-gray-300 whitespace-pre-wrap"></pre>
    </div>
</div>

<script>
    document.getElementById('bot-form').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent form from submitting normally
    });

    document.getElementById('run-button').addEventListener('click', function() {
        const form = document.getElementById('bot-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const logOutput = document.getElementById('log-output');
        const logContainer = document.getElementById('log-container');
        const runButton = document.getElementById('run-button');

        runButton.disabled = true;
        runButton.textContent = 'Running...';
        logOutput.textContent = 'Starting bot process...\\n';

        // Initial API call to start the bot
        fetch('/run_bot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            logOutput.textContent += 'Bot process started. Check the browser window.\\n';
            console.log(data.message);
        })
        .catch(error => {
            logOutput.textContent += `Error: ${error.message}\\n`;
            runButton.disabled = false;
            runButton.textContent = 'Run Bot';
            console.error('Error:', error);
        });

        // Polling function to fetch logs every second
        const logInterval = setInterval(() => {
            fetch('/get_logs')
                .then(response => response.json())
                .then(data => {
                    if (data.logs.length > 0) {
                        data.logs.forEach(log => {
                            logOutput.textContent += log + '\\n';
                        });
                        logContainer.scrollTop = logContainer.scrollHeight; // Auto-scroll
                    }
                    if (data.status === 'finished' || data.status === 'failed') {
                        clearInterval(logInterval);
                        runButton.disabled = false;
                        runButton.textContent = 'Run Bot';
                    }
                })
                .catch(error => {
                    clearInterval(logInterval);
                    logOutput.textContent += `Error fetching logs: ${error.message}\\n`;
                    runButton.disabled = false;
                    runButton.textContent = 'Run Bot';
                    console.error('Error fetching logs:', error);
                });
        }, 1000);
    });
</script>

</body>
</html>
"""

@app.route('/')
def home():
    """Renders the main UI page."""
    return render_template_string(html_template)

@app.route('/run_bot', methods=['POST'])
def start_bot_process():
    """
    Starts the bot in a new process based on user data from the UI.
    This endpoint is called when the "Run Bot" button is clicked.
    """
    data = request.json
    product_url = data.get('product_url')
    # Create a basic user profile from the form data
    user_profile = {
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'email': data.get('email'),
        'country_code': 'US', # Hardcoded for this example
        'address': '123 Test St', # Hardcoded for this example
        'apt_unit': '',
        'city': 'Test City',
        'state_code': 'CA',
        'postal_code': '90210',
        'phone': '555-555-5555',
        'card_number': '4111222233334444',
        'expiry_date': '1225',
        'cvv': '123',
        'name_on_card': f"{data.get('first_name')} {data.get('last_name')}"
    }

    # Start the bot logic in a separate process to prevent the UI from freezing
    p = Process(target=run_bot, args=(user_profile, product_url))
    p.start()

    # The Flask app can now monitor the process and its logs
    # For simplicity, we just return a message and let the client-side JS poll for logs
    return jsonify({'message': 'Bot process started successfully'})

@app.route('/get_logs')
def get_logs():
    """
    An endpoint for the frontend to poll for new log messages.
    """
    logs = []
    while not log_queue.empty():
        logs.append(log_queue.get())
    return jsonify({'logs': logs})

if __name__ == '__main__':
    # Run the Flask app on the local machine
    app.run(debug=True, host='127.0.0.1', port=5000)
