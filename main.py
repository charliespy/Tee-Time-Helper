from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import pytz

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
    def __init__(self, username=None, password=None, status_callback=None):
        self.driver = None
        self.wait = None
        self.is_running = False
        self.username = username
        self.password = password
        self.status_callback = status_callback or (lambda msg: print(msg))
        
    def update_status(self, message):
        """Update status via callback."""
        self.status_callback(message)
        
    def start_browser(self):
        """Initialize the Chrome browser."""
        self.update_status("Starting browser...")
        self.driver = webdriver.Chrome()
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
        self.driver.get("https://foreupsoftware.com/index.php/booking/19348#/login")
        
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
        """Navigate to the reservations tab."""
        self.update_status("Navigating to reservations...")
        reservations_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "reservations-tab")))
        reservations_tab.click()
        time.sleep(1)
        
    def start_new_reservation(self, num_people):
        """Start a new reservation with the specified number of people."""
        self.update_status("Starting new reservation...")
        reserve_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary")))
        reserve_button.click()
        time.sleep(1)
        
        book_now_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='BOOK NOW']")))
        book_now_button.click()
        time.sleep(1)
        
        self.update_status(f"Selecting {num_people} player(s)...")
        players_button = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//a[@class='btn btn-primary' and @data-value='{num_people}']")))
        players_button.click()
        time.sleep(1)
        
    def select_date(self, row, col):
        """Select a date from the calendar using row and column."""
        self.update_status(f"Selecting date at row {row}, column {col}...")
        td_element = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"(//table[contains(@class, 'table-condensed')]//tbody//tr[{row}]//td[{col}])")))
        self.update_status(f"Found date: {td_element.text}")
        td_element.click()
        time.sleep(2)
        
    def select_date_by_value(self, target_date):
        """Select a date from the calendar by its date value (YYYY-MM-DD format)."""
        self.update_status(f"Selecting date: {target_date}...")
        
        # Parse the target date
        target = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        
        # Navigate to the correct month if needed
        max_attempts = 12
        for _ in range(max_attempts):
            try:
                # Try to find and click the date directly
                date_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//td[@data-date='{target_date}' and not(contains(@class, 'disabled'))]")))
                date_element.click()
                time.sleep(2)
                self.update_status(f"Selected date: {target_date}")
                return True
            except TimeoutException:
                # Click next month button
                try:
                    next_button = self.driver.find_element(By.XPATH, "//th[@class='next']")
                    next_button.click()
                    time.sleep(0.5)
                except NoSuchElementException:
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
        
    def book_time(self, reservation_time):
        """Book a specific tee time."""
        self.update_status(f"Booking time: {reservation_time}...")
        
        time_tile = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class, 'booking-start-time-label') and text()='{reservation_time}']")))
        time_tile.click()
        time.sleep(1)
        
        book_time_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "js-book-button")))
        book_time_button.click()
        time.sleep(1)
        
        self.update_status(f"Successfully booked {reservation_time}!")
        return True
        
    def refresh_times(self):
        """Refresh the tee times page."""
        self.driver.refresh()
        time.sleep(2)
        
    # ==================== Mode 1: Instant Grab ====================
    
    def instant_grab(self, num_people, wait_until, row, col, reservation_time):
        """
        Original functionality: Wait until release time, then grab a specific tee time.
        
        Args:
            num_people: Number of players
            wait_until: datetime to wait until before grabbing
            row: Calendar row for the date
            col: Calendar column for the date
            reservation_time: Specific time to book (e.g., '2:06pm')
        """
        try:
            self.start_browser()
            self.login()
            self.navigate_to_reservations()
            self.start_new_reservation(num_people)
            
            pst = pytz.timezone('America/Los_Angeles')
            self.update_status("Waiting for release time...")
            
            while self.is_running:
                now = datetime.datetime.now(pst)
                if now >= wait_until:
                    self.select_date(row, col)
                    self.book_time(reservation_time)
                    break
                time.sleep(0.001)
                
            self.update_status("Instant grab complete!")
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            raise
            
    # ==================== Mode 2: Continuous Scan ====================
    
    def continuous_scan(self, num_people, target_date, start_time, end_time, scan_interval=30):
        """
        New functionality: Continuously scan for available times in a range.
        
        Args:
            num_people: Number of players
            target_date: Date to book (YYYY-MM-DD format)
            start_time: Start of time range (e.g., '10:00am')
            end_time: End of time range (e.g., '2:00pm')
            scan_interval: Seconds between scans (default 30)
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
                    self.update_status(f"Found available times: {matching_times}")
                    # Book the first available time
                    first_time = matching_times[0]
                    if self.book_time(first_time):
                        self.update_status(f"Successfully booked {first_time}!")
                        return True
                else:
                    self.update_status(f"No times available in range. Next scan in {scan_interval}s...")
                    
                # Wait before next scan
                for _ in range(scan_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
                # Refresh the page for fresh data
                if self.is_running:
                    self.refresh_times()
                    
            self.update_status("Scan stopped.")
            return False
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            raise


# ==================== Legacy function for backwards compatibility ====================

def reserve_tee_time(username, password, num_people, wait_until, row, col, reservation_time):
    """Legacy function that wraps the TeeTimeScanner for backwards compatibility."""
    scanner = TeeTimeScanner(username=username, password=password)
    try:
        scanner.instant_grab(num_people, wait_until, row, col, reservation_time)
        input("Press Enter to exit...")
    finally:
        scanner.stop_browser()


if __name__ == '__main__':
    import getpass
    
    print("=== Tee Time Helper (CLI Mode) ===")
    username = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")
    
    pst = pytz.timezone('America/Los_Angeles')
    standard_wait = datetime.datetime.now(pst).replace(hour=19, minute=0, second=0, microsecond=0)
    
    num_people = 2
    row = 5
    col = 1
    reservation_time = '2:06pm'
    
    reserve_tee_time(username, password, num_people, standard_wait, row, col, reservation_time)
