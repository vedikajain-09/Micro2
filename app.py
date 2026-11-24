from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date, timedelta
from functools import wraps
import os
from db import init_db, seed_database, get_db, check_password, hash_password

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hostel-secret-key-2026'

init_db()
seed_database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def warden_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'warden':
            flash('Access denied. Warden only.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user and check_password(user['password_hash'], password):
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']
                return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    with get_db() as conn:
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        pending_fees = conn.execute("SELECT COUNT(*) FROM fees WHERE status IN ('Pending', 'Overdue')").fetchone()[0]
        open_complaints = conn.execute("SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'").fetchone()[0]

        today = date.today().isoformat()
        total_att = conn.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,)).fetchone()[0]
        present_att = conn.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'Present'", (today,)).fetchone()[0]
        attendance_pct = round((present_att / total_att * 100) if total_att > 0 else 0, 1)

        # Chart data
        last_7_days = []
        attendance_data = []
        for i in range(6, -1, -1):
            d = (date.today() - timedelta(days=i)).isoformat()
            last_7_days.append((date.today() - timedelta(days=i)).strftime('%a'))
            total = conn.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (d,)).fetchone()[0]
            present = conn.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'Present'", (d,)).fetchone()[0]
            pct = round((present / total * 100) if total > 0 else 0, 1)
            attendance_data.append(pct)

        fee_collected = conn.execute("SELECT COUNT(*) FROM fees WHERE status = 'Paid'").fetchone()[0]
        fee_pending = conn.execute("SELECT COUNT(*) FROM fees WHERE status IN ('Pending', 'Overdue')").fetchone()[0]

    return render_template('dashboard.html',
                         total_students=total_students,
                         pending_fees=pending_fees,
                         open_complaints=open_complaints,
                         attendance_pct=attendance_pct,
                         last_7_days=last_7_days,
                         attendance_data=attendance_data,
                         fee_collected=fee_collected,
                         fee_pending=fee_pending)

@app.route('/students')
@login_required
def students():
    search = request.args.get('search', '')
    block_filter = request.args.get('block', '')
    query = "SELECT * FROM users WHERE role='student'"
    params = []
    if search:
        query += " AND (name LIKE ? OR roll_no LIKE ? OR room_no LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    if block_filter:
        query += " AND block = ?"
        params.append(block_filter)
    query += " ORDER BY name"
    with get_db() as conn:
        students_list = conn.execute(query, params).fetchall()
        blocks = [row[0] for row in conn.execute("SELECT DISTINCT block FROM users WHERE role='student' AND block IS NOT NULL").fetchall()]
    return render_template('students.html', students=students_list, blocks=blocks, search=search, block_filter=block_filter)

@app.route('/students/add', methods=['POST'])
@login_required
@warden_required
def add_student():
    data = request.form
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (data['username'],)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'Username already exists'})
        conn.execute('''INSERT INTO users (username, password_hash, role, name, roll_no, room_no, block, phone, guardian_contact, blood_group)
                        VALUES (?, ?, 'student', ?, ?, ?, ?, ?, ?, ?)''',
                     (data['username'], hash_password(data.get('password', 'pass123')),
                      data['name'], data['roll_no'], data['room_no'], data['block'],
                      data['phone'], data['guardian'], data['blood']))
    return jsonify({'success': True, 'message': 'Student added successfully'})

@app.route('/students/edit/<int:id>', methods=['POST'])
@login_required
@warden_required
def edit_student(id):
    data = request.form
    with get_db() as conn:
        conn.execute('''UPDATE users SET name=?, roll_no=?, room_no=?, block=?, phone=?, guardian_contact=?, blood_group=?
                        WHERE id=?''',
                     (data['name'], data['roll_no'], data['room_no'], data['block'],
                      data['phone'], data['guardian'], data['blood'], id))
    return jsonify({'success': True, 'message': 'Student updated successfully'})

@app.route('/students/delete/<int:id>', methods=['POST'])
@login_required
@warden_required
def delete_student(id):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (id,))
    return jsonify({'success': True, 'message': 'Student deleted successfully'})

@app.route('/announcements')
@login_required
def announcements():
    with get_db() as conn:
        anns = conn.execute("SELECT * FROM announcements ORDER BY created_at DESC").fetchall()
        read_ids = []
        if session.get('role') == 'student':
            reads = conn.execute("SELECT announcement_id FROM announcement_reads WHERE user_id = ?", (session['user_id'],)).fetchall()
            read_ids = [r[0] for r in reads]
    return render_template('announcements.html', announcements=anns, read_ids=read_ids)

@app.route('/announcements/add', methods=['POST'])
@login_required
@warden_required
def add_announcement():
    data = request.form
    with get_db() as conn:
        conn.execute("INSERT INTO announcements (title, content, priority) VALUES (?, ?, ?)",
                     (data['title'], data['content'], data['priority']))
    return jsonify({'success': True, 'message': 'Announcement published'})

@app.route('/announcements/delete/<int:id>', methods=['POST'])
@login_required
@warden_required
def delete_announcement(id):
    with get_db() as conn:
        conn.execute("DELETE FROM announcements WHERE id=?", (id,))
    return jsonify({'success': True, 'message': 'Announcement deleted'})

@app.route('/announcements/read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    with get_db() as conn:
        try:
            conn.execute("INSERT INTO announcement_reads (user_id, announcement_id) VALUES (?, ?)",
                         (session['user_id'], id))
        except:
            pass
    return jsonify({'success': True})

@app.route('/mess')
@login_required
def mess():
    with get_db() as conn:
        menus = conn.execute("SELECT * FROM mess_menu").fetchall()
    menu_dict = {}
    for m in menus:
        if m['day'] not in menu_dict:
            menu_dict[m['day']] = {}
        menu_dict[m['day']][m['meal']] = {'items': m['items'], 'type': m['type'], 'id': m['id']}
    today_name = date.today().strftime('%A')
    return render_template('mess.html', menu=menu_dict, today=today_name)

@app.route('/mess/update', methods=['POST'])
@login_required
@warden_required
def update_mess():
    data = request.json
    with get_db() as conn:
        conn.execute("UPDATE mess_menu SET items=?, type=? WHERE id=?",
                     (data['items'], data['type'], data['id']))
    return jsonify({'success': True, 'message': 'Menu updated'})

@app.route('/fees')
@login_required
def fees():
    with get_db() as conn:
        if session.get('role') == 'student':
            fees_list = conn.execute('''SELECT f.*, u.name FROM fees f
                                        JOIN users u ON f.student_id = u.id
                                        WHERE f.student_id = ?''', (session['user_id'],)).fetchall()
        else:
            fees_list = conn.execute('''SELECT f.*, u.name FROM fees f
                                        JOIN users u ON f.student_id = u.id
                                        ORDER BY u.name''').fetchall()
    return render_template('fees.html', fees=fees_list)

@app.route('/fees/pay/<int:id>', methods=['POST'])
@login_required
def pay_fee(id):
    with get_db() as conn:
        fee = conn.execute("SELECT * FROM fees WHERE id=?", (id,)).fetchone()
        if not fee:
            return jsonify({'success': False, 'message': 'Fee not found'})
        if session.get('role') == 'student' and fee['student_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        conn.execute("UPDATE fees SET status='Paid' WHERE id=?", (id,))
    return jsonify({'success': True, 'message': 'Payment successful! Receipt generated.'})

@app.route('/complaints')
@login_required
def complaints():
    with get_db() as conn:
        if session.get('role') == 'student':
            comps = conn.execute('''SELECT c.*, u.name, u.roll_no FROM complaints c
                                    JOIN users u ON c.student_id = u.id
                                    WHERE c.student_id = ? ORDER BY c.created_at DESC''',
                                 (session['user_id'],)).fetchall()
        else:
            comps = conn.execute('''SELECT c.*, u.name, u.roll_no FROM complaints c
                                    JOIN users u ON c.student_id = u.id
                                    ORDER BY c.created_at DESC''').fetchall()
    return render_template('complaints.html', complaints=comps)

@app.route('/complaints/add', methods=['POST'])
@login_required
def add_complaint():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Students only'})
    data = request.form
    with get_db() as conn:
        student = conn.execute("SELECT room_no FROM users WHERE id=?", (session['user_id'],)).fetchone()
        conn.execute('''INSERT INTO complaints (student_id, category, description, room_no)
                        VALUES (?, ?, ?, ?)''',
                     (session['user_id'], data['category'], data['description'], student['room_no'] if student else ''))
    return jsonify({'success': True, 'message': 'Complaint submitted successfully'})

@app.route('/complaints/update/<int:id>', methods=['POST'])
@login_required
@warden_required
def update_complaint(id):
    new_status = request.json.get('status')
    if new_status in ['Pending', 'In Progress', 'Resolved']:
        with get_db() as conn:
            conn.execute("UPDATE complaints SET status=? WHERE id=?", (new_status, id))
        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    return jsonify({'success': False})

@app.route('/attendance')
@login_required
@warden_required
def attendance():
    selected_date = request.args.get('date', date.today().isoformat())
    with get_db() as conn:
        students_list = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall()
        att_records = {row['student_id']: row['status'] for row in
                       conn.execute("SELECT student_id, status FROM attendance WHERE date=?", (selected_date,)).fetchall()}
    return render_template('attendance.html', students=students_list, att_records=att_records, selected_date=selected_date)

@app.route('/attendance/save', methods=['POST'])
@login_required
@warden_required
def save_attendance():
    data = request.json
    att_date = data['date']
    with get_db() as conn:
        for student_id, status in data['attendance'].items():
            conn.execute('''INSERT INTO attendance (student_id, date, status)
                            VALUES (?, ?, ?)
                            ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status''',
                         (int(student_id), att_date, status))
    return jsonify({'success': True, 'message': 'Attendance saved successfully!'})

@app.route('/attendance/mark_all', methods=['POST'])
@login_required
@warden_required
def mark_all_present():
    data = request.json
    att_date = data['date']
    with get_db() as conn:
        students = conn.execute("SELECT id FROM users WHERE role='student'").fetchall()
        for s in students:
            conn.execute('''INSERT INTO attendance (student_id, date, status)
                            VALUES (?, ?, 'Present')
                            ON CONFLICT(student_id, date) DO UPDATE SET status='Present' ''',
                         (s['id'], att_date))
    return jsonify({'success': True, 'message': 'All marked present!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
