from flask import Flask, render_template, jsonify, request
from main import TeeTimeScanner, TIME_BANK
import threading
import datetime
import pytz
import queue

app = Flask(__name__)

# Global state
scanner = None
scanner_thread = None
status_messages = queue.Queue()
current_status = "Idle"
is_scanning = False


def status_callback(message):
    """Callback to update status from scanner."""
    global current_status
    current_status = message
    status_messages.put(message)
    print(f"[Scanner] {message}")


def run_instant_grab(username, password, num_people, wait_until, target_date, reservation_time):
    """Run instant grab in a background thread."""
    global scanner, is_scanning
    is_scanning = True
    scanner = TeeTimeScanner(username=username, password=password, status_callback=status_callback)
    try:
        scanner.instant_grab(num_people, wait_until, target_date, reservation_time)
    except Exception as e:
        status_callback(f"Error: {e}")
    finally:
        is_scanning = False
        if scanner:
            scanner.stop_browser()


def run_continuous_scan(username, password, num_people, target_date, start_time, end_time, scan_interval):
    """Run continuous scan in a background thread."""
    global scanner, is_scanning
    is_scanning = True
    scanner = TeeTimeScanner(username=username, password=password, status_callback=status_callback)
    try:
        scanner.continuous_scan(num_people, target_date, start_time, end_time, scan_interval)
    except Exception as e:
        status_callback(f"Error: {e}")
    finally:
        is_scanning = False
        if scanner:
            scanner.stop_browser()


@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html', time_bank=TIME_BANK)


@app.route('/api/status')
def get_status():
    """Get current scanner status."""
    messages = []
    while not status_messages.empty():
        try:
            messages.append(status_messages.get_nowait())
        except queue.Empty:
            break
    
    return jsonify({
        'status': current_status,
        'is_running': is_scanning,
        'messages': messages
    })


@app.route('/api/instant-grab', methods=['POST'])
def start_instant_grab():
    """Start instant grab mode."""
    global scanner_thread, is_scanning
    
    if is_scanning:
        return jsonify({'error': 'Scanner is already running'}), 400
    
    data = request.json
    
    # Get credentials
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    num_people = int(data.get('num_people', 2))
    target_date = data.get('target_date')  # YYYY-MM-DD format
    reservation_time = data.get('reservation_time', '7:57am')
    
    if not target_date:
        return jsonify({'error': 'target_date is required'}), 400
    
    # Parse wait time
    wait_hour = int(data.get('wait_hour', 19))
    wait_minute = int(data.get('wait_minute', 0))
    
    pst = pytz.timezone('America/Los_Angeles')
    wait_until = datetime.datetime.now(pst).replace(
        hour=wait_hour, minute=wait_minute, second=0, microsecond=0
    )
    
    # If the time has passed today, set it for tomorrow
    if wait_until < datetime.datetime.now(pst):
        wait_until += datetime.timedelta(days=1)
    
    scanner_thread = threading.Thread(
        target=run_instant_grab,
        args=(username, password, num_people, wait_until, target_date, reservation_time),
        daemon=True
    )
    scanner_thread.start()
    
    return jsonify({
        'message': 'Instant grab started',
        'wait_until': wait_until.isoformat(),
        'target_date': target_date,
        'reservation_time': reservation_time
    })


@app.route('/api/continuous-scan', methods=['POST'])
def start_continuous_scan():
    """Start continuous scan mode."""
    global scanner_thread, is_scanning
    
    if is_scanning:
        return jsonify({'error': 'Scanner is already running'}), 400
    
    data = request.json
    
    # Get credentials
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    num_people = int(data.get('num_people', 2))
    target_date = data.get('target_date')  # YYYY-MM-DD format
    start_time = data.get('start_time', '10:00am')
    end_time = data.get('end_time', '2:00pm')
    scan_interval = int(data.get('scan_interval', 60))
    
    if not target_date:
        return jsonify({'error': 'target_date is required'}), 400
    
    scanner_thread = threading.Thread(
        target=run_continuous_scan,
        args=(username, password, num_people, target_date, start_time, end_time, scan_interval),
        daemon=True
    )
    scanner_thread.start()
    
    return jsonify({
        'message': 'Continuous scan started',
        'target_date': target_date,
        'time_range': f'{start_time} - {end_time}'
    })


@app.route('/api/stop', methods=['POST'])
def stop_scanner():
    """Stop the current scanner."""
    global scanner, is_scanning
    
    if scanner:
        scanner.is_running = False
        status_callback("Stopping scanner...")
    
    return jsonify({'message': 'Stop signal sent'})


@app.route('/api/times')
def get_times():
    """Get available time slots."""
    return jsonify({'times': TIME_BANK})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
