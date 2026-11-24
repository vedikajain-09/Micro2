import sqlite3
import os
from datetime import datetime, date, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'hostel.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        # Users
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE,
            room_no TEXT,
            block TEXT,
            phone TEXT,
            guardian_contact TEXT,
            blood_group TEXT
        )''')
        # Announcements
        c.execute('''CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'General',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        # Announcement reads
        c.execute('''CREATE TABLE IF NOT EXISTS announcement_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            announcement_id INTEGER NOT NULL,
            read_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, announcement_id)
        )''')
        # Mess menu
        c.execute('''CREATE TABLE IF NOT EXISTS mess_menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            meal TEXT NOT NULL,
            items TEXT NOT NULL,
            type TEXT DEFAULT 'Veg'
        )''')
        # Fees
        c.execute('''CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            fee_type TEXT DEFAULT 'Hostel'
        )''')
        # Complaints
        c.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            room_no TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        # Attendance
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            UNIQUE(student_id, date)
        )''')

def hash_password(password):
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)

def check_password(hash_val, password):
    from werkzeug.security import check_password_hash
    return check_password_hash(hash_val, password)

def seed_database():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] > 0:
            # Still refresh mess menu with new Indian dishes
            c.execute("DELETE FROM mess_menu")
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            indian_menu = {
                'Monday': {
                    'Breakfast': ('Poha, Sev, Lemon, Tea, Banana', 'Veg'),
                    'Lunch': ('Dal Tadka, Jeera Rice, Aloo Gobi, Roti, Salad, Curd', 'Veg'),
                    'Snacks': ('Samosa, Chutney, Tea', 'Veg'),
                    'Dinner': ('Paneer Butter Masala, Jeera Rice, Roti, Dal, Salad', 'Veg'),
                },
                'Tuesday': {
                    'Breakfast': ('Upma, Coconut Chutney, Tea, Boiled Egg', 'Veg'),
                    'Lunch': ('Rajma, Rice, Mix Veg, Roti, Salad, Pickle', 'Veg'),
                    'Snacks': ('Bread Pakora, Green Chutney, Tea', 'Veg'),
                    'Dinner': ('Chicken Curry, Rice, Roti, Dal Fry, Salad', 'Non-Veg'),
                },
                'Wednesday': {
                    'Breakfast': ('Idli, Sambar, Coconut Chutney, Tea', 'Veg'),
                    'Lunch': ('Chole, Bhature, Rice, Salad, Boondi Raita', 'Veg'),
                    'Snacks': ('Aloo Tikki, Chutney, Tea', 'Veg'),
                    'Dinner': ('Palak Paneer, Jeera Rice, Roti, Dal, Salad', 'Veg'),
                },
                'Thursday': {
                    'Breakfast': ('Paratha (Aloo/Gobi), Curd, Pickle, Tea', 'Veg'),
                    'Lunch': ('Kadhi Pakora, Rice, Aloo Matar, Roti, Salad', 'Veg'),
                    'Snacks': ('Vada Pav, Chutney, Tea', 'Veg'),
                    'Dinner': ('Egg Curry, Rice, Roti, Dal, Salad', 'Non-Veg'),
                },
                'Friday': {
                    'Breakfast': ('Puri Bhaji, Halwa, Tea', 'Veg'),
                    'Lunch': ('Veg Biryani, Raita, Salad, Papad', 'Veg'),
                    'Snacks': ('Pakora (Onion/Mix), Chutney, Tea', 'Veg'),
                    'Dinner': ('Butter Chicken, Naan, Jeera Rice, Dal Makhani', 'Non-Veg'),
                },
                'Saturday': {
                    'Breakfast': ('Dosa, Sambar, Chutney, Tea', 'Veg'),
                    'Lunch': ('Dal Makhani, Rice, Shahi Paneer, Roti, Salad', 'Veg'),
                    'Snacks': ('Momos, Chutney, Tea', 'Veg'),
                    'Dinner': ('Fish Curry, Rice, Roti, Dal, Salad', 'Non-Veg'),
                },
                'Sunday': {
                    'Breakfast': ('Chole Bhature, Pickle, Tea, Sweet', 'Veg'),
                    'Lunch': ('Special Thali: Dal, Sabzi, Rice, Roti, Raita, Sweet', 'Veg'),
                    'Snacks': ('Jalebi, Fafda, Tea', 'Veg'),
                    'Dinner': ('Mutton Curry, Roti, Rice, Dal, Salad', 'Non-Veg'),
                },
            }
            for day in days:
                for meal in ['Breakfast', 'Lunch', 'Snacks', 'Dinner']:
                    items, mtype = indian_menu[day][meal]
                    c.execute('INSERT INTO mess_menu (day, meal, items, type) VALUES (?, ?, ?, ?)',
                              (day, meal, items, mtype))
            return

        # Warden
        c.execute('''INSERT INTO users (username, password_hash, role, name)
                     VALUES (?, ?, ?, ?)''',
                  ('warden', hash_password('admin123'), 'warden', 'Dr. Anil Kumar'))

        # Students
        students = [
            ('student1', 'Rahul Sharma', 'BTAI001', '101', 'A', '9876543210', '9876543211', 'O+'),
            ('student2', 'Priya Patel', 'BTAI002', '102', 'A', '9876543220', '9876543221', 'A+'),
            ('student3', 'Amit Singh', 'BTAI003', '201', 'B', '9876543230', '9876543231', 'B+'),
            ('student4', 'Sneha Gupta', 'BTAI004', '202', 'B', '9876543240', '9876543241', 'AB+'),
            ('student5', 'Vikram Rao', 'BTAI005', '301', 'C', '9876543250', '9876543251', 'O-'),
            ('student6', 'Anjali Mehta', 'BTAI006', '103', 'A', '9876543260', '9876543261', 'A-'),
            ('student7', 'Rohan Desai', 'BTAI007', '203', 'B', '9876543270', '9876543271', 'B-'),
            ('student8', 'Kavita Joshi', 'BTAI008', '302', 'C', '9876543280', '9876543281', 'O+'),
        ]
        student_ids = []
        for s in students:
            c.execute('''INSERT INTO users (username, password_hash, role, name, roll_no, room_no, block, phone, guardian_contact, blood_group)
                         VALUES (?, ?, 'student', ?, ?, ?, ?, ?, ?, ?)''',
                      (s[0], hash_password('pass123'), s[1], s[2], s[3], s[4], s[5], s[6], s[7]))
            student_ids.append(c.lastrowid)

        # Announcements
        announcements = [
            ('Hostel Meeting Tomorrow', 'Mandatory meeting for all students at 5 PM in the common hall regarding new rules.', 'Urgent'),
            ('Mess Menu Update', 'Special dinner this Friday for Diwali celebration. Non-veg options available.', 'Event'),
            ('Fee Payment Reminder', 'Last date for hostel fee payment is 30th November. Late fees will apply.', 'General'),
            ('Wi-Fi Maintenance', 'Wi-Fi will be down from 2 AM to 4 AM tonight for upgrades.', 'General'),
            ('Sports Day', 'Annual sports day on Sunday. Register with your block representative.', 'Event'),
        ]
        for a in announcements:
            c.execute('INSERT INTO announcements (title, content, priority) VALUES (?, ?, ?)', a)

        # Mess Menu - Varied Indian dishes
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        indian_menu = {
            'Monday': {
                'Breakfast': ('Poha, Sev, Lemon, Tea, Banana', 'Veg'),
                'Lunch': ('Dal Tadka, Jeera Rice, Aloo Gobi, Roti, Salad, Curd', 'Veg'),
                'Snacks': ('Samosa, Chutney, Tea', 'Veg'),
                'Dinner': ('Paneer Butter Masala, Jeera Rice, Roti, Dal, Salad', 'Veg'),
            },
            'Tuesday': {
                'Breakfast': ('Upma, Coconut Chutney, Tea, Boiled Egg', 'Veg'),
                'Lunch': ('Rajma, Rice, Mix Veg, Roti, Salad, Pickle', 'Veg'),
                'Snacks': ('Bread Pakora, Green Chutney, Tea', 'Veg'),
                'Dinner': ('Chicken Curry, Rice, Roti, Dal Fry, Salad', 'Non-Veg'),
            },
            'Wednesday': {
                'Breakfast': ('Idli, Sambar, Coconut Chutney, Tea', 'Veg'),
                'Lunch': ('Chole, Bhature, Rice, Salad, Boondi Raita', 'Veg'),
                'Snacks': ('Aloo Tikki, Chutney, Tea', 'Veg'),
                'Dinner': ('Palak Paneer, Jeera Rice, Roti, Dal, Salad', 'Veg'),
            },
            'Thursday': {
                'Breakfast': ('Paratha (Aloo/Gobi), Curd, Pickle, Tea', 'Veg'),
                'Lunch': ('Kadhi Pakora, Rice, Aloo Matar, Roti, Salad', 'Veg'),
                'Snacks': ('Vada Pav, Chutney, Tea', 'Veg'),
                'Dinner': ('Egg Curry, Rice, Roti, Dal, Salad', 'Non-Veg'),
            },
            'Friday': {
                'Breakfast': ('Puri Bhaji, Halwa, Tea', 'Veg'),
                'Lunch': ('Veg Biryani, Raita, Salad, Papad', 'Veg'),
                'Snacks': ('Pakora (Onion/Mix), Chutney, Tea', 'Veg'),
                'Dinner': ('Butter Chicken, Naan, Jeera Rice, Dal Makhani', 'Non-Veg'),
            },
            'Saturday': {
                'Breakfast': ('Dosa, Sambar, Chutney, Tea', 'Veg'),
                'Lunch': ('Dal Makhani, Rice, Shahi Paneer, Roti, Salad', 'Veg'),
                'Snacks': ('Momos, Chutney, Tea', 'Veg'),
                'Dinner': ('Fish Curry, Rice, Roti, Dal, Salad', 'Non-Veg'),
            },
            'Sunday': {
                'Breakfast': ('Chole Bhature, Pickle, Tea, Sweet', 'Veg'),
                'Lunch': ('Special Thali: Dal, Sabzi, Rice, Roti, Raita, Sweet', 'Veg'),
                'Snacks': ('Jalebi, Fafda, Tea', 'Veg'),
                'Dinner': ('Mutton Curry, Roti, Rice, Dal, Salad', 'Non-Veg'),
            },
        }
        for day in days:
            for meal in ['Breakfast', 'Lunch', 'Snacks', 'Dinner']:
                items, mtype = indian_menu[day][meal]
                c.execute('INSERT INTO mess_menu (day, meal, items, type) VALUES (?, ?, ?, ?)',
                          (day, meal, items, mtype))

        # Fees
        today = date.today()
        for i, sid in enumerate(student_ids):
            status = 'Paid' if i % 3 == 0 else 'Pending'
            if i == 2:
                status = 'Overdue'
            c.execute('INSERT INTO fees (student_id, amount, due_date, status, fee_type) VALUES (?, ?, ?, ?, ?)',
                      (sid, 15000.0, (today + timedelta(days=15 - i*2)).isoformat(), status, 'Hostel'))
            mess_status = 'Paid' if i % 2 == 0 else 'Pending'
            c.execute('INSERT INTO fees (student_id, amount, due_date, status, fee_type) VALUES (?, ?, ?, ?, ?)',
                      (sid, 3000.0, (today + timedelta(days=10)).isoformat(), mess_status, 'Mess'))

        # Complaints
        complaints = [
            (student_ids[0], 'Electrical', 'Light in room not working', '101', 'Pending'),
            (student_ids[1], 'Plumbing', 'Tap leaking in bathroom', '102', 'In Progress'),
            (student_ids[2], 'Wi-Fi', 'Slow internet speed', '201', 'Resolved'),
            (student_ids[3], 'Cleaning', 'Corridor needs cleaning', '202', 'Pending'),
            (student_ids[4], 'Mess', 'Food quality issue yesterday', '301', 'In Progress'),
        ]
        for comp in complaints:
            c.execute('''INSERT INTO complaints (student_id, category, description, room_no, status)
                         VALUES (?, ?, ?, ?, ?)''', comp)

        # Attendance (last 5 days)
        for days_ago in range(5):
            att_date = (today - timedelta(days=days_ago)).isoformat()
            for i, sid in enumerate(student_ids):
                status = 'Present'
                if i == 3 and days_ago == 0:
                    status = 'On Leave'
                elif i == 5 and days_ago == 1:
                    status = 'Absent'
                c.execute('INSERT OR IGNORE INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                          (sid, att_date, status))

        print("Database seeded successfully!")
