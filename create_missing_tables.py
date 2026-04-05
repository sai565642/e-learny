import pymysql

c = pymysql.connect(host='127.0.0.1', user='root', password='root', db='elearning')
cursor = c.cursor()
queries = [
    'CREATE TABLE IF NOT EXISTS contact_messages (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)',
    'CREATE TABLE IF NOT EXISTS courses_app_course_instructors (id BIGINT AUTO_INCREMENT PRIMARY KEY, course_id BIGINT, user_id BIGINT)',
    'CREATE TABLE IF NOT EXISTS courses_app_language (id BIGINT AUTO_INCREMENT PRIMARY KEY, slug VARCHAR(255), name VARCHAR(255))',
    'CREATE TABLE IF NOT EXISTS courses_app_section (id BIGINT AUTO_INCREMENT PRIMARY KEY, course_id BIGINT, title VARCHAR(255), `order` INT, category_id BIGINT, language_id BIGINT, slug VARCHAR(255))',
    'CREATE TABLE IF NOT EXISTS courses_app_sub_section (id BIGINT AUTO_INCREMENT PRIMARY KEY, section_id BIGINT, title VARCHAR(255), `order` INT, category_id BIGINT, language_id BIGINT, slug VARCHAR(255), course_id BIGINT)',
    'CREATE TABLE IF NOT EXISTS courses_app_video (id BIGINT AUTO_INCREMENT PRIMARY KEY, sub_section_id BIGINT, title VARCHAR(255), video_file VARCHAR(255), `order` INT, course_id BIGINT, section_id BIGINT, category_id BIGINT, language_id BIGINT, slug VARCHAR(255), thumbnail VARCHAR(255), demo TINYINT)',
    'CREATE TABLE IF NOT EXISTS courses_app_document (id BIGINT AUTO_INCREMENT PRIMARY KEY, sub_section_id BIGINT, title VARCHAR(255), document VARCHAR(255), `order` INT, course_id BIGINT, category_id BIGINT, language_id BIGINT, slug VARCHAR(255), section_id BIGINT)',
    'CREATE TABLE IF NOT EXISTS purchases_app_coursespurchased (id BIGINT AUTO_INCREMENT PRIMARY KEY, course_id BIGINT, user_id BIGINT, course_category_id BIGINT, language_id BIGINT, date DATE)',
    'CREATE TABLE IF NOT EXISTS student_video_progress (id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id BIGINT, video_id BIGINT, is_completed TINYINT)',
]
for q in queries:
    cursor.execute(q)
c.commit()

alter_queries = [
    'ALTER TABLE courses_app_course ADD COLUMN language_id BIGINT',
    'ALTER TABLE courses_app_course ADD COLUMN original_price DECIMAL(10,2) DEFAULT 0',
    'ALTER TABLE courses_app_course ADD COLUMN discount_price DECIMAL(10,2) DEFAULT 0',
    'ALTER TABLE courses_app_course ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
    'ALTER TABLE courses_app_course ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP',
    'ALTER TABLE courses_app_course ADD COLUMN course_active TINYINT DEFAULT 1',
    'ALTER TABLE courses_app_course ADD COLUMN trending TINYINT DEFAULT 0'
]
for aq in alter_queries:
    try: 
        cursor.execute(aq)
    except Exception as e: 
        pass
c.commit()
c.close()
print("All missing tables created!")
