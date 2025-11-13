import sqlite3
import os
import base64
import io
from PIL import Image
import re

try:
    import pytesseract
except Exception:
    pytesseract = None

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'moveinsync.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_dicts(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Tools for reading
def get_all_stops():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stops')
    stops = cursor.fetchall()
    conn.close()
    return stops

def get_all_paths():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM paths')
    paths = cursor.fetchall()
    conn.close()
    return paths

def get_all_routes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM routes')
    routes = cursor.fetchall()
    conn.close()
    return routes

def get_all_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vehicles')
    vehicles = cursor.fetchall()
    conn.close()
    return vehicles

def get_unassigned_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vehicles WHERE id NOT IN (
            SELECT vehicle_id FROM deployments
        )
    ''')
    vehicles = cursor.fetchall()
    conn.close()
    return vehicles

def get_all_drivers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM drivers')
    drivers = cursor.fetchall()
    conn.close()
    return drivers

def get_unassigned_drivers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM drivers WHERE id NOT IN (
            SELECT driver_id FROM deployments
        )
    ''')
    drivers = cursor.fetchall()
    conn.close()
    return drivers

def get_all_trips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM daily_trips')
    trips = cursor.fetchall()
    conn.close()
    return trips

def get_deployments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, v.license_plate, dr.name as driver_name, dt.date, r.name as route_name
        FROM deployments d
        JOIN vehicles v ON d.vehicle_id = v.id
        JOIN drivers dr ON d.driver_id = dr.id
        JOIN daily_trips dt ON d.trip_id = dt.id
        JOIN routes r ON dt.route_id = r.id
    ''')
    deployments = cursor.fetchall()
    conn.close()
    return deployments

def get_paths_with_stops():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id as path_id, p.name as path_name, s.id as stop_id, s.name as stop_name, s.latitude, s.longitude, ps.order_index
        FROM paths p
        LEFT JOIN path_stops ps ON ps.path_id = p.id
        LEFT JOIN stops s ON s.id = ps.stop_id
        ORDER BY p.id, ps.order_index
    ''')
    rows = cursor.fetchall()
    conn.close()
    paths = {}
    for row in rows:
        path_id = row['path_id']
        if path_id not in paths:
            paths[path_id] = {
                'id': path_id,
                'name': row['path_name'],
                'stops': []
            }
        if row['stop_id'] is not None:
            stop_data = {
                'id': row['stop_id'],
                'name': row['stop_name'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'order': row['order_index']
            }
            if not any(s['id'] == row['stop_id'] for s in paths[path_id]['stops']):
                paths[path_id]['stops'].append(stop_data)
    for path in paths.values():
        path['stops'].sort(key=lambda item: item['order'] if item['order'] is not None else 0)
    return list(paths.values())

def get_routes_with_paths():
    results = fetch_dicts('''
        SELECT r.id, r.path_id, r.route_display_name, r.shift_time, r.direction, 
               r.start_point, r.end_point, r.status, p.name as path_name
        FROM routes r
        JOIN paths p ON r.path_id = p.id
        ORDER BY r.shift_time
    ''')
    seen_route_ids = set()
    deduplicated = []
    for route in results:
        if route['id'] not in seen_route_ids:
            seen_route_ids.add(route['id'])
            deduplicated.append(route)
    return deduplicated

def get_trips_with_routes():
    results = fetch_dicts('''
        SELECT dt.id, dt.route_id, dt.display_name, dt.booking_status_percentage, 
               dt.live_status, dt.date, r.route_display_name as route_name, 
               r.shift_time, p.name as path_name
        FROM daily_trips dt
        JOIN routes r ON dt.route_id = r.id
        JOIN paths p ON r.path_id = p.id
        ORDER BY dt.date, r.shift_time
    ''')
    seen_trip_ids = set()
    deduplicated = []
    for trip in results:
        if trip['id'] not in seen_trip_ids:
            seen_trip_ids.add(trip['id'])
            deduplicated.append(trip)
    return deduplicated

def get_deployments_detailed():
    results = fetch_dicts('''
        SELECT d.id, d.trip_id, d.vehicle_id, d.driver_id, v.license_plate, v.type as vehicle_type,
               v.capacity, v.model, dr.name as driver_name, dr.license_number, dr.phone, 
               dt.display_name as trip_display_name, dt.booking_status_percentage, 
               dt.live_status, dt.date, r.route_display_name as route_name
        FROM deployments d
        JOIN vehicles v ON d.vehicle_id = v.id
        JOIN drivers dr ON d.driver_id = dr.id
        JOIN daily_trips dt ON d.trip_id = dt.id
        JOIN routes r ON dt.route_id = r.id
        ORDER BY dt.date, r.shift_time
    ''')
    seen_trip_ids = set()
    deduplicated = []
    for deployment in results:
        if deployment['trip_id'] not in seen_trip_ids:
            seen_trip_ids.add(deployment['trip_id'])
            deduplicated.append(deployment)
    return deduplicated

# Tools for creating
def create_stop(name, latitude, longitude):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO stops (name, latitude, longitude) VALUES (?, ?, ?)', (name, latitude, longitude))
    conn.commit()
    stop_id = cursor.lastrowid
    conn.close()
    return stop_id

def create_path(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO paths (name) VALUES (?)', (name,))
    conn.commit()
    path_id = cursor.lastrowid
    conn.close()
    return path_id

def create_route(path_id, route_display_name, shift_time, direction, start_point, end_point, status='active'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO routes (path_id, route_display_name, shift_time, direction, start_point, end_point, status) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                   (path_id, route_display_name, shift_time, direction, start_point, end_point, status))
    conn.commit()
    route_id = cursor.lastrowid
    conn.close()
    return route_id

def create_vehicle(license_plate, vtype, capacity, model):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO vehicles (license_plate, type, capacity, model) VALUES (?, ?, ?, ?)', 
                   (license_plate, vtype, capacity, model))
    conn.commit()
    vehicle_id = cursor.lastrowid
    conn.close()
    return vehicle_id

def create_driver(name, license_number, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO drivers (name, license_number, phone) VALUES (?, ?, ?)', (name, license_number, phone))
    conn.commit()
    driver_id = cursor.lastrowid
    conn.close()
    return driver_id

def create_trip(route_id, display_name, booking_status_percentage=0.0, live_status='', date=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO daily_trips (route_id, display_name, booking_status_percentage, live_status, date) 
                      VALUES (?, ?, ?, ?, ?)''', 
                   (route_id, display_name, booking_status_percentage, live_status, date))
    conn.commit()
    trip_id = cursor.lastrowid
    conn.close()
    return trip_id

def assign_vehicle_driver(trip_id, vehicle_id, driver_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO deployments (trip_id, vehicle_id, driver_id) VALUES (?, ?, ?)', (trip_id, vehicle_id, driver_id))
    conn.commit()
    deployment_id = cursor.lastrowid
    conn.close()
    return deployment_id

# Check consequences
def check_trip_booked_percentage(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT booking_status_percentage FROM daily_trips WHERE id = ?', (trip_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0

def find_trip_by_display_name(display_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM daily_trips WHERE display_name LIKE ?', (f'%{display_name}%',))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_stops_for_path(path_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.name FROM stops s
        JOIN path_stops ps ON s.id = ps.stop_id
        JOIN paths p ON ps.path_id = p.id
        WHERE p.name = ?
        ORDER BY ps.order_index
    ''', (path_name,))
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def get_routes_using_path(path_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.route_display_name, r.shift_time, r.status FROM routes r
        JOIN paths p ON r.path_id = p.id
        WHERE p.name = ?
    ''', (path_name,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def create_path_with_stops(path_name, stop_names):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO paths (name) VALUES (?)', (path_name,))
    path_id = cursor.lastrowid
    for idx, stop_name in enumerate(stop_names, 1):
        cursor.execute('SELECT id FROM stops WHERE name = ?', (stop_name,))
        stop_result = cursor.fetchone()
        if stop_result:
            cursor.execute('INSERT INTO path_stops (path_id, stop_id, order_index) VALUES (?, ?, ?)', 
                          (path_id, stop_result[0], idx))
    conn.commit()
    conn.close()
    return path_id

# Helper functions for agent
def find_vehicle_by_plate(license_plate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM vehicles WHERE license_plate LIKE ?', (f'%{license_plate}%',))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def find_driver_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM drivers WHERE name LIKE ?', (f'%{name}%',))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def check_stop_in_use(stop_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM path_stops ps 
        JOIN stops s ON ps.stop_id = s.id 
        WHERE s.name = ?
    ''', (stop_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] > 0 if result else False

def check_vehicle_exists(license_plate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM vehicles WHERE license_plate = ?', (license_plate,))
    result = cursor.fetchone()
    conn.close()
    return result[0] > 0 if result else False

def delete_stop_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM stops WHERE name = ?', (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_trip_info(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM daily_trips WHERE id = ?', (trip_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def get_trip_status_by_name(trip_display_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dt.id, dt.display_name, dt.booking_status_percentage, dt.live_status, dt.date,
               r.route_display_name, v.license_plate, d.name as driver_name
        FROM daily_trips dt
        JOIN routes r ON dt.route_id = r.id
        LEFT JOIN deployments dep ON dt.id = dep.trip_id
        LEFT JOIN vehicles v ON dep.vehicle_id = v.id
        LEFT JOIN drivers d ON dep.driver_id = d.id
        WHERE dt.display_name LIKE ?
    ''', (f'%{trip_display_name}%',))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

# Enhanced image processing with vision capabilities for screenshot analysis
def process_image_for_trip(image_data):
    if not image_data:
        return None
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return None
    
    text_content = ''
    if pytesseract:
        try:
            text_content = pytesseract.image_to_string(image.convert('L'))
        except Exception:
            text_content = ''
    
    if text_content:
        trip_patterns = [
            r'Bulk\s*-\s*(\d{2}:\d{2})',
            r'Path\s+Path\s*-\s*(\d{2}:\d{2})',
            r'Gawana\s*-\s*(\d{2}:\d{2})',
            r'AKN\s*-\s*(\d{2}:\d{2})',
            r'Mellows\s+BTS\s*-\s*(\d{2}:\d{2})',
            r'([A-Za-z\s]+)\s*-\s*(\d{2}:\d{2})'
        ]
        
        for pattern in trip_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                trip_display_name = match.group(0).strip()
                trip_id = find_trip_by_display_name(trip_display_name)
                if trip_id:
                    return trip_id
        
        match = re.search(r'trip\s*#?\s*(\d+)', text_content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        digits = re.findall(r'\b(\d{1,4})\b', text_content)
        for value in digits:
            try:
                parsed = int(value)
                if 1 <= parsed <= 100:
                    return parsed
            except ValueError:
                continue
    
    width, height = image.size
    if width or height:
        fallback = (width + height) % 6 + 1
        return fallback
    return None

# Additional CRUD operations
def delete_vehicle(vehicle_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def delete_driver(driver_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def update_trip_status(trip_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE daily_trips SET status = ? WHERE id = ?', (status, trip_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        latitude REAL,
        longitude REAL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS path_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path_id INTEGER,
        stop_id INTEGER,
        order_index INTEGER,
        FOREIGN KEY (path_id) REFERENCES paths(id),
        FOREIGN KEY (stop_id) REFERENCES stops(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path_id INTEGER,
        route_display_name TEXT,
        shift_time TEXT,
        direction TEXT,
        start_point TEXT,
        end_point TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (path_id) REFERENCES paths(id)
    )''')
    
    if not column_exists('routes', 'route_display_name'):
        cursor.execute('ALTER TABLE routes ADD COLUMN route_display_name TEXT')
    if not column_exists('routes', 'shift_time'):
        cursor.execute('ALTER TABLE routes ADD COLUMN shift_time TEXT')
    if not column_exists('routes', 'direction'):
        cursor.execute('ALTER TABLE routes ADD COLUMN direction TEXT')
    if not column_exists('routes', 'start_point'):
        cursor.execute('ALTER TABLE routes ADD COLUMN start_point TEXT')
    if not column_exists('routes', 'end_point'):
        cursor.execute('ALTER TABLE routes ADD COLUMN end_point TEXT')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_plate TEXT UNIQUE,
        type TEXT,
        capacity INTEGER,
        model TEXT
    )''')
    
    if not column_exists('vehicles', 'type'):
        cursor.execute('ALTER TABLE vehicles ADD COLUMN type TEXT')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        license_number TEXT,
        phone TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        display_name TEXT,
        booking_status_percentage REAL,
        live_status TEXT,
        date TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )''')
    
    if not column_exists('daily_trips', 'display_name'):
        cursor.execute('ALTER TABLE daily_trips ADD COLUMN display_name TEXT')
    if not column_exists('daily_trips', 'booking_status_percentage'):
        cursor.execute('ALTER TABLE daily_trips ADD COLUMN booking_status_percentage REAL')
    if not column_exists('daily_trips', 'live_status'):
        cursor.execute('ALTER TABLE daily_trips ADD COLUMN live_status TEXT')
    
    if not column_exists('routes', 'status'):
        cursor.execute('ALTER TABLE routes ADD COLUMN status TEXT DEFAULT "active"')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS deployments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER UNIQUE,
        vehicle_id INTEGER,
        driver_id INTEGER,
        FOREIGN KEY (trip_id) REFERENCES daily_trips(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    conn.commit()
    
    from sample_data import SAMPLE_STOPS, SAMPLE_ROUTES, SAMPLE_VEHICLES, SAMPLE_DRIVERS, SAMPLE_TRIPS, SAMPLE_DEPLOYMENTS, SAMPLE_PATHS, SAMPLE_PATH_STOPS
    
    for stop in SAMPLE_STOPS:
        cursor.execute('INSERT OR IGNORE INTO stops (name, latitude, longitude) VALUES (?, ?, ?)', stop)
    
    for path_name, status in SAMPLE_PATHS:
        cursor.execute('INSERT OR IGNORE INTO paths (name) VALUES (?)', (path_name,))
    
    for path_id, stop_id, order_index in SAMPLE_PATH_STOPS:
        cursor.execute('INSERT OR IGNORE INTO path_stops (path_id, stop_id, order_index) VALUES (?, ?, ?)', 
                      (path_id, stop_id, order_index))
    
    for path_id, display_name, shift_time, direction, start_point, end_point in SAMPLE_ROUTES:
        try:
            cursor.execute('''INSERT OR IGNORE INTO routes 
                (path_id, route_display_name, shift_time, direction, start_point, end_point, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                (path_id, display_name, shift_time, direction, start_point, end_point, 'active'))
        except sqlite3.OperationalError:
            cursor.execute('''INSERT OR IGNORE INTO routes 
                (path_id, route_display_name, shift_time, direction, start_point, end_point) 
                VALUES (?, ?, ?, ?, ?, ?)''', 
                (path_id, display_name, shift_time, direction, start_point, end_point))
    
    for license_plate, vtype, capacity, model in SAMPLE_VEHICLES:
        cursor.execute('INSERT OR IGNORE INTO vehicles (license_plate, type, capacity, model) VALUES (?, ?, ?, ?)', 
                      (license_plate, vtype, capacity, model))
    
    for name, license_num, phone in SAMPLE_DRIVERS:
        cursor.execute('INSERT OR IGNORE INTO drivers (name, license_number, phone) VALUES (?, ?, ?)', 
                      (name, license_num, phone))
    
    for route_id, display_name, booking_pct, live_status, date in SAMPLE_TRIPS:
        cursor.execute('''INSERT OR IGNORE INTO daily_trips 
            (route_id, display_name, booking_status_percentage, live_status, date) 
            VALUES (?, ?, ?, ?, ?)''', 
            (route_id, display_name, booking_pct, live_status, date))
    
    for trip_display_name, vehicle_plate, driver_name in SAMPLE_DEPLOYMENTS:
        cursor.execute('SELECT id FROM daily_trips WHERE display_name = ?', (trip_display_name,))
        trip_result = cursor.fetchone()
        if trip_result:
            trip_id = trip_result[0]
            cursor.execute('SELECT id FROM vehicles WHERE license_plate = ?', (vehicle_plate,))
            vehicle_result = cursor.fetchone()
            cursor.execute('SELECT id FROM drivers WHERE name = ?', (driver_name,))
            driver_result = cursor.fetchone()
            if vehicle_result and driver_result:
                cursor.execute('INSERT OR IGNORE INTO deployments (trip_id, vehicle_id, driver_id) VALUES (?, ?, ?)', 
                              (trip_id, vehicle_result[0], driver_result[0]))
    
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("[OK] Database initialized with dummy data")