#  SecureShare

> A Flask-based web application for secure file storage, encryption, and collaborative file sharing — with end-to-end encryption, role-based access control, and full audit trails.

![Python](https://img.shields.io/badge/Python-3.9%2B-3572A5?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white)
![AES-256](https://img.shields.io/badge/Encryption-AES%E2%80%93256-e74c3c?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-003087?style=flat-square)


---

##  Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [How Encryption Works](#how-encryption-works)
4. [Architecture](#architecture)
5. [Database Models](#database-models)
6. [API Endpoints](#api-endpoints)
7. [Project Structure](#project-structure)
8. [Setup & Installation](#setup--installation)
9. [Notes](#notes)

---

##  Overview

**SecureShare** lets users upload, encrypt, and share files with controlled access. Every file is encrypted before it ever touches disk using AES-256, and only users with the correct credentials and permissions can decrypt it. The platform also supports collaborative folders where teams can share files under a shared encryption context with role-based access.

---

##  Core Features

###  Security
- End-to-end file encryption using **AES-256**
- Password-based key derivation via **PBKDF2 + SHA-256**
- File integrity verification with **SHA-256 hashing**
- Secure session management with configurable lifetimes
- Email verification on account creation

###  File Management
- Personal file storage with **categorization**
- File sharing via **access codes** with expiration dates
- Favorite file marking system
- Download tracking and statistics
- Integrity check on every download

###  Collaboration
- **Collaborative folders** for team-based file sharing
- Role-based access control — **Owner**, **Editor**, **Viewer**
- Email invitations with secure token links
- Public / private folder toggle
- Shared upload and download within folders

###  Email Integration
- Account verification emails
- File share notifications
- Collaboration invitations
- Password reset functionality

---

##  How Encryption Works

The encryption pipeline is split across `encruption.py` and `file_management.py`.

### Upload Flow

```
  raw file bytes
       │
       ▼
  PBKDF2HMAC(password, random 16-byte salt, 100,000 iterations)
       │  produces a 32-byte key
       ▼
  Fernet(key).encrypt(file bytes)
       │
       ├──► encrypted bytes  →  saved to disk   (uploads/<unique_filename>)
       └──► base64(salt)     →  stored in DB    (UploadedFile.salt)
```

### Download Flow

```
  encrypted bytes  ←  read from disk
  base64(salt)     ←  read from DB
       │
       ▼
  PBKDF2HMAC(password, decoded salt, 100,000 iterations)  →  same key
       │
       ▼
  Fernet(key).decrypt(encrypted bytes)
       │
       ▼
  SHA-256 hash compared against the hash stored at upload time
       │
       ▼
  decrypted file sent to user
```

### Key Points

| Point | Detail |
|---|---|
| **Unique salt per file** | The same password produces a different encryption key for every file. |
| **Authenticated encryption** | Fernet uses AES-128-CBC + HMAC-SHA256 internally — any tampering is caught at decryption. |
| **Double integrity check** | A SHA-256 hash of the original plaintext is stored at upload and re-verified on every download. |

> **Note:** Collaborative files are encrypted using the **folder creator's password**, so all folder members can decrypt them regardless of their own password.

---

##  Architecture

### Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask (Python) |
| **Database** | SQLite via SQLAlchemy ORM |
| **Frontend** | HTML, CSS (SCSS), JavaScript |
| **Encryption** | `cryptography.fernet` (AES-256) |
| **Email** | Flask-Mail + Gmail SMTP |
| **Auth** | Flask-Login |

---

##  Database Models

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Account   │────▶│ UploadedFile │────▶│   FileShare   │
│             │     │              │     │               │
│ id          │     │ id           │     │ id            │
│ email       │     │ user_id      │     │ file_id       │
│ username    │     │ original_filename  │ sender_id     │
│ password    │     │ stored_filename    │ recipient_email│
│ is_verified │     │ file_size    │     │ share_code    │
│ theme       │     │ salt         │     │ expires_at    │
│ ...         │     │ file_hash    │     │ max_access    │
└─────────────┘     │ ...          │     └───────────────┘
                    └──────────────┘
┌──────────────┐    ┌──────────────┐     ┌───────────────┐
│ CollabFolder │───▶│ CollabMember │     │  CollabFile   │
│              │    │              │     │               │
│ id           │    │ id           │     │ folder_id     │
│ name         │    │ folder_id    │     │ uploaded_by   │
│ description  │    │ user_id      │     │ original_filename
│ created_by   │    │ role         │     │ stored_filename
│ is_public    │    │ invite_token │     │ file_hash     │
│ ...          │    │ ...          │     └───────────────┘
└──────────────┘    └──────────────┘
```

| Model | Purpose |
|---|---|
| `Account` | User accounts — credentials, verification state, theme |
| `UploadedFile` | Personal file records — name, size, salt, hash, favorites, category |
| `FileShare` | Sharing metadata — codes, expiry, access limits |
| `CollabFolder` | Team folders — name, owner, public/private flag |
| `CollabMember` | Membership & invitations — role, token, status |
| `CollabFile` | Files inside collaborative folders — linked to folder, hashed |

---

##  API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Home page |
| `GET / POST` | `/register` | User registration |
| `GET / POST` | `/login` | User login |
| `GET` | `/logout` | User logout |
| `GET / POST` | `/verify` | Email verification |
| `GET` | `/resend-code/<user_id>` | Resend verification code |

### File Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard` | User dashboard |
| `POST` | `/upload` | Upload a file |
| `GET` | `/download/<file_id>` | Download a personal file |
| `POST` | `/delete-file/<file_id>` | Delete a file |
| `GET` | `/toggle-favorite/<file_id>` | Toggle favorite status |

### File Sharing

| Method | Endpoint | Description |
|---|---|---|
| `GET / POST` | `/share/<file_id>` | Share a file with others |
| `GET / POST` | `/access-shared` | Access a shared file via code |

### Collaboration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/collaborations` | List all collaborative folders |
| `POST` | `/collab/create` | Create a collaborative folder |
| `GET` | `/collab/<folder_id>` | View a specific folder |
| `POST` | `/collab/<folder_id>/upload` | Upload to a collaborative folder |
| `GET` | `/collab/<folder_id>/download/<file_id>` | Download from a collaborative folder |
| `POST` | `/collab/<folder_id>/invite` | Invite a member |
| `POST` | `/collab/<folder_id>/remove/<member_id>` | Remove a member |
| `POST` | `/collab/<folder_id>/delete` | Delete a folder |
| `GET` | `/invite/<token>` | View an invitation |

### Account Management

| Method | Endpoint | Description |
|---|---|---|
| `GET / POST` | `/edit/<id>` | Edit account details |
| `GET` | `/delete/<id>` | Delete account |

---

##  Project Structure

```
SecureShare/
│
├── app.py                   # Main application — routes, models, business logic
├── encruption.py            # Encryption/decryption helpers (Fernet + PBKDF2)
├── file_management.py       # FileManager class — disk I/O, hashing, temp files
│
├── templates/
│   ├── base.html            # Shared layout and navigation bar
│   ├── index.html           # Landing page
│   ├── registration.html    # Sign-up form
│   ├── verify.html          # Email verification code entry
│   ├── login.html           # Sign-in form
│   ├── dashboard.html       # Main dashboard — stats, upload, file grid
│   ├── edit.html            # Profile editing form
│   ├── share.html           # File sharing configuration form
│   ├── access_shared.html   # Enter a share code to download a file
│   ├── collaborations.html  # Collaborative folders — create, view, upload, invite
│   └── view_invitation.html # Accept or decline a collaboration invite
│
├── static/
│   └── style.css            # Global stylesheet
│
├── uploads/                 # Encrypted files on disk (auto-created)
│
└── instance/
    └── database.db          # SQLite database file (auto-created)
```

---

##  Setup & Installation

### Prerequisites

- Python **3.9+**
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd SecureShare

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install flask flask-sqlalchemy flask-login flask-mail flask-migrate flask-scss cryptography werkzeug

# 4. Run database migrations (first time only)
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# 5. Start the development server
python app.py
```

The server starts at **http://127.0.0.1:5000** by default.

> **Note:** The `uploads/` folder is created automatically on first run if it does not already exist.

---

##  Notes

>  This is a **student project** built for educational purposes. If you plan to deploy this in a production environment, consider adding additional security hardening such as HTTPS enforcement, stronger rate limiting, secrets management, and a production-grade database.

