# 🎓 e-Learny Platform | Project Setup Guide

Welcome to **e-Learny Platform**, a premium, high-density E-Learning Management System built with Python Flask and MySQL.

---

## 🛠️ Prerequisites
- **Python 3.9+**
- **MySQL Server 8.0+**
- **Virtual Environment** (Recommended)

---

## 🏗️ 1. Database Configuration
You must have a MySQL server running. Follow these steps to initialize the database:

1. **Log into MySQL Shell:**
   ```sql
   mysql -u root -p
   ```

2. **Run Initialization SQL:**
   Create the database and required tables. You can use the provided `schema.sql` and run these commands first:
   ```sql
   CREATE DATABASE IF NOT EXISTS elearning;
   USE elearning;
   
   -- The application handles table creation via the models, 
   -- but ensure your MySQL user has full permissions on 'elearning'.
   ```

---

1. **Configure Credentials:** Open `config.py` in the root directory and update your MySQL connection details:
   ```python
   DB_HOST = '127.0.0.1'
   DB_USER = 'root'
   DB_PASSWORD = 'your_mysql_password'
   DB_NAME = 'elearning'
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 3. Launching the Platform
Start the Flask development server:
```bash
python app.py
```
Visit the platform at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔐 4. Fresh Installation: Creating an Admin
The platform requires an Administrative account to manage users and approve teachers. If you are starting on a fresh database:

1. **Run the Admin Creator tool:**
   ```bash
   python create_admin.py
   ```
2. **Follow the interactive prompts** to set your username, email, and secure password.
3. This creates a **Superuser** with full access to the Admin Dashboard.

---

## 📂 5. Project Architecture
- `app.py`: Core routing and logic.
- `database.py`: Hardened MySQL interaction engine.
- `templates/`: Premium UI/UX design components.
- `static/`: Digital assets (High-fidelity 3D workspace icons).

---

### 🛡️ Developed for Engineering Excellence
Developed by **SAI Coder** for the future of digital education. 🚀🛡️🏆🏙️🔐
