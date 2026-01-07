from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = 'facilibook_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'      # Check your username
app.config['MYSQL_PASSWORD'] = ''      # Check your password
app.config['MYSQL_DB'] = 'facilibook'

mysql = MySQL(app)

# --- HELPER FUNCTIONS ---
def get_facilities(only_active=False):
    """Fetches facilities. If only_active=True, hides maintenance ones."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if only_active:
        cursor.execute("SELECT * FROM facilities WHERE status = 'active'")
    else:
        cursor.execute("SELECT * FROM facilities")
    return cursor.fetchall()

def get_user_bookings(user_id):
    """Fetches history + feedback status for a user."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = """
        SELECT 
            b.id, b.start_time, b.end_time, b.purpose, b.status,
            b.rejection_reason, 
            f.name as facility_name,
            u.name as faculty_name,
            admin_user.name as approver_name,
            fb.id as feedback_id
        FROM bookings b
        JOIN facilities f ON b.facility_id = f.id
        JOIN users u ON b.user_id = u.id
        LEFT JOIN users admin_user ON b.approved_by = admin_user.id
        LEFT JOIN feedback fb ON b.id = fb.booking_id
        WHERE b.user_id = %s
        ORDER BY b.start_time DESC
    """
    cursor.execute(query, (user_id,))
    return cursor.fetchall()

# --- AUTH ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            # CHECK IF ACCOUNT IS ACTIVE
            if account['is_active'] == 0:
                return render_template('login.html', error="Account deactivated. Contact Admin.")
        if account and account['password'] == password:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']
            session['name'] = account['name']
            return redirect(url_for('admin_dashboard') if account['role'] == 'admin' else url_for('my_bookings'))
        else:
            return render_template('login.html', error="Incorrect Username or Password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if username exists
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return render_template('register.html', error="Username already exists!")
            
        # Insert new user
        cursor.execute('INSERT INTO users (name, username, password, role) VALUES (%s, %s, %s, "faculty")', (name, username, password))
        mysql.connection.commit()
        
        # --- NEW: Flash the success message ---
        flash('Account created successfully! You can now log in.', 'success')
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch the 5 most recent pending requests
        query = """
            SELECT b.id, b.start_time, b.end_time, b.purpose, 
                   f.name as facility_name, u.name as faculty_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN users u ON b.user_id = u.id
            WHERE b.status = 'pending'
            ORDER BY b.start_time ASC
            LIMIT 5
        """
        cursor.execute(query)
        pending_bookings = cursor.fetchall()
        
        return render_template('admin_dashboard.html', pending_bookings=pending_bookings)
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            # Debugging: Print what the server receives (Check your terminal!)
            print("Received Form Data:", request.form)

            action = request.form.get('action')
            user_id = request.form.get('user_id')
            
            # UNIFIED EDIT LOGIC
            if action == 'edit':
                name = request.form['name']
                username = request.form['username']
                password = request.form.get('password') # Optional field
                
                # Check if username is taken by someone else
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, user_id))
                if cursor.fetchone():
                    flash('Error: That username is already taken!', 'error')
                else:
                    if password and password.strip():
                        # Update Name, Username AND Password
                        cursor.execute('UPDATE users SET name=%s, username=%s, password=%s WHERE id=%s', 
                                     (name, username, password, user_id))
                        flash('User details and password updated!', 'success')
                    else:
                        # Update ONLY Name and Username
                        cursor.execute('UPDATE users SET name=%s, username=%s WHERE id=%s', 
                                     (name, username, user_id))
                        flash('User details updated successfully!', 'success')
                
            mysql.connection.commit()
            return redirect(url_for('manage_users'))

        # Fetch all Faculty users
        cursor.execute("SELECT * FROM users WHERE role != 'admin'")
        users = cursor.fetchall()
        return render_template('manage_users.html', users=users)
        
    return redirect(url_for('login'))


@app.route('/delete_user/<int:id>')
def delete_user(id):
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE users SET is_active = 0 WHERE id = %s', (id,))
        mysql.connection.commit()
        flash('User account deactivated. History preserved.', 'warning')
        return redirect(url_for('manage_users'))
    return redirect(url_for('login'))

@app.route('/api/stats')
def api_stats():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get optional filter from URL (e.g., ?month=2026-02)
        filter_month = request.args.get('month') 

        # 1. WEEKLY STATS (Always "This Week" for comparison)
        cursor.execute("""
            SELECT f.name, COUNT(b.id) as count 
            FROM facilities f 
            LEFT JOIN bookings b ON f.id = b.facility_id 
            AND YEARWEEK(b.start_time, 1) = YEARWEEK(CURDATE(), 1)
            GROUP BY f.id
        """)
        weekly_stats = cursor.fetchall()

        # 2. MONTHLY STATS (Dynamic: Current Month OR Selected History)
        if filter_month:
            # If user picked a date, use that (Format: YYYY-MM)
            cursor.execute("""
                SELECT f.name, COUNT(b.id) as count 
                FROM facilities f 
                LEFT JOIN bookings b ON f.id = b.facility_id 
                AND DATE_FORMAT(b.start_time, '%%Y-%%m') = %s
                GROUP BY f.id
            """, (filter_month,))
        else:
            # Default to Current Month
            cursor.execute("""
                SELECT f.name, COUNT(b.id) as count 
                FROM facilities f 
                LEFT JOIN bookings b ON f.id = b.facility_id 
                AND DATE_FORMAT(b.start_time, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')
                GROUP BY f.id
            """)
        monthly_stats = cursor.fetchall()

        # 3. Status Distribution (Unchanged)
        cursor.execute("SELECT status, COUNT(*) as count FROM bookings GROUP BY status ORDER BY status")
        status_stats = cursor.fetchall()

        # 4. Feedback Ratings (Unchanged)
        cursor.execute("""
            SELECT f.name, AVG(fb.rating) as avg_rating
            FROM facilities f
            JOIN bookings b ON f.id = b.facility_id
            JOIN feedback fb ON b.id = fb.booking_id
            GROUP BY f.id
            ORDER BY avg_rating DESC
        """)
        feedback_stats = cursor.fetchall()
        for item in feedback_stats:
            item['avg_rating'] = round(item['avg_rating'], 1) if item['avg_rating'] else 0

        return jsonify({
            'weekly': weekly_stats,
            'monthly': monthly_stats,
            'statuses': status_stats,
            'feedbacks': feedback_stats
        })
    return jsonify({})

@app.route('/admin/facilities', methods=['GET', 'POST'])
def manage_facilities():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST':
            name, desc, cap, status = request.form['name'], request.form['description'], request.form['capacity'], request.form['status']
            if 'facility_id' in request.form and request.form['facility_id']:
                cursor.execute('UPDATE facilities SET name=%s, description=%s, capacity=%s, status=%s WHERE id=%s', 
                             (name, desc, cap, status, request.form['facility_id']))
            else:
                cursor.execute('INSERT INTO facilities (name, description, capacity, status) VALUES (%s, %s, %s, %s)', 
                             (name, desc, cap, status))
            mysql.connection.commit()
            return redirect(url_for('manage_facilities'))
        return render_template('manage_facilities.html', facilities=get_facilities(only_active=False))
    return redirect(url_for('login'))

@app.route('/delete_facility/<int:id>')
def delete_facility(id):
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM facilities WHERE id = %s', (id,))
        mysql.connection.commit()
    return redirect(url_for('manage_facilities'))

@app.route('/admin/bookings')
def admin_bookings():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT b.id AS booking_id, b.start_time, b.end_time, b.purpose, b.status, 
                   f.name AS facility_name, u.name AS faculty_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN users u ON b.user_id = u.id
            WHERE b.status = 'pending'
            ORDER BY b.start_time ASC
        """)
        return render_template('admin_bookings.html', bookings=cursor.fetchall())
    return redirect(url_for('login'))

@app.route('/approve_booking/<int:id>')
def approve_booking(id):
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE bookings SET status = 'approved', approved_by = %s WHERE id = %s", (session['id'], id))
        mysql.connection.commit()
        return redirect(url_for('admin_bookings'))
    return redirect(url_for('login'))

@app.route('/reject_booking', methods=['POST'])
def reject_booking():
    if 'role' in session and session['role'] == 'admin':
        booking_id = request.form['booking_id']
        reason = request.form['reason']
        
        cursor = mysql.connection.cursor()
        # Update status AND save the reason
        cursor.execute("UPDATE bookings SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, booking_id))
        mysql.connection.commit()
        
        return redirect(url_for('admin_bookings'))
    return redirect(url_for('login'))

@app.route('/admin/reports')
def admin_reports():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT b.start_time, b.end_time, b.purpose, f.name AS facility_name, u.name AS faculty_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN users u ON b.user_id = u.id
            WHERE b.status = 'approved'
            ORDER BY b.start_time DESC
        """)
        return render_template('admin_reports.html', reports=cursor.fetchall())
    return redirect(url_for('login'))

@app.route('/admin/feedback')
def admin_feedback():
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT fb.*, f.name as facility_name, u.name as faculty_name
            FROM feedback fb
            JOIN bookings b ON fb.booking_id = b.id
            JOIN facilities f ON b.facility_id = f.id
            JOIN users u ON b.user_id = u.id
            ORDER BY fb.date_submitted DESC
        """)
        return render_template('admin_feedback.html', feedbacks=cursor.fetchall())
    return redirect(url_for('login'))

@app.route('/toggle_user_status/<int:id>')
def toggle_user_status(id):
    if 'role' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # 1. Get current status
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (id,))
        user = cursor.fetchone()
        
        if user:
            # 2. Toggle Status (If 1 make 0, If 0 make 1)
            new_status = 0 if user['is_active'] == 1 else 1
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, id))
            mysql.connection.commit()
            
            msg = "User Deactivated." if new_status == 0 else "User Reactivated."
            flash(msg, 'warning' if new_status == 0 else 'success')
            
        return redirect(url_for('manage_users'))
    return redirect(url_for('login'))

# --- FACULTY ROUTES ---
@app.route('/api/calendar')
def api_calendar():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch BOTH Approved AND Pending bookings
    cursor.execute("""
        SELECT b.start_time, b.end_time, b.status, f.name as facility_name
        FROM bookings b 
        JOIN facilities f ON b.facility_id = f.id
        WHERE b.status IN ('approved', 'pending')
    """)
    events = []
    for b in cursor.fetchall():
        # Format time (e.g., "8:00am-10:00am")
        time_str = f"{b['start_time'].strftime('%I:%M%p').lower()}-{b['end_time'].strftime('%I:%M%p').lower()}"
        
        # Determine Color based on Status
        if b['status'] == 'approved':
            color = '#198754' # Green
            status_label = "" # No label needed for approved
        else:
            color = '#ffc107' # Yellow/Orange
            status_label = " (PENDING)" # Add text so they know it's not final

        title = f"{time_str} | {b['facility_name']}{status_label}"
        
        events.append({
            'title': title, 
            'start': b['start_time'].isoformat(), 
            'end': b['end_time'].isoformat(), 
            'color': color,
            # Make text black if yellow (for readability), white if green
            'textColor': '#000000' if b['status'] == 'pending' else '#ffffff'
        })
    return jsonify(events)


@app.route('/my_bookings')
def my_bookings():
    if 'role' in session and session['role'] == 'faculty':
        return render_template('my_bookings.html', bookings=get_user_bookings(session['id']), current_time=datetime.now())
    return redirect(url_for('login'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'role' in session and session['role'] == 'faculty':
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO feedback (booking_id, rating, remarks) VALUES (%s, %s, %s)", 
                       (request.form['booking_id'], request.form['rating'], request.form['remarks']))
        mysql.connection.commit()
        return redirect(url_for('my_bookings'))
    return redirect(url_for('login'))

@app.route('/faculty', methods=['GET', 'POST'])
def faculty_booking():
    if 'role' in session and session['role'] == 'faculty':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        active_facilities = get_facilities(only_active=True) # Hide maintenance

        if request.method == 'POST':
            facility_id = request.form['facility_id']
            start_str, end_str, purpose = request.form['start_time'], request.form['end_time'], request.form['purpose']
            
            # --- VALIDATION ---
            start_dt = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
            
            if start_dt < datetime.now():
                return render_template('faculty_booking.html', facilities=active_facilities, error="Cannot book past dates.")
            if start_dt >= end_dt:
                return render_template('faculty_booking.html', facilities=active_facilities, error="End time must be after Start time.")
            
            # Maintenance Check
            cursor.execute("SELECT status FROM facilities WHERE id = %s", (facility_id,))
            fac = cursor.fetchone()
            if fac and fac['status'] == 'maintenance':
                return render_template('faculty_booking.html', facilities=active_facilities, error="Facility is under maintenance.")

            # Conflict Check
            cursor.execute("SELECT * FROM bookings WHERE facility_id=%s AND status!='rejected' AND start_time<%s AND end_time>%s", 
                           (facility_id, end_str, start_str))
            if cursor.fetchone():
                return render_template('faculty_booking.html', facilities=active_facilities, error="Time slot already taken.")
            
            cursor.execute('INSERT INTO bookings (facility_id, user_id, start_time, end_time, purpose) VALUES (%s, %s, %s, %s, %s)', 
                           (facility_id, session['id'], start_str, end_str, purpose))
            mysql.connection.commit()
            return redirect(url_for('my_bookings'))

        return render_template('faculty_booking.html', facilities=active_facilities)
    return redirect(url_for('login'))

@app.route('/print_permit/<int:id>')
def print_permit(id):
    if 'role' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT b.id, b.start_time, b.end_time, b.purpose, 
                f.name as facility_name, u.name as faculty_name, admin_user.name as approver_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN users u ON b.user_id = u.id
            LEFT JOIN users admin_user ON b.approved_by = admin_user.id
            WHERE b.id = %s AND b.status = 'approved'
        """, (id,))
        return render_template('print_permit.html', booking=cursor.fetchone())
    return "Permit not found."

# --- ADD THIS TO app.py ---

@app.route('/cancel_booking/<int:id>')
def cancel_booking(id):
    if 'role' in session and session['role'] == 'faculty':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # 1. Security Check: Does this booking belong to the logged-in user?
        cursor.execute("SELECT * FROM bookings WHERE id=%s AND user_id=%s", (id, session['id']))
        booking = cursor.fetchone()
        
        if booking:
            # 2. Check if it's in the past (Optional safety)
            # if booking['start_time'] < datetime.now():
            #     return "Cannot cancel past bookings."

            # 3. Delete the booking to free up the slot
            cursor.execute("DELETE FROM bookings WHERE id=%s", (id,))
            mysql.connection.commit()
            
        return redirect(url_for('my_bookings'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)