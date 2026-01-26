# Tee Time Helper

An automated golf tee time booking tool that helps you secure tee times from ForeUp-powered golf course websites. Features a web-based UI with two booking modes.

## Features

### Mode 1: Continuous Scan
Continuously monitors the booking website for available tee times within your specified time range. When a slot becomes available (e.g., from a cancellation), it automatically books it.

- Select a target date
- Define a time window (e.g., 10:00am - 2:00pm)
- Set scan interval (how often to check)
- Auto-books the first available time in your range

### Mode 2: Instant Grab
Waits until the exact release time (typically 7pm PST for next-week bookings) and immediately grabs a pre-selected tee time.

- Set the release hour/minute
- Specify calendar row/column for the date
- Choose the exact tee time you want
- Executes the booking the moment times are released

## Requirements

- Python 3.10+
- Google Chrome browser
- ChromeDriver (automatically managed by Selenium)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   cd "Tee Time Helper"
   python3 -m venv tee_time_venv
   source tee_time_venv/bin/activate  # macOS/Linux
   # or
   tee_time_venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Activate the virtual environment**:
   ```bash
   source tee_time_venv/bin/activate
   ```

2. **Start the web server**:
   ```bash
   python app.py
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

## Usage Guide

### Using Continuous Scan Mode

1. Enter your **ForeUp account credentials** (email and password)
2. Select **Continuous Scan** mode (default)
3. Set the **Number of Players**
4. Pick your **Target Date** from the date picker
5. Choose your **Time Range**:
   - Start time (e.g., 10:03am)
   - End time (e.g., 2:06pm)
6. Set the **Scan Interval** (how often to check for availability)
7. Click **Start Scanner**
8. The scanner will:
   - Open a Chrome browser
   - Log into the booking site
   - Navigate to the target date
   - Check for available times in your range
   - If found, book the first available slot
   - If not found, wait and refresh to check again

### Using Instant Grab Mode

1. Enter your **ForeUp account credentials** (email and password)
2. Select **Instant Grab** mode
3. Set the **Number of Players**
4. Configure release time:
   - **Release Hour**: When tee times become available (usually 19 = 7pm PST)
   - **Release Minute**: Exact minute (usually 0)
5. Set calendar position:
   - **Calendar Row**: Which row your target date is in (1-6)
   - **Calendar Column**: Which column/day (1=Sun, 2=Mon, ..., 7=Sat)
6. Select the **Exact Time** you want to book
7. Click **Start Scanner**
8. The scanner will:
   - Open a Chrome browser
   - Log in and navigate to the booking page
   - Wait until the exact release time
   - Instantly click on your target date and time
   - Complete the booking

### Stopping the Scanner

Click the **Stop** button to halt any running scan. The browser will close automatically.

## File Structure

```
Tee Time Helper/
├── main.py              # Core scanner logic (TeeTimeScanner class)
├── app.py               # Flask web server and API endpoints
├── templates/
│   └── index.html       # Web UI
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── tee_time_venv/       # Virtual environment (not tracked in git)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the web UI |
| `/api/continuous-scan` | POST | Start continuous scanning mode |
| `/api/instant-grab` | POST | Start instant grab mode |
| `/api/stop` | POST | Stop the current scan |
| `/api/status` | GET | Get scanner status and log messages |
| `/api/times` | GET | Get list of available time slots |

## Available Time Slots

The golf course uses 9-minute tee time intervals starting at 6:00am:

```
6:00am, 6:09am, 6:18am, 6:27am, 6:36am, 6:45am, 6:54am,
7:03am, 7:12am, 7:21am, 7:30am, 7:39am, 7:48am, 7:57am,
8:06am, 8:15am, 8:24am, 8:33am, 8:42am, 8:51am, 9:00am,
... (continues through 3:00pm)
```

## Troubleshooting

### Browser doesn't open
- Ensure Chrome is installed
- Selenium 4.x automatically manages ChromeDriver

### Login fails
- Double-check your email and password
- Ensure your ForeUp account is active
- Check if the website structure has changed

### Date selection fails
- For Instant Grab: verify the row/column values match the calendar layout
- For Continuous Scan: ensure the date is within the bookable range

### Scanner stops unexpectedly
- Check the status log for error messages
- The website may have rate limiting; try increasing the scan interval

## Security

- **Credentials are never stored on disk** - they are only kept in memory during the session
- Credentials are entered through the web UI each time you start the application
- Safe to upload to Git - no sensitive data is hardcoded in the source code
- The application runs locally on your machine; credentials are not sent to any third-party servers

## Notes

- The scanner opens a visible Chrome browser window so you can monitor its progress
- Times are handled in PST (America/Los_Angeles timezone)
- The booking website is ForeUp Software (foreupsoftware.com)
- Course ID 19348 is hardcoded; modify `main.py` line 72 for different courses

## Disclaimer

This tool is for personal use only. Be respectful of the booking system and other golfers. Excessive automated requests may violate the website's terms of service.
