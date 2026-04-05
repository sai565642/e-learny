import pymysql
import pymysql.cursors
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.Error as err:
        print(f"Database Connection Error: {err}")
        return None

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    result = None
    
    try:
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
            if 'INSERT' in query.upper():
                result = cursor.lastrowid
                if result is None:
                    result = True
            else:
                result = True
        elif fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
            
    except pymysql.Error as err:
        error_msg = f"Database Query Error: {err}"
        print(error_msg)
        with open("db_error.log", "a") as f:
            f.write(error_msg + "\n")
        if commit:
            conn.rollback()
        return None
    finally:
        try:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
        except: pass
            
    return result

# --------------------------------------- AUTH HELPERS ---------------------------------------

def create_user(username, email, password, first_name='', last_name='', role='Student'):
    if execute_query("SELECT id FROM auth_user WHERE username = %s OR email = %s", (username, email), fetchone=True):
        return False, "Username or Email already exists"
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    query = """
        INSERT INTO auth_user (username, email, password, first_name, last_name, is_superuser, is_staff, is_active, date_joined)
        VALUES (%s, %s, %s, %s, %s, 0, 0, 1, %s)
    """
    res = execute_query(query, (username, email, hashed_password, first_name, last_name, now_str), commit=True)
    
    if isinstance(res, str) and res.startswith("Error"):
        return False, f"Failed to create user: {res}"

    # Verify creation
    user = execute_query("SELECT id FROM auth_user WHERE username = %s", (username,), fetchone=True)
    if user:
        user_id = user['id']
        execute_query("INSERT INTO user_management_app_profile (user_id, occupational_status) VALUES (%s, %s)", (user_id, role), commit=True)
        return True, user_id
    
    return False, f"Failed to verify creation after insert. Res: {res}"

def authenticate_user(username, password):
    user = execute_query("SELECT * FROM auth_user WHERE username = %s", (username,), fetchone=True)
    if user:
        try:
            if check_password_hash(user['password'], password):
                return user
        except:
            if user['password'] == password:
                return user
    return None

# --------------------------------------- COURSE HELPERS ---------------------------------------

def get_course_structure(course_id):
    sql = """
        SELECT c.*, u.first_name, u.last_name, u.username as instructor_name, u.id as instructor_id,
               cat.name as category_name
        FROM courses_app_course c 
        JOIN courses_app_course_instructors ci ON c.id = ci.course_id 
        JOIN auth_user u ON ci.user_id = u.id 
        LEFT JOIN courses_app_course_category cat ON c.category_id = cat.id
        WHERE c.id = %s
    """
    course = execute_query(sql, (course_id,), fetchone=True)
    if not course:
        return None, None
    
    sections = execute_query("SELECT * FROM courses_app_section WHERE course_id = %s ORDER BY `order` ASC", (course_id,), fetchall=True) or []
    for section in sections:
        # Get all sub-sections
        sub_sections = execute_query("SELECT id FROM courses_app_sub_section WHERE section_id = %s ORDER BY `order` ASC", (section['id'],), fetchall=True) or []
        sub_ids = [s['id'] for s in sub_sections]
        
        section['lectures'] = []
        section['documents'] = []
        
        if sub_ids:
            # Flatten videos into lectures
            placeholders = ', '.join(['%s'] * len(sub_ids))
            section['lectures'] = execute_query(f"SELECT * FROM courses_app_video WHERE sub_section_id IN ({placeholders}) ORDER BY `order` ASC", tuple(sub_ids), fetchall=True) or []
            section['documents'] = execute_query(f"SELECT * FROM courses_app_document WHERE sub_section_id IN ({placeholders}) ORDER BY `order` ASC", tuple(sub_ids), fetchall=True) or []
            
    return course, sections
