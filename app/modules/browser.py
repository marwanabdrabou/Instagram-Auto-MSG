from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (TimeoutException, NoSuchElementException, 
                                      ElementClickInterceptedException)
import time
import random
import logging
from config import CHROME_OPTIONS, SELECTORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramBrowser:
    def __init__(self, headless=False):
        self.driver = self._init_browser(headless)
        self.wait = WebDriverWait(self.driver, 20)
        
    def _init_browser(self, headless):
        """Initialize and return a configured browser instance"""
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", CHROME_OPTIONS)
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Additional options for stability
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Mask selenium detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        })
        
        return driver
    
    def login(self, username, password):
        """Login to Instagram account"""
        try:
            logger.info("Navigating to Instagram login page")
            self.driver.get("https://www.instagram.com/accounts/login/")
            
            # Handle cookie popup if it appears (EU)
            self._dismiss_cookie_popup()
            
            # Fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, SELECTORS['login_page']['username_field']))
            )
            self._type_like_human(username_field, username)
            
            # Fill password
            password_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, SELECTORS['login_page']['password_field']))
            )
            self._type_like_human(password_field, password)
            
            # Submit login
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, SELECTORS['login_page']['submit_button']))
            )
            submit_button.click()
            
            # Wait for login to complete
            time.sleep(random.uniform(3, 5))
            
            # Dismiss "Save Login Info" prompt
            self._dismiss_save_login_prompt()
            
            # Dismiss notifications prompt
            self._dismiss_notification_prompt()
            
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def send_message(self, profile_url, message_text):
        """Send message to a specific profile"""
        try:
            logger.info(f"Attempting to message profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(random.uniform(2, 4))
            
            # Find and click message button
            if not self._click_message_button():
                return False
            
            # Type and send message
            if not self._type_and_send_message(message_text):
                return False
            
            logger.info(f"Message successfully sent to {profile_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {profile_url}: {str(e)}")
            return False
    
    def _dismiss_cookie_popup(self):
        """Dismiss cookie consent popup if it appears"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow')]"))
            )
            cookie_button.click()
            time.sleep(1)
        except:
            pass
    
    def _dismiss_save_login_prompt(self):
        """Dismiss 'Save Login Info' prompt if it appears"""
        try:
            not_now_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            time.sleep(1)
        except:
            pass
    
    def _dismiss_notification_prompt(self):
        """Dismiss notification prompt if it appears"""
        try:
            not_now_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, SELECTORS['login_page']['not_now_button']))
            )
            not_now_button.click()
            time.sleep(1)
        except:
            pass
    
    def _click_message_button(self):
        """Find and click the message button on profile page"""
        for selector in SELECTORS['profile_page']['message_button']:
            try:
                message_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                message_button.click()
                time.sleep(random.uniform(1, 2))
                return True
            except:
                continue
        return False
    
    def _type_and_send_message(self, message_text):
        """Type message and send it"""
        try:
            message_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, SELECTORS['profile_page']['message_box']))
            )
            self._type_like_human(message_box, message_text)
            
            # Press Enter to send
            message_box.send_keys(Keys.ENTER)
            time.sleep(random.uniform(1, 2))
            return True
        except Exception as e:
            logger.error(f"Failed to type message: {str(e)}")
            return False
    
    def _type_like_human(self, element, text):
        """Type text into an element with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except:
            pass