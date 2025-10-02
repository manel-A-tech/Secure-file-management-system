# Secure-file-management-system

Secure File Management System
A Python-based application that enables users to securely share and manage files with robust authentication, encrypted storage, and access control mechanisms.
 Project Overview
This project demonstrates the practical application of cybersecurity principles in file management. The system combines backend development with security best practices, implementing password hashing, file encryption, authentication mechanisms, and protection against brute-force attacks.
Academic Context: This project is being developed as part of [Course Name/Code] under the supervision of [Professor Name] at [University Name] for the [Semester/Year] semester.
 Project Goals

Implement secure user authentication and authorization
Develop encrypted file storage and retrieval system
Apply industry-standard security practices
Create a user-friendly interface for file management
Demonstrate understanding of cryptographic principles

 Key Features
Core Functionality

User Registration & Login

Secure account creation with username and password
Password hashing using bcrypt
Session management


Encrypted File Storage

Automatic file encryption during upload (AES/Fernet)
Secure file storage with user-based isolation
Decryption on authorized download


Access Control

User-specific file access permissions
Admin role for system monitoring (optional)
Prevention of unauthorized file access



Security Features

Password Security: Bcrypt hashing with salt
File Encryption: AES encryption via Python cryptography library
Brute-Force Protection: Failed login tracking and rate limiting
Audit Logging: Security event monitoring
Session Security: Token-based authentication
