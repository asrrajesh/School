# MySchool - Flet Desktop Application

A modern, feature-rich educational application built with Flet and Python. MySchool provides user authentication, account management, and question bank functionality with a beautiful Material Design interface.

## Features

- **User Authentication**
  - Secure sign-up and login with email/mobile number (via the edukoreaiapi backend)
  - Password recovery functionality
  - Session management

- **User Dashboard**
  - Welcome screen with personalized greeting
  - Navigation drawer menu
  - Quick access to features
  - Secure logout functionality

- **Question Bank**
  - Coming soon! (Placeholder for future content)

- **Modern UI**
  - Material Design 3 interface
  - Responsive layout
  - Gradient headers
  - Smooth navigation

## Prerequisites

Before running this project, ensure you have the following installed:

- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **edukoreaiapi backend running** - this UI is a client only; start the API server from the sibling `edukoreaiapi` project first (see its README), then point this app at it via `API_BASE_URL` in `.env` (defaults to `http://localhost:8000`).

## Installation Steps

### 1. Clone or Navigate to Project Directory

```bash
cd c:\Rajesh\School\myschool
```

### 2. Create a Virtual Environment (Optional but Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **flet** - UI framework
- **httpx** - HTTP client used to call the edukoreaiapi backend
- **python-dotenv** - Environment variable management

Or manually install:
```bash
pip install flet httpx python-dotenv
```

### 4. Start the API server

All database and Claude OCR logic now lives in the sibling `edukoreaiapi` project. Start it first (defaults to `http://localhost:8000`):
```bash
cd ..\edukoreaiapi
python main.py
```
Then set `API_BASE_URL` in this project's `.env` if the API isn't on `localhost:8000`.

### 5. Run the Application

```bash
python main.py
```

The application window will open automatically. The login screen will be displayed.

## Android Build and APK Creation

To create an Android APK for this project, you can either use the Flet packaging workflow or build directly from the generated Flutter project.

### Prerequisites for Android Build

Install the following:

- **Flutter SDK** - [Install Flutter](https://docs.flutter.dev/get-started/install)
- **Android Studio** with Android SDK
- **JDK 17** or compatible Java version
- Ensure Android SDK and Flutter are added to your `PATH`

Then verify the setup:

```bash
flutter doctor
```

If Android licenses are pending, run:

```bash
flutter doctor --android-licenses
```

### Option 1: Build APK Using Flet

From the project root:

```bash
cd c:\Rajesh\School\myschool
flet build apk --debug
```

For a production-ready release APK:

```bash
flet build apk --release
```

This creates the APK package for Android and stores it in the generated build output folder.

### Option 2: Build APK Directly from the Flutter Project

```bash
cd c:\Rajesh\School\myschool\flet_android_build
flutter pub get
flutter build apk --debug
```

Release build:

```bash
flutter build apk --release
```

### APK Output Location

After the build completes, the APK is usually generated here:

```bash
flet_android_build\build\app\outputs\flutter-apk\app-release.apk
```

For debug builds, the output file is typically:

```bash
flet_android_build\build\app\outputs\flutter-apk\app-debug.apk
```

### Optional: Build Android App Bundle

```bash
flutter build appbundle
```

This generates a `.aab` file that is commonly used for Google Play upload.

## Project Structure

```
myschool/
├── main.py                          # Application entry point
├── requirements.txt                 # Project dependencies
├── README.md                        # This file
├── config/                          # Configuration module
│   ├── __init__.py
│   └── config.py                   # Centralized configuration settings
├── screens/                         # UI screen modules
│   ├── __init__.py
│   ├── login_screen.py             # Login interface
│   ├── signup_screen.py            # User registration interface
│   ├── forgot_password_screen.py   # Password recovery interface
│   ├── home_screen.py              # Dashboard/home interface
│   └── question_bank_screen.py     # Question bank interface (coming soon)
└── database/                        # Database layer
    ├── __init__.py
    └── db.py                       # MongoDB operations and utilities
```

## Usage Guide

### First Time Users

1. **Sign Up**
   - Click "Sign Up" on the login screen
   - Enter a valid email address or mobile number (10-15 digits)
   - Create a password (minimum 8 characters)
   - Confirm your password
   - Click "CREATE ACCOUNT"

2. **Login**
   - Enter your email or mobile number
   - Enter your password
   - Click "LOGIN"

### Existing Users

1. **Login**
   - Enter your credentials
   - Click "LOGIN"

2. **Access Dashboard**
   - View your personalized welcome message
   - Click the menu icon (☰) to open the navigation drawer

3. **Navigation**
   - **Question Bank** - Access question bank (coming soon)
   - **Exit** - Close the application
   - **Logout** - Log out of your account (click logout icon in top right)

### Forgot Password

1. Click "Forgot Password?" on the login screen
2. Enter your email or mobile number
3. Click "SEND RESET LINK"
4. Instructions will be sent to your email/SMS (stub implementation)

## Configuration

All application settings are managed through environment variables in the `.env` file. This provides a clean, secure, and easily customizable configuration system.

### Quick Start - Local Development

A `.env` file is already included with sensible defaults for local development. No additional configuration is needed to get started!

```bash
# Just run the app, it will use settings from .env
python main.py
```

### Customizing Settings

Edit the `.env` file in the project root to customize any settings:

```bash
# Edit .env
nano .env    # or use your favorite editor
```

The `.env` file contains all configuration organized by category with clear comments.

### MongoDB Configuration

In `.env`:

```bash
# Local MongoDB (default)
MONGO_URI=mongodb://localhost:27017/
DB_NAME=myschool

# For MongoDB Atlas (cloud), uncomment and update:
# MONGO_URI=mongodb+srv://username:password@your_cluster.mongodb.net/myschool?retryWrites=true&w=majority
```

### Application Window Settings

In `.env`:

```bash
WINDOW_WIDTH=400                # Window width in pixels
WINDOW_HEIGHT=780               # Window height in pixels
WINDOW_RESIZABLE=true           # Allow user to resize window
BACKGROUND_COLOR=#F5F5F5        # Background color (hex)
```

### Theme Configuration

In `.env`:

```bash
THEME_COLOR=#3949AB             # Primary theme color
SECONDARY_COLOR=#5C6BC0         # Secondary theme color
APP_TITLE=MySchool              # Application window title
APP_VERSION=1.0.0               # Application version
```

### Security Settings

In `.env`:

```bash
PASSWORD_MIN_LENGTH=8           # Minimum password length
SESSION_TIMEOUT=0               # Session timeout in minutes (0 = no timeout)
MAX_LOGIN_ATTEMPTS=5            # Max login attempts before lockout
LOCKOUT_DURATION=15             # Lockout duration in minutes
```

### Validation Settings

In `.env`:

```bash
EMAIL_PATTERN=^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$  # Email regex pattern
MOBILE_PATTERN=^\+?[0-9]{10,15}$                   # Mobile number pattern
MOBILE_MIN_LENGTH=10                                # Min mobile digits
MOBILE_MAX_LENGTH=15                                # Max mobile digits
```

### Feature Flags

Enable or disable features in `config/config.py`:

```python
ENABLE_PASSWORD_RESET_EMAIL = False      # Email-based password reset
ENABLE_SMS_NOTIFICATIONS = False         # SMS notifications
ENABLE_USER_REGISTRATION = True          # Allow new user registration
ENABLE_GUEST_ACCESS = False              # Guest mode (coming soon)
ENABLE_SOCIAL_LOGIN = False              # Social login (coming soon)
```

### Logging Configuration

Edit `config/config.py` to customize logging:

```python
LOG_LEVEL = "INFO"              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = False             # Log to file
LOG_TO_CONSOLE = True           # Log to console
LOG_FILE_PATH = "logs/myschool.log"  # Log file location
```

## Database Schema

### Users Collection

```json
{
  "_id": ObjectId,
  "username": "user@example.com",        // Email or mobile number
  "password": "$2b$12$...",              // Bcrypt hashed password
  "created_at": ISODate("2024-01-01")   // Account creation timestamp
}
```

## Troubleshooting

### MongoDB Connection Error
- **Error:** "Cannot connect to database"
- **Solution:** 
  - Ensure MongoDB is running (`mongod`)
  - Check connection string in `database/db.py`
  - Verify MongoDB is accessible on port 27017

### Import Errors
- **Error:** "ModuleNotFoundError: No module named 'flet'"
- **Solution:** Run `pip install -r requirements.txt`

### Password Hashing Issues
- **Error:** "AttributeError: module 'bcrypt' has no attribute..."
- **Solution:** Ensure bcrypt is installed: `pip install bcrypt`

### Port Already in Use
- **Error:** Address already in use
- **Solution:** Change the port in MongoDB connection or close other instances

### Application Won't Start
- **Solution:**
  1. Check Python version: `python --version` (must be 3.9+)
  2. Verify all dependencies: `pip list`
  3. Check for syntax errors: `python -m py_compile main.py`

## Development Notes

### Adding New Features

1. Create a new screen in `screens/` folder
2. Implement view function returning `ft.Column` or `ft.Container`
3. Add route handler in `main.py`
4. Import the view function in `main.py`

### Database Operations

All database operations are in `database/db.py`. Key functions:

- `register_user(username, password)` - Create new user
- `login_user(username, password)` - Authenticate user
- `request_password_reset(username)` - Handle password reset

### Password Requirements

- Minimum 8 characters
- Email format: `user@domain.com`
- Mobile: 10-15 digits (e.g., `+919876543210`)

## Security Considerations

- Passwords are hashed using bcrypt with salt
- Never store plain text passwords
- MongoDB index on username ensures uniqueness
- Session management via page.session in Flet

## Future Enhancements

- [ ] Implement actual password reset email/SMS
- [ ] Complete Question Bank feature
- [ ] User profile management
- [ ] Progress tracking
- [ ] Exam mode
- [ ] Multiple choice questions with scoring

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review error messages in console output
3. Verify MongoDB connection
4. Check Python version compatibility

## License

This project is provided as-is for educational purposes.

## Dependencies Version Info

- flet: Latest
- pymongo: Latest
- bcrypt: Latest
- Python: 3.9+

---

**Happy Learning! 🎓**
