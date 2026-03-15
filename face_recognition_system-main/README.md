# Face Recognition Attendance Management System

This project is a modern attendance management system that integrates face recognition technology to track employee presence. The system provides a comprehensive portal for both administrators and employees, ensuring an efficient, transparent, and secure attendance process.

## Table of Contents

1. [Key Features](#key-features)
2. [Technologies Used](#technologies-used)
3. [System Requirements](#system-requirements)
4. [Quick Start with Docker (Recommended)](#quick-start-with-docker-recommended)
5. [Manual Installation and Setup](#manual-installation-and-setup)
   - [Backend](#backend)
   - [Frontend](#frontend)
6. [Usage](#usage)
   - [Login](#login)
   - [Public Attendance (Face Recognition)](#public-attendance-face-recognition)
   - [Admin Portal](#admin-portal)
   - [Employee Portal](#employee-portal)
7. [Default Admin Account](#default-admin-account)

## Key Features

### Face Recognition Attendance
- Accurate face recognition for check-in/check-out
- Face training with multiple poses (front, left, right, up, down) to improve accuracy
- Liveness detection to prevent spoofing attempts

### Comprehensive Employee Management (Admin)
- Add, edit, soft-delete, and restore employee information
- Manage face training data for individual employees
- Reset employee passwords

### Attendance Management
- Records check-in/check-out timestamps
- Categorizes attendance: normal, late, half-day
- Applies company attendance policies (work hours, lunch breaks, late arrival grace period, maximum check-ins/check-outs)

### Employee Self-Service Portal
- View personal attendance history with date filtering
- Submit attendance recovery/adjustment requests for discrepancies
- Change account password

### Reporting
- Generate attendance reports by employee or department
- Export reports to files (e.g., Excel)

### System Configuration (Admin)
- Manage critical system settings
- Create database backups
- Reset/restore the system

### Robust Authentication System
- Clear role-based access control for Admin and Employee
- Account locking mechanism after multiple failed login attempts
- Mandatory password change for initial employee logins

## Technologies Used

### Backend
- **Python 3.12+**
- **Flask**: A microframework for web development
- **SQLAlchemy**: An Object-Relational Mapper (ORM) for database interaction
- **OpenCV**: A library for image processing
- **dlib**: A machine learning toolkit for various facial processing tasks
- **insightface**: A high-performance face recognition library
- **pytz**: For timezone handling

### Frontend
- **Vue.js 3**: A progressive JavaScript framework for building user interfaces
- **Pinia**: A lightweight and powerful state management library for Vue.js
- **Vuetify 3**: A Material Design UI framework for building beautiful and responsive interfaces
- **Axios**: A Promise-based HTTP client for interacting with the backend API
- **Vue Router**: The official routing library for Vue.js

### Database
- **SQLite**

### Deployment
- **Docker**: Containerized deployment for easy setup
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving

## System Requirements

### For Docker Deployment (Recommended)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Minimum RAM**: 4GB
- **Minimum Disk Space**: 10GB

### For Manual Setup
- Python 3.8+
- Node.js 16+ and npm (or Yarn)
- pip (Python package installer)
- OpenCV (Often installed as a dependency with face recognition libraries)
- C++ Build Tools (For Windows, required for dlib and related libraries. On Linux/macOS, basic development tools are usually sufficient)

## Quick Start with Docker (Recommended)

### Option 1: Using Pre-built Images from Docker Hub

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_URL>
   cd <your_project_folder>
   ```

2. **Run the application:**
   ```bash
   docker-compose up -d
   ```

**Alternative - Download only docker-compose.yml:**
```bash
mkdir face-recognition-system
cd face-recognition-system
curl -O https://raw.githubusercontent.com/van49785/face_recognition_system/main/docker-compose.yml
docker-compose up -d
```

3. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost/api

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Build from Source

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_URL>
   cd <your_project_folder>
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

3. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost/api

### Docker Images Available

The following pre-built images are available on Docker Hub:

- **Backend**: `thaovan01320/face-recognition-backend:latest`
- **Frontend**: `thaovan01320/face-recognition-frontend:latest`

### Data Persistence

The Docker setup includes volume mounts for data persistence:
- **Database**: `./backend/instance` - SQLite database files
- **Face Data**: `./backend/data` - Employee face recognition data

## Manual Installation and Setup

### Backend

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_URL>
   cd <your_project_folder>/backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   # If you encounter issues installing dlib, refer to dlib's documentation or search for solutions specific to your operating system.
   ```

4. **Configure the database:**
   
   Create a `.env` file in the `backend/` directory (at the same level as `app/` and `run.py`).
   
   Add your database configuration. Example for SQLite (development):
   ```env
   DATABASE_URL=sqlite:///./data/attendance.db
   SECRET_KEY=your_super_secret_key_here # Change this key!
   JWT_SECRET_KEY=your_jwt_secret_key_here # Change this key!
   ```

5. **Initialize the database:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   python seed_data.py  # Add initial admin user or sample data
   ```

6. **Run the backend server:**
   ```bash
   python main.py
   # By default, it will run on http://127.0.0.1:5000/
   ```

### Frontend

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend # If you are currently in the backend directory
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   # Or if you use Yarn:
   # yarn install
   ```

3. **Run the frontend development server:**
   ```bash
   npm run dev
   # Or if you use Yarn:
   # yarn dev
   ```
   
   The application will run on `http://localhost:5173/` (or a different port if 5173 is already in use).

## Usage

Once the application is running (either via Docker or manual setup), you can access it via your web browser.

### Login

Access the login page:
- **Docker**: http://localhost/login
- **Manual Setup**: http://localhost:5173/login

You will see two tabs: "Admin Login" and "Employee Login".

- **Admin Login**: For system administrators
- **Employee Login**: For employees. If this is their first login or their password requires a change, the system will redirect them to a password change page

### Public Attendance (Face Recognition)

Access the attendance interface:
- **Docker**: http://localhost/attendance
- **Manual Setup**: http://localhost:5173/attendance

This is the main attendance interface where employees can use face recognition to check-in/check-out.

### Admin Portal

After logging in with an Admin account, you will be redirected to the admin dashboard. From here, you can:

- **Manage Employees**: Add, edit, soft-delete, and restore employee information and face data
- **View Attendance History**: See detailed attendance records for all employees
- **Manage Recovery Requests**: View and process attendance adjustment requests from employees
- **View Reports**: Generate and export aggregated attendance reports
- **System Configuration**: Adjust settings, create backups, etc.

### Employee Portal

After logging in with an Employee account, you will be redirected to your personal portal. From here, you can:

- **View Personal Attendance History**: See all your attendance records, with the ability to filter by date range
- **Submit Attendance Recovery Requests**: Submit requests to adjust attendance records for forgotten check-ins/outs or errors
- **Change Password**: Update your account password

## Default Admin Account

The system comes with a pre-configured admin account:

- **Username**: `admin1`
- **Password**: `123456`
- **Email**: `van49785@gmail.com`
- **Role**: `admin`

> **Security Note**: Please change the default admin password immediately after first login in a production environment.

## Troubleshooting

### Docker Issues

1. **Port conflicts**: If port 80 is already in use, modify the docker-compose.yml file to use a different port:
   ```yaml
   frontend:
     ports:
       - "8080:80"  # Change to port 8080
   ```

2. **Permission issues**: On Linux/macOS, you might need to use `sudo` with Docker commands.

3. **Face recognition not working**: Ensure your camera is accessible and not being used by other applications.

### Manual Setup Issues

1. **dlib installation fails**: This is common on Windows. Try installing pre-compiled wheels or use conda instead of pip.

2. **Camera access denied**: Check browser permissions for camera access.

## Contributing

If you wish to contribute to this project, please fork the repository, create a new branch for your feature/bug fix, and submit a Pull Request.

## Support

For issues and questions, please create an issue in the GitHub repository or contact van49785@gmail.com.
