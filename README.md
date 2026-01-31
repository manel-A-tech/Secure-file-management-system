# Secure-file-management-system
A Python-based application for secure file sharing and management with authentication, encryption, and access control.

Overview
Secure Share is a Flask-based web application that provides secure file storage, encryption, and collaborative file sharing features. The platform allows users to upload, encrypt, and share files with controlled access, while also offering collaborative folders for team-based file management.

Core Features

 Security Features
End-to-end file encryption using AES-256 encryption

Password-based key derivation (PBKDF2 with SHA256)

File integrity verification via SHA-256 hashing

Secure session management with configurable lifetimes

Email verification for account security

 File Management
Personal file storage with categorization

File sharing with access codes and expiration dates

Favorite file marking system

Download tracking and statistics

File integrity checking on download

 Collaboration Features
Collaborative folders for team file sharing

Role-based access control (Owner, Editor, Viewer)

Email invitations with secure token links

Public/private folder settings

Collaborative file upload/download

 Email Integration
Account verification emails

File share notifications

Collaboration invitations

Password reset functionality

 Architecture
Tech Stack
Backend: Flask (Python)

Database: SQLite with SQLAlchemy ORM

Frontend: HTML, CSS (with SCSS), JavaScript

Encryption: cryptography.fernet (AES-256)

Email: Flask-Mail with Gmail SMTP

Authentication: Flask-Login

Database Models
Account - User accounts with verification
id, email, username, password, is_verified, 
verification_code, code_expiry, theme

UploadedFile - Personal file storage records
id, user_id, original_filename, stored_filename, 
file_size, salt, upload_date, download_count, 
is_favorite, category, file_hash

FileShare - File sharing records
id, file_id, sender_id, recipient_email, 
share_code, created_at, expires_at, access_count, max_access

CollabFolder - Collaborative folders
id, name, description, created_by, created_at, is_public

CollabMember - Folder membership and invitations
id, folder_id, user_id, role, joined_at, 
invite_token, invite_status, invited_at, invited_by

CollabFile - Files in collaborative folders
folder_id ,uploaded_by ,original_filename ,stored_filename, file_hash

Note : Collaborative files are encrypted using the folder creator's password, so all members can decrypt them regardless of their own password.

How Encryption Works
The encryption pipeline is split across encruption.py and file_management.py:
Upload flow:
  raw file bytes
      │
      ▼
  PBKDF2HMAC(password, random 16-byte salt, 100 000 iterations)
      │ produces a 32-byte key
      ▼
  Fernet(key).encrypt(file bytes)
      │
      ├──► encrypted bytes  →  saved to disk  (uploads/<unique_filename>)
      └──► base64(salt)     →  stored in DB   (UploadedFile.salt)

Download flow:
  encrypted bytes  ←  read from disk
  base64(salt)     ←  read from DB
      │
      ▼
  PBKDF2HMAC(password, decoded salt, 100 000 iterations)  →  same key
      │
      ▼
  Fernet(key).decrypt(encrypted bytes)
      │
      ▼
  SHA-256 hash compared against the hash stored at upload time
      │
      ▼
  decrypted file sent to user
Key points:

The salt is unique per file, so the same password produces a different encryption key each time.
Fernet provides authenticated encryption (AES-128-CBC + HMAC-SHA256), so tampering is detected at the decryption step.
A separate SHA-256 hash of the original plaintext is stored at upload time and verified on every download for an additional integrity check.

API Endpoints
Authentication
GET / - Home page

GET/POST /register - User registration

GET/POST /login - User login

GET /logout - User logout

GET/POST /verify - Email verification

GET /resend-code/<user_id> - Resend verification code

File Management
GET /dashboard - User dashboard

POST /upload - Upload file

GET /download/<file_id> - Download personal file

POST /delete-file/<file_id> - Delete file

GET /toggle-favorite/<file_id> - Toggle favorite status

File Sharing
GET/POST /share/<file_id> - Share file with others

GET/POST /access-shared - Access shared files with code

Collaboration
GET /collaborations - List collaborative folders

POST /collab/create - Create collaborative folder

GET /collab/<folder_id> - View specific folder

POST /collab/<folder_id>/upload - Upload to collaborative folder

GET /collab/<folder_id>/download/<file_id> - Download from collaborative folder

POST /collab/<folder_id>/invite - Invite members

POST /collab/<folder_id>/remove/<member_id> - Remove members

POST /collab/<folder_id>/delete - Delete folder

GET /invite/<token> - View invitation

Account Management
GET/POST /edit/<id> - Edit account details

GET /delete/<id> - Delete account

Project Structure
SecureShare/
│
├── app.py                  # Main application: routes, models, business logic
├── encruption.py           # Encryption/decryption helpers (Fernet + PBKDF2)
├── file_management.py      # FileManager class: disk I/O, hashing, temp files
│
├── templates/
│   ├── base.html           # Shared layout and navigation bar
│   ├── index.html          # Landing page
│   ├── registration.html   # Sign-up form
│   ├── verify.html         # Email verification code entry
│   ├── login.html          # Sign-in form
│   ├── dashboard.html      # Main dashboard: stats, upload, file grid
│   ├── edit.html           # Profile editing form
│   ├── share.html          # File sharing configuration form
│   ├── access_shared.html  # Enter a share code to download a file
│   ├── collaborations.html # Collaborative folders: create, view, upload, invite
│   └── view_invitation.html# Accept or decline a collaboration invite
│
├── static/
│   └── style.css           # Global stylesheet
│
├── uploads/                # Directory for encrypted files on disk (auto-created)
│
└── instance/
    └── database.db         # SQLite database file (auto-created)

Setup & Installation
Prerequisites

Python 3.9+
pip

Steps
bash# 1. Clone the repository
git clone <repository-url>
cd SecureShare

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Linux / macOS
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install flask flask-sqlalchemy flask-login flask-mail flask-migrate flask-scss cryptography werkzeug

# 4. Run database migrations (first time)
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# 5. Start the development server
python app.py
The server starts at http://127.0.0.1:5000 by default.

Note: The uploads/ folder is created automatically on first run if it does not exist.


Note: This is a student project for educational purposes. Always use additional security measures for production deployments.
