import yaml
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DRIVER_PATH = config['DRIVER_PATH']


def get_driver():
    """
    The function sets up a Chrome WebDriver with options to disable popup
    blocking and notifications. The window size is set to 2048x1536 pixels.
    """
    try:
        service = Service(executable_path=DRIVER_PATH)
        chrome_options = Options()
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(2048, 1536)
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        sys.exit(1)

    return driver


# EXTRA FEATURES - FOR LATER USE

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By

# def close_popup(driver, css_selector: str):
#     try:
#         WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
#         close_button = driver.find_element(By.CSS_SELECTOR, css_selector)
#         close_button.click()
#     except Exception as e:
#         print("Exception while closing popup: ", e)
