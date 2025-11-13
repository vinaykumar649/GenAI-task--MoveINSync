SAMPLE_PATHS = [
    ('South Bangalore - MG Road to BTM Layout', 'Active'),
    ('Central Bangalore - Indiranagar to Koramangala', 'Active')
]

SAMPLE_STOPS = [
    ('MG Road Station', 12.9716, 77.6412),
    ('BTM Layout Terminal', 12.9176, 77.6144),
    ('Indiranagar Junction', 13.0352, 77.6412),
    ('Koramangala Center', 12.9352, 77.6245)
]

SAMPLE_PATH_STOPS = [
    (1, 1, 0),
    (1, 2, 1),
    (2, 3, 0),
    (2, 4, 1)
]

SAMPLE_ROUTES = [
    (1, 'South Bangalore - Morning 08:00', '08:00', 'South', 'MG Road Station', 'BTM Layout Terminal'),
    (1, 'South Bangalore - Evening 18:00', '18:00', 'South', 'MG Road Station', 'BTM Layout Terminal'),
    (2, 'Central Bangalore - Morning 09:00', '09:00', 'Central', 'Indiranagar Junction', 'Koramangala Center'),
    (2, 'Central Bangalore - Evening 17:00', '17:00', 'Central', 'Indiranagar Junction', 'Koramangala Center')
]

SAMPLE_VEHICLES = [
    ('KA-01-AB-1234', 'Bus', 52, 'Volvo AC Bus'),
    ('KA-01-CD-5678', 'Bus', 45, 'Tata Bus'),
    ('KA-01-EF-9012', 'Cab', 4, 'Swift Sedan'),
    ('KA-01-GH-3456', 'Bus', 50, 'Ashok Leyland'),
    ('KA-01-IJ-7890', 'Cab', 6, 'Toyota Innova')
]

SAMPLE_DRIVERS = [
    ('Amit Kumar', 'DL123456', '9876543210'),
    ('Rajesh Singh', 'DL789012', '9876543211'),
    ('Priya Sharma', 'DL345678', '9876543212'),
    ('Suresh Patel', 'DL456789', '9876543213'),
    ('Deepak Verma', 'DL654321', '9876543214')
]

SAMPLE_TRIPS = [
    (1, 'South Bangalore - Morning 08:00', 0.0, 'Scheduled', '2025-11-15'),
    (1, 'South Bangalore - Evening 18:00', 0.0, 'Scheduled', '2025-11-15'),
    (2, 'Central Bangalore - Morning 09:00', 0.0, 'Scheduled', '2025-11-15'),
    (2, 'Central Bangalore - Evening 17:00', 0.0, 'Scheduled', '2025-11-15')
]

SAMPLE_DEPLOYMENTS = [
    ('South Bangalore - Morning 08:00', 'KA-01-AB-1234', 'Amit Kumar'),
    ('South Bangalore - Evening 18:00', 'KA-01-CD-5678', 'Rajesh Singh'),
    ('Central Bangalore - Morning 09:00', 'KA-01-EF-9012', 'Priya Sharma'),
    ('Central Bangalore - Evening 17:00', 'KA-01-GH-3456', 'Suresh Patel')
]
