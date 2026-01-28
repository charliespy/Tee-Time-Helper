from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import pytz
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Time slots available at the course (9-minute intervals)
TIME_BANK = [
    "6:00am", "6:09am", "6:18am", "6:27am", "6:36am", "6:45am", "6:54am",
    "7:03am", "7:12am", "7:21am", "7:30am", "7:39am", "7:48am", "7:57am",
    "8:06am", "8:15am", "8:24am", "8:33am", "8:42am", "8:51am", "9:00am",
    "9:09am", "9:18am", "9:27am", "9:36am", "9:45am", "9:54am", "10:03am",
    "10:12am", "10:21am", "10:30am", "10:39am", "10:48am", "10:57am", "11:06am",
    "11:15am", "11:24am", "11:33am", "11:42am", "11:51am", "12:00pm", "12:09pm",
    "12:18pm", "12:27pm", "12:36pm", "12:45pm", "12:54pm", "1:03pm", "1:12pm",
    "1:21pm", "1:30pm", "1:39pm", "1:48pm", "1:57pm", "2:06pm", "2:15pm",
    "2:24pm", "2:33pm", "2:42pm", "2:51pm", "3:00pm"
]

def parse_time_to_minutes(time_str):
    """Convert time string like '10:03am' to minutes from midnight."""
    time_str = time_str.lower().strip()
    is_pm = 'pm' in time_str
    time_str = time_str.replace('am', '').replace('pm', '')
    
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    
    if is_pm and hours != 12:
        hours += 12
    elif not is_pm and hours == 12:
        hours = 0
    
    return hours * 60 + minutes


def is_time_in_range(time_str, start_time, end_time):
    """Check if a time string falls within the given range."""
    time_minutes = parse_time_to_minutes(time_str)
    start_minutes = parse_time_to_minutes(start_time)
    end_minutes = parse_time_to_minutes(end_time)
    return start_minutes <= time_minutes <= end_minutes


def get_times_in_range(start_time, end_time):
    """Get all times from TIME_BANK that fall within the range."""
    return [t for t in TIME_BANK if is_time_in_range(t, start_time, end_time)]


class TeeTimeScanner:
    def __init__(self, username=None, password=None, status_callback=None, enable_notifications=False):
        self.driver = None
        self.wait = None
        self.is_running = False
        self.username = username
        self.password = password
        self.status_callback = status_callback or (lambda msg: print(msg))
        self.enable_notifications = enable_notifications
        self.notified_times = set()  # Track times we've already notified about
        
    def update_status(self, message):
        """Update status via callback."""
        self.status_callback(message)
    
    def send_push_notification(self, message, title="Tee Time Alert"):
        """Send a push notification via Pushover."""
        if not self.enable_notifications:
            return False
        
        # Get Pushover credentials from environment variables
        user_key = os.getenv('PUSHOVER_USER_KEY')
        api_token = os.getenv('PUSHOVER_API_TOKEN')
        
        if not all([user_key, api_token]):
            self.update_status("Notifications not configured: Missing Pushover credentials in .env file")
            return False
        
        try:
            import requests
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": api_token,
                    "user": user_key,
                    "title": title,
                    "message": message,
                    "priority": 1,  # High priority - shows as highlighted
                    "sound": "cashregister"  # Fun sound for tee time alerts
                }
            )
            if response.status_code == 200:
                self.update_status("Push notification sent!")
                return True
            else:
                self.update_status(f"Pushover error: {response.text}")
                return False
        except Exception as e:
            self.update_status(f"Failed to send notification: {e}")
            return False
        
    def start_browser(self):
        """Initialize the Chrome browser in headless mode for server deployment."""
        self.update_status("Starting browser...")
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # For Linux servers (uncomment if needed)
        # options.binary_location = '/usr/bin/chromium-browser'
        # service = Service('/usr/bin/chromedriver')
        # self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        self.is_running = True
        
    def stop_browser(self):
        """Close the browser."""
        self.is_running = False
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
        self.update_status("Browser closed.")
        
    def login(self):
        """Log into the ForeUp website."""
        if not self.username or not self.password:
            raise ValueError("Username and password are required")
            
        self.update_status("Navigating to login page...")
        # self.driver.get("https://foreupsoftware.com/index.php/booking/19347/1468#/teetimes") # Torrey
        self.driver.get("https://foreupsoftware.com/index.php/booking/19346/1469#/teetimes") # mission
        
        self.update_status("Entering credentials...")
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "login_email")))
        password_field = self.driver.find_element(By.ID, "login_password")
        time.sleep(1)
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        time.sleep(1)
        
        send_button = self.wait.until(EC.element_to_be_clickable((By.ID, "submit_button")))
        send_button.click()
        time.sleep(1)
        self.update_status("Logged in successfully!")
        
    def navigate_to_reservations(self):
        """Navigate to the reservations page."""
        self.update_status("Navigating to reservations...")
        # self.driver.get("https://foreupsoftware.com/index.php/booking/19347/1468#/teetimes") # Torrey
        self.driver.get("https://foreupsoftware.com/index.php/booking/19346/1469#/teetimes") # mission
        time.sleep(1)
        
    def start_new_reservation(self, num_people):
        """Start a new reservation with the specified number of people."""
        self.update_status("Starting new reservation...")
        resident_button = self.wait.until(EC.element_to_be_clickable(
            # (By.XPATH, "//button[contains(text(), 'Resident (0 - 7 Days)')]"))) # Torrey
            (By.XPATH, "//button[contains(text(), 'STANDARD TEE TIMES')]"))) # mission
        resident_button.click()
        time.sleep(1)
        
        self.update_status(f"Selecting {num_people} player(s)...")
        players_button = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//a[@class='btn btn-primary' and @data-value='{num_people}']")))
        players_button.click()
        time.sleep(1)
        
    def select_date_by_value(self, target_date):
        """Select a date from the calendar by its date value (YYYY-MM-DD format)."""
        self.update_status(f"Selecting date: {target_date}...")
        
        # Parse the target date
        target = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        target_day = str(target.day)
        target_month_year = target.strftime("%B %Y")  # e.g., "February 2026"
        
        # Navigate to the correct month if needed
        max_attempts = 12
        for _ in range(max_attempts):
            try:
                # Check if we're on the correct month by reading the calendar header
                # The header typically shows "Month Year" (e.g., "January 2026")
                month_header = self.driver.find_element(
                    By.XPATH, "//th[@class='datepicker-switch']"
                ).text.strip()
                
                self.update_status(f"Current calendar month: {month_header}, looking for: {target_month_year}")
                
                if month_header == target_month_year:
                    # We're on the correct month, find and click the day
                    # Look for a td with class "day" that:
                    # - Is NOT disabled, old, or new
                    # - Contains the target day number
                    date_element = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//td[contains(@class, 'day') and not(contains(@class, 'disabled')) and not(contains(@class, 'old')) and not(contains(@class, 'new')) and normalize-space(text())='{target_day}']")))
                    date_element.click()
                    time.sleep(2)
                    self.update_status(f"Selected date: {target_date}")
                    return True
                else:
                    # Not on the correct month, click next
                    next_button = self.driver.find_element(By.XPATH, "//th[@class='next']")
                    next_button.click()
                    time.sleep(0.5)
                    
            except TimeoutException:
                self.update_status(f"Timeout waiting for date element")
                # Try clicking next month
                try:
                    next_button = self.driver.find_element(By.XPATH, "//th[@class='next']")
                    next_button.click()
                    time.sleep(0.5)
                except NoSuchElementException:
                    break
            except NoSuchElementException as e:
                self.update_status(f"Element not found: {e}")
                break
        
        self.update_status(f"Could not find date: {target_date}")
        return False
        
    def get_available_times(self):
        """Get all available tee times currently displayed."""
        available_times = []
        try:
            time.sleep(1)
            time_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'booking-start-time-label')]")
            
            for elem in time_elements:
                time_text = elem.text.strip()
                if time_text:
                    available_times.append(time_text)
                    
        except Exception as e:
            self.update_status(f"Error getting times: {e}")
            
        return available_times
        
    def scan_available_times(self, start_time, end_time):
        """Scan for available times within the specified range."""
        available = self.get_available_times()
        matching = [t for t in available if is_time_in_range(t, start_time, end_time)]
        return matching
        
    def refresh_times(self, target_date):
        """Refresh the tee times by re-selecting the date."""
        self.update_status("Refreshing tee times...")
        self.select_date_by_value(target_date)
    
    # ==================== Continuous Scan (Monitor Only) ====================
    
    def continuous_scan(self, num_people, target_date, start_time, end_time, scan_interval=60):
        """
        Monitor for available tee times in a range (does not book automatically).
        
        Args:
            num_people: Number of players
            target_date: Date to monitor (YYYY-MM-DD format)
            start_time: Start of time range (e.g., '10:00am')
            end_time: End of time range (e.g., '2:00pm')
            scan_interval: Seconds between scans (default 60)
        """
        try:
            self.start_browser()
            self.login()
            self.navigate_to_reservations()
            self.start_new_reservation(num_people)
            
            if not self.select_date_by_value(target_date):
                self.update_status("Failed to select date. Stopping.")
                return False
            
            scan_count = 0
            while self.is_running:
                scan_count += 1
                self.update_status(f"Scan #{scan_count}: Looking for times between {start_time} and {end_time}...")
                
                matching_times = self.scan_available_times(start_time, end_time)
                
                if matching_times:
                    self.update_status(f"*** FOUND AVAILABLE TIMES: {matching_times} ***")
                    
                    # Send notification for newly found times (avoid spamming for same times)
                    new_times = [t for t in matching_times if t not in self.notified_times]
                    if new_times and self.enable_notifications:
                        times_str = ', '.join(new_times)
                        self.send_push_notification(
                            f"{times_str} on {target_date}\n\nBook now before it's gone at https://foreupsoftware.com/index.php/booking/19346/1469#/teetimes!",
                            title="Tee Time Available!"
                        )
                        self.notified_times.update(new_times)
                    
                    # Keep scanning - user will manually book
                else:
                    self.update_status(f"No times available in range. Next scan in {scan_interval}s...")
                    
                # Wait before next scan
                for _ in range(scan_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
                # Refresh the page for fresh data
                if self.is_running:
                    self.refresh_times(target_date)
                    
            self.update_status("Scan stopped.")
            return False
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            raise

