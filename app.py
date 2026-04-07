import random
import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query, get_course_structure, create_user
from config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.context_processor
def inject_user():
    return dict(user=getattr(app, 'user', None), profile=getattr(app, 'profile', None))

@app.before_request
def load_user():
    if 'user_id' in session:
        user_id = session['user_id']
        app.user = execute_query("SELECT * FROM auth_user WHERE id = %s", (user_id,), fetchone=True)
        profile = execute_query("SELECT * FROM user_management_app_profile WHERE user_id = %s", (user_id,), fetchone=True)
        
        if app.user and not profile:
            execute_query("INSERT INTO user_management_app_profile (user_id, occupational_status, is_approved) VALUES (%s, %s, %s)",
                         (user_id, 'Student', 0), commit=True)
            profile = execute_query("SELECT * FROM user_management_app_profile WHERE user_id = %s", (user_id,), fetchone=True)
            
        app.profile = profile
    else:
        app.user = None
        app.profile = None

# Real Email Sender (Gmail SMTP)
def send_otp_email(email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = f"{otp} is your e-Learny Verification Code"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: Arial, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f7f6; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="100%" style="max-width: 500px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 40px 0 20px 0;">
                                    <img src="https://img.icons8.com/fluency/96/graduation-cap.png" alt="e-Learny" width="64" height="64" style="display: block;">
                                    <h1 style="color: #007bff; font-size: 28px; margin: 15px 0 0 0; letter-spacing: -0.5px; font-weight: bold;">e-Learny</h1>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="padding: 0 40px 30px 40px;">
                                    <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 15px 0;">Verify Your Email</h2>
                                    <p style="color: #666666; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Welcome to the future of learning! Please use the verification code below to complete your registration and unlock your potential.
                                    </p>
                                    <div style="background-color: #f8f9fa; border: 2px dashed #007bff; border-radius: 8px; padding: 20px; display: inline-block;">
                                        <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #007bff;">{otp}</span>
                                    </div>
                                    <p style="color: #999999; font-size: 13px; margin: 30px 0 0 0;">
                                        This code will expire in 10 minutes.<br>If you didn't request this code, please ignore this email.
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="background-color: #f8f9fa; padding: 20px; border-top: 1px solid #eeeeee;">
                                    <p style="color: #aaaaaa; font-size: 12px; margin: 0;">&copy; 2026 e-Learny Platform. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.starttls()
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if name and email and message:
            execute_query("INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)", 
                         (name, email, message), commit=True)
            flash("Thank you! Your message has been safely received. Our team will reach out soon.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin/support', methods=['GET'])
def admin_support():
    if not getattr(app, 'user', None) or not app.user['is_superuser']: return redirect(url_for('index'))
    messages = execute_query("SELECT * FROM contact_messages ORDER BY created_at DESC", fetchall=True) or []
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if not getattr(app, 'user', None) or not app.user['is_superuser']: return redirect(url_for('index'))
    all_users = execute_query("SELECT p.occupational_status FROM auth_user u JOIN user_management_app_profile p ON u.id = p.user_id", fetchall=True) or []
    all_courses = execute_query("SELECT id FROM courses_app_course", fetchall=True) or []
    unseen_msg = execute_query("SELECT COUNT(*) as count FROM contact_messages", fetchone=True)
    stats = {
        'users': len(all_users),
        'students': len([u for u in all_users if u['occupational_status'] == 'Student']),
        'teachers': len([u for u in all_users if u['occupational_status'] == 'Teacher']),
        'courses': len(all_courses),
        'unseen_messages': unseen_msg['count'] if unseen_msg else 0
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not getattr(app, 'user', None) or not app.user['is_superuser']: return redirect(url_for('index'))
    if request.method == 'POST' and request.form.get('action') == 'delete_user':
        target_id = request.form.get('id')
        target_is_admin = execute_query("SELECT is_superuser FROM auth_user WHERE id = %s", (target_id,), fetchone=True)
        if target_is_admin and target_is_admin['is_superuser']:
            flash("CRITICAL: Administrative profiles cannot be deleted via web interface.", "error")
        else:
            execute_query("DELETE FROM user_management_app_profile WHERE user_id = %s", (target_id,), commit=True)
            execute_query("DELETE FROM auth_user WHERE id = %s", (target_id,), commit=True)
            flash("User successfully removed from infrastructure.", "success")
            
    users = execute_query("SELECT u.id, u.username, u.email, u.is_superuser, p.occupational_status, p.id as profile_id, p.is_approved FROM auth_user u JOIN user_management_app_profile p ON u.id = p.user_id ORDER BY u.id DESC", fetchall=True)
    return render_template('admin/users.html', users=users)

@app.route('/admin/teachers', methods=['GET', 'POST'])
def admin_teachers():
    if not getattr(app, 'user', None) or not app.user['is_superuser']: return redirect(url_for('index'))
    if request.method == 'POST':
        action = request.form.get('action')
        target_id = request.form.get('id')
        if action == 'approve_teacher':
            execute_query("UPDATE user_management_app_profile SET is_approved = 1 WHERE user_id = %s", (target_id,), commit=True)
            flash("Teacher approved successfully!", "success")
        elif action == 'revoke_teacher':
            execute_query("UPDATE user_management_app_profile SET is_approved = 0 WHERE user_id = %s", (target_id,), commit=True)
            flash("Teacher access revoked.", "warning")
        elif action == 'delete_user':
            execute_query("DELETE FROM user_management_app_profile WHERE user_id = %s", (target_id,), commit=True)
            execute_query("DELETE FROM auth_user WHERE id = %s", (target_id,), commit=True)
            flash("Teacher deleted.", "error")
    teachers = execute_query("SELECT u.id, u.username, u.first_name, u.last_name, u.email, p.id as profile_id, p.is_approved, p.occupational_status FROM auth_user u JOIN user_management_app_profile p ON u.id = p.user_id WHERE p.occupational_status = 'Teacher' ORDER BY p.id DESC", fetchall=True)
    return render_template('admin/approve_teachers.html', teachers=teachers)

@app.route('/admin/courses', methods=['GET', 'POST'])
def admin_courses():
    if not getattr(app, 'user', None) or not app.user['is_superuser']: return redirect(url_for('index'))
    
    if request.method == 'POST' and request.form.get('action') == 'delete_course':
        target_id = request.form.get('id')
        enr_count = execute_query("SELECT COUNT(*) as cnt FROM purchases_app_coursespurchased WHERE course_id = %s", (target_id,), fetchone=True)
        if enr_count and enr_count['cnt'] > 0:
            flash(f"Cannot delete course! {enr_count['cnt']} students are enrolled.", "error")
        else:
            execute_query("DELETE FROM courses_app_course_instructors WHERE course_id = %s", (target_id,), commit=True)
            execute_query("DELETE FROM courses_app_course WHERE id = %s", (target_id,), commit=True)
            flash("Course deleted successfully.", "success")
    
    sql = """
        SELECT c.*, u.username as instructor_name, u.first_name, u.last_name, u.id as instructor_id,
               cat.name as category_name
        FROM courses_app_course c 
        JOIN courses_app_course_instructors ci ON c.id = ci.course_id 
        JOIN auth_user u ON ci.user_id = u.id
        LEFT JOIN courses_app_course_category cat ON c.category_id = cat.id
        ORDER BY c.id DESC
    """
    courses = execute_query(sql, fetchall=True) or []
    for c in courses:
        enr = execute_query("SELECT COUNT(*) as cnt FROM purchases_app_coursespurchased WHERE course_id = %s", (c['id'],), fetchone=True)
        c['student_count'] = enr['cnt'] if enr else 0
        
    return render_template('all_courses.html', courses=courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        if execute_query("SELECT id FROM auth_user WHERE username = %s OR email = %s", (username, email), fetchone=True):
            flash("Username or Email already exists", "error")
            return render_template('register.html')
            
        otp = str(random.randint(100000, 999999))
        session['pending_user'] = {
            'username': username, 'email': email, 'password': request.form.get('password'),
            'first_name': request.form.get('first_name'), 'last_name': request.form.get('last_name'),
            'role': request.form.get('role', 'Student'), 'otp': otp
        }
        
        if send_otp_email(email, otp):
            flash("OTP sent to your email!", "success")
            return redirect(url_for('verify_otp'))
        else:
            flash("Failed to send OTP email. Please try again or check SMTP configuration.", "error")
            
    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user' not in session: return redirect(url_for('register'))
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session['pending_user']['otp']:
            data = session['pending_user']
            success, res = create_user(data['username'], data['email'], data['password'], data['first_name'], data['last_name'], data['role'])
            if success:
                session.pop('pending_user')
                flash("Verified and registered! Please login.", "success")
                return redirect(url_for('login'))
            else:
                flash(f"Registration failed: {res}", "error")
        else:
            flash("Invalid OTP.", "error")
    return render_template('verify_otp.html')

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username', '').strip()
    if not username:
        return jsonify({'available': False})
    
    existing = execute_query("SELECT id FROM auth_user WHERE username = %s", (username,), fetchone=True)
    return jsonify({'available': not existing})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = execute_query("SELECT * FROM auth_user WHERE username = %s", (username,), fetchone=True)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash(f"Welcome back, {user['username']}!", "success")
            if user['is_superuser']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    app.user = None
    flash("Successfully logged out. We'll see you again soon!", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    if not getattr(app, 'profile', None): return "Profile error", 404
        
    role = app.profile['occupational_status']
    is_approved = app.profile.get('is_approved', 0)
    
    if role == 'Teacher':
        total = execute_query("SELECT COUNT(*) as cnt FROM courses_app_course_instructors WHERE user_id = %s", (app.user['id'],), fetchone=True)['cnt'] or 0
        my_courses = execute_query("""
            SELECT c.* FROM courses_app_course c 
            JOIN courses_app_course_instructors ci ON c.id = ci.course_id 
            WHERE ci.user_id = %s
            ORDER BY c.id DESC LIMIT 5
        """, (app.user['id'],), fetchall=True) or []
        for c in my_courses:
            enr = execute_query("SELECT COUNT(*) as cnt FROM purchases_app_coursespurchased WHERE course_id = %s", (c['id'],), fetchone=True)
            c['student_count'] = enr['cnt'] if enr else 0
            cat = execute_query("SELECT name FROM courses_app_course_category WHERE id = %s", (c['category_id'],), fetchone=True)
            c['domain'] = cat['name'] if cat else 'General'
        
        all_courses = execute_query("SELECT * FROM courses_app_course", fetchall=True) or []
        return render_template('teacher/dashboard.html', courses=my_courses, total_count=total, all_courses=all_courses, is_approved=is_approved)
    
    courses = execute_query("SELECT c.* FROM courses_app_course c JOIN purchases_app_coursespurchased p ON c.id = p.course_id WHERE p.user_id = %s ORDER BY p.id DESC", (app.user['id'],), fetchall=True) or []
    for c in courses:
        total = execute_query("SELECT COUNT(*) as cnt FROM courses_app_video WHERE course_id = %s", (c['id'],), fetchone=True)
        total_count = total['cnt'] or 0
        done = execute_query("SELECT COUNT(DISTINCT vp.video_id) as cnt FROM student_video_progress vp JOIN courses_app_video v ON vp.video_id = v.id WHERE vp.user_id = %s AND v.course_id = %s AND vp.is_completed = 1", (app.user['id'], c['id']), fetchone=True)
        completed_count = done['cnt'] or 0
        c['progress_percent'] = int((completed_count / total_count * 100)) if total_count > 0 else 0
        cat = execute_query("SELECT name FROM courses_app_course_category WHERE id = %s", (c['category_id'],), fetchone=True)
        c['domain'] = cat['name'] if cat else 'General'
    return render_template('student/dashboard.html', courses=courses)

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    c = execute_query("SELECT category_id, language_id, slug FROM courses_app_course WHERE id = %s", (course_id,), fetchone=True)
    if c:
        from datetime import date
        execute_query("INSERT INTO purchases_app_coursespurchased (course_id, user_id, course_category_id, language_id, `date`) VALUES (%s, %s, %s, %s, %s)",
                     (course_id, app.user['id'], c['category_id'], c['language_id'], date.today()), commit=True)
        flash("Successfully enrolled! 🎉", "success")
        return redirect(url_for('course_detail', course_slug=c['slug']))
    return redirect(url_for('dashboard'))

@app.route('/course/<course_slug>')
def course_detail(course_slug):
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    c_info = execute_query("SELECT id FROM courses_app_course WHERE slug = %s", (course_slug,), fetchone=True)
    if not c_info: return "404", 404
    course, sections = get_course_structure(c_info['id'])
    completed_ids = [r['video_id'] for r in (execute_query("SELECT video_id FROM student_video_progress WHERE user_id = %s", (app.user['id'],), fetchall=True) or [])]
    total_lectures = 0
    completed_lectures = 0
    for sec in sections:
        for lec in sec['lectures']:
            total_lectures += 1
            lec['is_completed'] = lec['id'] in completed_ids
            if lec['is_completed']: completed_lectures += 1
            
    is_course_finished = (total_lectures > 0 and completed_lectures >= total_lectures)
    purchased = execute_query("SELECT id FROM purchases_app_coursespurchased WHERE user_id = %s AND course_id = %s", (app.user['id'], course['id']), fetchone=True)
    return render_template('course_detail.html', course=course, sections=sections, purchased=purchased, is_course_finished=is_course_finished)

@app.route('/course/<course_slug>/certificate')
def course_certificate(course_slug):
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    course = execute_query("SELECT id, title FROM courses_app_course WHERE slug = %s", (course_slug,), fetchone=True)
    if not course: return "404", 404
    
    total = execute_query("SELECT COUNT(*) as cnt FROM courses_app_video WHERE course_id = %s", (course['id'],), fetchone=True)['cnt'] or 0
    done = execute_query("SELECT COUNT(DISTINCT vp.video_id) as cnt FROM student_video_progress vp JOIN courses_app_video v ON vp.video_id = v.id WHERE vp.user_id = %s AND v.course_id = %s AND vp.is_completed = 1", (app.user['id'], course['id']), fetchone=True)['cnt'] or 0
    
    if total == 0 or done < total:
        flash("You haven't completed this course yet!", "warning")
        return redirect(url_for('course_detail', course_slug=course_slug))
        
    date_completed = execute_query("SELECT date FROM purchases_app_coursespurchased WHERE user_id = %s AND course_id = %s", (app.user['id'], course['id']), fetchone=True)
    comp_date = date_completed['date'] if date_completed else None
    
    return render_template('certificate.html', course=course, user=app.user, date=comp_date)

@app.route('/toggle_video/<int:video_id>', methods=['POST'])
def toggle_video_progress(video_id):
    if not getattr(app, 'user', None): return jsonify({"error": "Unauthorized"}), 401
    
    vid_info = execute_query("SELECT course_id FROM courses_app_video WHERE id = %s", (video_id,), fetchone=True)
    if not vid_info: return jsonify({"error": "Not found"}), 404
    course_id = vid_info['course_id']
    
    current = execute_query("SELECT id FROM student_video_progress WHERE user_id = %s AND video_id = %s AND is_completed = 1", (app.user['id'], video_id), fetchone=True)
    completed_now = False
    
    if current:
        execute_query("DELETE FROM student_video_progress WHERE user_id = %s AND video_id = %s", (app.user['id'], video_id), commit=True)
    else:
        execute_query("INSERT INTO student_video_progress (user_id, video_id, is_completed) VALUES (%s, %s, 1)", (app.user['id'], video_id), commit=True)
        completed_now = True
        
    total = execute_query("SELECT COUNT(*) as cnt FROM courses_app_video WHERE course_id = %s", (course_id,), fetchone=True)['cnt'] or 0
    done = execute_query("SELECT COUNT(DISTINCT vp.video_id) as cnt FROM student_video_progress vp JOIN courses_app_video v ON vp.video_id = v.id WHERE vp.user_id = %s AND v.course_id = %s AND vp.is_completed = 1", (app.user['id'], course_id), fetchone=True)['cnt'] or 0
    
    is_finished = (completed_now and total > 0 and done >= total)
    return jsonify({"completed": completed_now, "course_finished": is_finished, "done": done, "total": total})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    if request.method == 'POST':
        execute_query("UPDATE auth_user SET first_name = %s, last_name = %s, email = %s WHERE id = %s", (request.form.get('first_name'), request.form.get('last_name'), request.form.get('email'), app.user['id']), commit=True)
        execute_query("UPDATE user_management_app_profile SET mobile = %s, bio = %s, dob = %s, gender = %s WHERE user_id = %s", (request.form.get('mobile'), request.form.get('bio'), request.form.get('dob'), request.form.get('gender'), app.user['id']), commit=True)
        flash("Profile updated successfully! ✨", "success")
        return redirect(url_for('profile'))
    return render_template('profile.html', user=app.user, profile=app.profile)

# --- 2-STEP COURSE CREATION ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    if getattr(app, 'profile', {}).get('occupational_status') != 'Teacher' or not getattr(app, 'profile', {}).get('is_approved'):
        flash("Unauthorized", "error"); return redirect(url_for('dashboard'))
    if request.method == 'POST':
        thumb = ''
        file = request.files.get('thumbnail')
        if file and file.filename and allowed_file(file.filename):
            fname = secure_filename(f"course_{app.user['id']}_{random.randint(1000,9999)}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            thumb = f'/static/uploads/{fname}'
        session['course_draft'] = {
            'title': request.form.get('title'),
            'category': request.form.get('category'),
            'level': request.form.get('level', 'Beginner'),
            'description': request.form.get('description'),
            'thumbnail': thumb
        }
        return redirect(url_for('course_content'))
    return render_template('teacher/add_course.html')

@app.route('/teacher/course-content', methods=['GET', 'POST'])
def course_content():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    if 'course_draft' not in session: return redirect(url_for('add_course'))
    draft = session['course_draft']
    if request.method == 'POST':
        import re, json, datetime
        slug = re.sub(r'[^a-z0-9]+', '-', draft['title'].lower()).strip('-') + f'-{random.randint(100,999)}'
        now = datetime.datetime.now()
        lang_id = 10; cat_id = 10
        if draft['category'] == 'backend': lang_id = 11; cat_id = 11
        elif draft['category'] == 'database': lang_id = 12; cat_id = 12
        elif draft['category'] == 'cloud': lang_id = 13; cat_id = 13
        
        sql = "INSERT INTO courses_app_course (title, slug, description, thumbnail, category_id, language_id, original_price, discount_price, created_at, updated_at, course_active, trending, level) VALUES (%s,%s,%s,%s,%s,%s,0,0,%s,%s,1,0,%s)"
        c_id = execute_query(sql, (draft['title'], slug, draft['description'], draft['thumbnail'], cat_id, lang_id, now, now, draft['level']), commit=True)
        if not isinstance(c_id, int):
            row = execute_query("SELECT id FROM courses_app_course WHERE slug = %s", (slug,), fetchone=True)
            c_id = row['id'] if row else None
        
        if c_id:
            execute_query("INSERT INTO courses_app_course_instructors (course_id, user_id) VALUES (%s,%s)", (c_id, app.user['id']), commit=True)
            sections = json.loads(request.form.get('sections_data', '[]'))
            for i, sec in enumerate(sections):
                s_id = execute_query("INSERT INTO courses_app_section (course_id, title, `order`, category_id, language_id, slug) VALUES (%s,%s,%s,%s,%s,%s)", (c_id, sec['title'], i, cat_id, lang_id, f"sec-{c_id}-{i}"), commit=True)
                if s_id:
                    ss_id = execute_query("INSERT INTO courses_app_sub_section (section_id, title, `order`, category_id, language_id, slug, course_id) VALUES (%s,%s,%s,%s,%s,%s,%s)", (s_id, "Lectures", 0, cat_id, lang_id, f"sub-{s_id}", c_id), commit=True)
                    if ss_id:
                        for j, lec in enumerate(sec['lectures']):
                            execute_query("INSERT INTO courses_app_video (sub_section_id, title, video_file, `order`, course_id, section_id, category_id, language_id, slug, thumbnail, demo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (ss_id, lec['title'], lec['url'], j, c_id, s_id, cat_id, lang_id, f"vid-{ss_id}-{j}", '', 0), commit=True)
                        if sec.get('notes'):
                            execute_query("INSERT INTO courses_app_document (sub_section_id, title, document, `order`, course_id, category_id, language_id, slug, section_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (ss_id, "Notes", sec['notes'], 99, c_id, cat_id, lang_id, f"doc-{ss_id}", s_id), commit=True)
            session.pop('course_draft', None)
            flash("Course Published! 🚀", "success")
            return redirect(url_for('dashboard'))
    return render_template('teacher/course_content.html', draft=draft)

@app.route('/teacher/enrollments')
def enrollments():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    is_admin = app.user.get('is_superuser', 0)
    where = "WHERE ci.user_id = %s" if not is_admin else ""
    params = (app.user['id'],) if not is_admin else ()
    
    data = execute_query(f"""
        SELECT u.id as s_id, u.username as s_name, u.first_name, u.last_name, 
               c.id as c_id, c.title as c_title, p.date
        FROM purchases_app_coursespurchased p
        JOIN auth_user u ON p.user_id = u.id
        JOIN courses_app_course c ON p.course_id = c.id
        JOIN courses_app_course_instructors ci ON c.id = ci.course_id
        {where} ORDER BY p.id DESC
    """, params, fetchall=True) or []
    
    grouped = {}
    for r in data:
        t = execute_query("SELECT COUNT(*) as cnt FROM courses_app_video WHERE course_id = %s", (r['c_id'],), fetchone=True)['cnt'] or 0
        d = execute_query("SELECT COUNT(DISTINCT vp.video_id) as cnt FROM student_video_progress vp JOIN courses_app_video v ON vp.video_id = v.id WHERE vp.user_id = %s AND v.course_id = %s AND vp.is_completed = 1", (r['s_id'], r['c_id']), fetchone=True)['cnt'] or 0
        prog = int((d/t*100)) if t > 0 else 0
        name = f"{r.get('first_name') or ''} {r.get('last_name') or ''}".strip() or r['s_name']
        s_obj = {'name': name, 'progress': prog}
        if r['c_id'] not in grouped: grouped[r['c_id']] = {'title': r['c_title'], 'students': [s_obj]}
        else: grouped[r['c_id']]['students'].append(s_obj)
    return render_template('teacher/enrollments.html', enrollments=list(grouped.values()))

@app.route('/resend-otp')
def resend_otp():
    if 'pending_user' not in session: return redirect(url_for('register'))
    otp = str(random.randint(100000, 999999))
    session['pending_user']['otp'] = otp; session.modified = True
    
    if send_otp_email(session['pending_user']['email'], otp):
        flash("A new OTP has been sent.", "success")
    else:
        flash("Failed to send OTP email. Please check your Gmail App Password configuration in config.py", "error")
    return redirect(url_for('verify_otp'))

@app.route('/languages')
def languages():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    all_langs = execute_query("SELECT * FROM courses_app_language", fetchall=True)
    return render_template('languages.html', all_languages=all_langs)

@app.route('/courses/<language_slug>')
def course_categories(language_slug):
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    lang = execute_query("SELECT * FROM courses_app_language WHERE slug = %s", (language_slug,), fetchone=True)
    if not lang: return "404", 404
    cats = execute_query("SELECT * FROM courses_app_course_category WHERE language_id = %s", (lang['id'],), fetchall=True)
    courses = execute_query("SELECT * FROM courses_app_course WHERE language_id = %s", (lang['id'],), fetchall=True)
    purchases = [p['course_id'] for p in (execute_query("SELECT course_id FROM purchases_app_coursespurchased WHERE user_id = %s", (app.user['id'],), fetchall=True) or [])]
    return render_template('course_list.html', language=lang, categories=cats, courses=courses, purchased_ids=purchases)

@app.route('/admin/profile')
def admin_profile(): return redirect(url_for('profile'))
@app.route('/all-courses')
def all_courses():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    sql = """
        SELECT c.*, u.username as instructor_name, u.first_name, u.last_name, u.id as instructor_id,
               cat.name as category_name
        FROM courses_app_course c 
        JOIN courses_app_course_instructors ci ON c.id = ci.course_id 
        JOIN auth_user u ON ci.user_id = u.id
        LEFT JOIN courses_app_course_category cat ON c.category_id = cat.id
        ORDER BY c.id DESC
    """
    courses = execute_query(sql, fetchall=True) or []
    for c in courses:
        enr = execute_query("SELECT COUNT(*) as cnt FROM purchases_app_coursespurchased WHERE course_id = %s", (c['id'],), fetchone=True)
        c['student_count'] = enr['cnt'] if enr else 0
    return render_template('all_courses.html', courses=courses)

@app.route('/teacher/delete_course/<int:course_id>', methods=['POST'])
def teacher_delete_course(course_id):
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    owner = execute_query("SELECT user_id FROM courses_app_course_instructors WHERE course_id = %s", (course_id,), fetchone=True)
    if owner and owner['user_id'] == app.user['id']:
        enr_count = execute_query("SELECT COUNT(*) as cnt FROM purchases_app_coursespurchased WHERE course_id = %s", (course_id,), fetchone=True)
        if enr_count and enr_count['cnt'] > 0:
            flash(f"Cannot delete course! {enr_count['cnt']} students already enrolled.", "error")
        else:
            execute_query("DELETE FROM courses_app_course_instructors WHERE course_id = %s", (course_id,), commit=True)
            execute_query("DELETE FROM courses_app_course WHERE id = %s", (course_id,), commit=True)
            flash("Course deleted successfully.", "success")
    else:
        flash("Unauthorized action", "error")
    return redirect(url_for('dashboard'))
@app.route('/student/my-courses')
def my_courses():
    if not getattr(app, 'user', None): return redirect(url_for('login'))
    if getattr(app, 'profile', {}).get('occupational_status') != 'Student': return redirect(url_for('dashboard'))
    courses = execute_query("SELECT c.* FROM courses_app_course c JOIN purchases_app_coursespurchased p ON c.id = p.course_id WHERE p.user_id = %s ORDER BY p.id DESC", (app.user['id'],), fetchall=True) or []
    for c in courses:
        total = execute_query("SELECT COUNT(*) as cnt FROM courses_app_video WHERE course_id = %s", (c['id'],), fetchone=True)['cnt'] or 0
        done = execute_query("SELECT COUNT(DISTINCT vp.video_id) as cnt FROM student_video_progress vp JOIN courses_app_video v ON vp.video_id = v.id WHERE vp.user_id = %s AND v.course_id = %s AND vp.is_completed = 1", (app.user['id'], c['id']), fetchone=True)['cnt'] or 0
        c['progress_percent'] = int((done / total * 100)) if total > 0 else 0
        cat = execute_query("SELECT name FROM courses_app_course_category WHERE id = %s", (c['category_id'],), fetchone=True)
        c['domain'] = cat['name'] if cat else 'General'
    return render_template('student/my_courses.html', courses=courses)
@app.route('/course/<int:course_id>/enrollments')
def course_enrollments(course_id):
    # Simply redirect to the main enrollments hub which is already grouped by course
    return redirect(url_for('enrollments'))

if __name__ == '__main__':
    app.run(debug=True)
