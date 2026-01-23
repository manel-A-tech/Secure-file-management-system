from enum import unique
from datetime import datetime, timedelta
from os import access
import profile
from flask import Flask, flash, render_template, redirect, request, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from encruption import encode_salt, encrypt_file, decode_salt, decrypt_file
from file_management import FileManager
import os
import random
import string
from flask_mail import Mail, Message
from flask_migrate import Migrate
import secrets

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['SESSION_COOKIE_NAME'] = 'secure_share_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
# email configuration:
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Simple Mail Transfer Protocol
app.config['MAIL_PORT'] = 587  # encryption
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bouasriachaima362@gmail.com'
# gmail 3rd party app password
app.config['MAIL_PASSWORD'] = 'pzxy mdaj wihc epdr'
app.config['MAIL_DEFAULT_SENDER'] = 'bouasriachaima362@gmail.com'

# file upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16mg

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

# ensure upload folder exists(temporary, if we buy a server the upload is going to be in it)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# initialize FileManager
file_manager = FileManager(app.config['UPLOAD_FOLDER'])

# initializing the session manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page"
login_manager.login_message_category = "error"

# creating the data base(inheriting the UserMixin now)


class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    # whether the email is verified
    is_verified = db.Column(db.Boolean, default=False)
    # stores the 6 digit code sent to users email
    verification_code = db.Column(db.String(6), nullable=True)
    # stores the exact date/time when the code expires
    code_expiry = db.Column(db.DateTime, nullable=True)
    # stores users chosen color for their profile
    profile_color = db.Column(db.String(7), default='#00ffc2')
    # stores user's theme preference
    theme = db.Column(db.String(10), default='dark')
    # creates a link between Account and UploadedFile tables
    files = db.relationship('UploadedFile', backref='owner',
                            lazy=True, cascade='all, delete-orphan')
    shares = db.relationship('FileShare', backref='sender', lazy=True,
                             cascade='all, delete-orphan')  # links account to FileShare table

    def __repr__(self) -> str:
        return f"account{self.id},{self.username}"

# creating database for uploaded file


class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'account.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.String(50), nullable=False)
    salt = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    download_count = db.Column(db.Integer, default=0)
    is_favorite = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='other')
    shares = db.relationship('FileShare', backref='file',
                             lazy=True, cascade='all, delete-orphan')
    file_hash = db.Column(db.String(64), nullable=True)  

    def __repr__(self) -> str:
        return f"File: {self.original_filename}"
# create database for shared files
   


class FileShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey(
        'uploaded_file.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey(
        'account.id'), nullable=False)
    # we dont need an account for the recipient
    recipient_email = db.Column(db.String(100), nullable=False)
    # the 8 character code sent to recipient
    share_code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=True)
    # counts how many times share was used
    access_count = db.Column(db.Integer, default=0)
    max_access = db.Column(db.Integer, default=5)

    def __repr__(self) -> str:
        return f"Share: {self.share_code}"

# Collaborative folder model
class CollabFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_public = db.Column(db.Boolean, default=False)
    # Relationships
    members = db.relationship('CollabMember', backref='folder', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('CollabFile', backref='folder', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('Account', foreign_keys=[created_by])
    
    def __repr__(self):
        return f"CollabFolder: {self.name}"
    
# Folder membership model
class CollabMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, 
                         db.ForeignKey('collab_folder.id', name='fk_collab_member_folder'), 
                         nullable=False)
    user_id = db.Column(db.Integer, 
                       db.ForeignKey('account.id', name='fk_collab_member_user'), 
                       nullable=False)
    role = db.Column(db.String(20), default='viewer')
    joined_at = db.Column(db.DateTime, default=datetime.now)
    
    # New columns for invitations
    invite_token = db.Column(db.String(32), unique=True, nullable=True)
    invite_status = db.Column(db.String(20), default='pending')
    invited_at = db.Column(db.DateTime, default=datetime.now)
    invited_by = db.Column(db.Integer, 
                          db.ForeignKey('account.id', name='fk_collab_member_invited_by'), 
                          nullable=True)

    # Relationships
    user = db.relationship('Account', foreign_keys=[user_id], backref='collaborations')
    inviter = db.relationship('Account', foreign_keys=[invited_by], backref='sent_invitations')

# Collaborative files model
class CollabFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('collab_folder.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.String(50), nullable=False)
    salt = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    download_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), default='other')
    file_hash = db.Column(db.String(64), nullable=True)
    # Relationships
    uploader = db.relationship('Account', foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"CollabFile: {self.original_filename}"

@login_manager.user_loader
def load_user(userid):
    return Account.query.get((int(userid)))


# checking if the account is in the database bu the username

def check_account_exists(username):
    account = Account.query.filter_by(username=username).first()
    if account:
        return True
    return False

# encryption


def encrypt_password(password):
    return generate_password_hash(password)

# creating a new account


def create_new_account(username, email, password):
    encrypted_pass = encrypt_password(password)
    verification_code = generate_verification_code()
    code_expiry = datetime.now() + timedelta(minutes=15)
    # random profile color
    colors = ['#00ffc2', '#38bdf8', '#f59e0b', '#ec4899', '#8b5cf6', '#10b981']

    new_account = Account(username=username, email=email,
                          password=encrypted_pass, is_verified=False,
                          verification_code=verification_code, code_expiry=code_expiry,
                          profile_color=random.choice(colors))
    db.session.add(new_account)
    db.session.commit()
    send_verification_email(email, verification_code, username)
    return new_account
# generating unique random 6 digit code


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))
# generating unique random 8 digit code


def generate_share_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# sent email of verification body


def send_verification_email(email, code, username):
    print(f"\n📧 Attempting to send email to {email}...")
    try:
        msg = Message('Verify Your Secure Share Account', recipients=[email])
        msg.body = f'''Hello {username},

     Welcome to Secure Share! 🔐

     Your verification code is: {code}

     This code will expire in 15 minutes.

     If you didn't create an account, please ignore this email.

     Best regards,
     Secure Share Team
     '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        print(f"\n{'='*50}")
        print(f"BACKUP - VERIFICATION CODE: {code}")
        return False


def send_share_notification(recipient_email, sender_name, filename, share_code):
    try:
        msg = Message('Someone Shared a File With You!',
                      recipients=[recipient_email])
        msg.body = f'''Hello!

        {sender_name} has shared a file with you: "{filename}"

        Your access code is: {share_code}

        Visit Secure Share and use this code to download the file.

        Best regards,
        Secure Share Team
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# function to get the category according to the file's extension


def get_file_category(filename):
    extension = file_manager.get_file_extension(filename)
    categories = {
        'images': ['png', 'jpg', 'jpeg', 'gif'],
        'documents': ['txt', 'pdf', 'doc', 'docx'],
        'videos': ['mp4'],
        'audio': ['mp3'],
        'archives': ['zip']
    }
    for category, extensions in categories.items():
        if extension in extensions:
            return category
    return 'other'

# Check if user has access to folder
def user_has_folder_access(user_id, folder_id, required_role=None):
    member = CollabMember.query.filter_by(
        user_id=user_id, 
        folder_id=folder_id
    ).first()
    
    if not member:
        return False
    
    if required_role:
        role_hierarchy = {'viewer': 1, 'editor': 2, 'owner': 3}
        return role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0)
    
    return True

def generate_invite_token():
    """Generate a secure random token for invitations"""
    return secrets.token_urlsafe(24)

# Send collaboration invite email
def send_collab_invite(recipient_email, folder_name, sender_name, invite_link):
    """Send invitation link instead of code"""
    try:
        msg = Message('You\'ve been invited to collaborate!', 
                     recipients=[recipient_email])
        msg.html = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>🤝 Collaboration Invitation</h2>
            <p>Hello!</p>
            <p><strong>{sender_name}</strong> has invited you to collaborate on the folder: <strong>"{folder_name}"</strong></p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p>Click the link below to accept or decline the invitation:</p>
                <a href="{invite_link}" style="display: inline-block; background: #00ffc2; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 10px 0;">
                    🔗 View Invitation
                </a>
                <p style="font-size: 12px; color: #666;">This link will expire in 7 days.</p>
            </div>
            <p>Best regards,<br>Secure Share Team</p>
        </body>
        </html>
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending invite: {str(e)}")
        return False

############################ ROUTES######################

# home page


@app.route("/")
def home():
    return render_template('index.html')

# registration page


@app.route("/register", methods=["POST", "GET"])
def register():
    # check if already logged in
    if current_user.is_authenticated:
        return redirect("/dashboard")
    # add account
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Validation
        if not username or not email or not password:
            flash("All fields are required", "error")
            return redirect("/register")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect("/register")

        if check_account_exists(username):
            flash("Username already exists", "error")
            return redirect("/register")

        try:
            account = create_new_account(username, email, password)
            flash(
                "Account created successfully! Check your email for the verification code.", "success")
            return redirect(f"/verify?user_id={account.id}")
        except Exception as e:
            db.session.rollback()
            flash(f"error in creating the account :{e}", "error")
            return redirect("/register")

    else:  # for the get request
        return render_template('registration.html')

# verification page


@app.route("/verify", methods=["GET", "POST"])
def verify():
    user_id = request.args.get('user_id') or request.form.get('user_id')
    if not user_id:
        flash("Invalid verification request", "error")
        return redirect("/register")
    account = Account.query.get(user_id)
    if not account:
        flash("Account not found", "error")
        return redirect("/register")
    if account.is_verified:
        flash("Account already verified. Please login.", "success")
        return redirect("/login")
    if request.method == "POST":
        code = request.form.get('verification_code')
        if not code:
            flash("Please enter the verification code", "error")
            return render_template('verify.html', user_id=user_id)
        if datetime.now() > account.code_expiry:
            flash("Verification code expired. Please request a new one.", "error")
            return render_template('verify.html', user_id=user_id, expired=True)
        if code == account.verification_code:
            account.is_verified = True
            account.verification_code = None
            account.code_expiry = None
            db.session.commit()
            flash("Email verified successfully! You can now login.", "success")
            return redirect("/login")
        else:
            flash("Invalid verification code. Please try again.", "error")
            return render_template('verify.html', user_id=user_id)
    return render_template('verify.html', user_id=user_id)

# resending the verification code page


@app.route("/resend-code/<int:user_id>")
def resend_code(user_id):
    account = Account.query.get(user_id)
    if not account:
        flash("Account not found", "error")
        return redirect("/register")

    if account.is_verified:
        flash("Account already verified", "success")
        return redirect("/login")
    new_code = generate_verification_code()
    account.verification_code = new_code
    account.code_expiry = datetime.now() + timedelta(minutes=15)
    db.session.commit()
    if send_verification_email(account.email, new_code, account.username):
        flash("New verification code sent to your email", "success")
    else:
        flash("Failed to send email. Please try again later.", "error")
    return redirect(f"/verify?user_id={user_id}")

# login page


@app.route("/login", methods=["GET", "POST"])
def login():
    # check if already logged in
    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        account = Account.query.filter_by(username=username).first()

        if account and check_password_hash(account.password, password):
            if not account.is_verified:
                flash("Please verify your email before logging in", "error")
                return redirect(f"/verify?user_id={account.id}")
            remember_me = True if remember == 'yes' else False
            login_user(account, remember=remember_me)
            if remember_me:
                session.permanent = True
            else:
                session.permanent = False

            flash("login successful", "success")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect("/dashboard")
        else:
            flash("invalid username or password", "error")
            return redirect("/login")
    else:
        return render_template('login.html')

# logout route


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully", "success")
    return redirect("/login")

# dashborard routes


@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_verified:
        flash("Please verify your email before accessing the dashboard", "error")
        return redirect("/verify")
    # get users files with optional filtering
    filter_by = request.args.get('filter', 'all')
    category = request.args.get('category', 'all')
    query = UploadedFile.query.filter_by(user_id=current_user.id)
    # to get the favorite files
    if filter_by == 'favorites':
        query = query.filter_by(is_favorite=True)
    # to get the files based on the category
    if category != 'all':
        query = query.filter_by(category=category)
    files = query.order_by(UploadedFile.upload_date.desc()).all()
    # calculate stats
    total_files = len(files)
    total_downloads = sum(f.download_count for f in files)
    favorite_count = len([f for f in files if f.is_favorite])
    return render_template('dashboard.html',
                           username=current_user.username,
                           files=files,
                           total_files=total_files,
                           total_downloads=total_downloads,
                           favorite_count=favorite_count,
                           profile_color=current_user.profile_color)

# uploading a file


@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash("No file selected", "error")
        return redirect("/dashboard")

    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect("/dashboard")

    try:
        file_data = file.read()
        file_size = len(file_data)
        if not file_manager.is_file_size_valid(file_size):
            flash("File size exceeds 16MB limit", "error")
            return redirect("/dashboard")

        # Calculate SHA-256 hash for integrity verification
        file_hash = file_manager.hash_file_sha256(file_data)

        encrypted_data, salt = encrypt_file(file_data, current_user.password)
        unique_filename = file_manager.generate_unique_filename(
            current_user.id, file.filename)
        file_manager.save_encrypted_file(encrypted_data, unique_filename)
        salt_encoded = encode_salt(salt)
        category = get_file_category(file.filename)
        # saving the file to the database
        new_file = UploadedFile(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_size=file_manager.format_file_size(file_size),
            salt=salt_encoded,
            category=category,
            file_hash=file_hash  # Store the hash for integrity checking
        )
        db.session.add(new_file)
        db.session.commit()
        flash(
            f"File '{file.filename}' uploaded and encrypted successfully", "success")
        return redirect("/dashboard")
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading file: {str(e)}", "error")
        return redirect("/dashboard")

# downloading a file


@app.route("/download/<int:file_id>")
@login_required
def download_file(file_id):
    file_record = UploadedFile.query.get_or_404(file_id)
    if file_record.user_id != current_user.id:
        flash("You don't have permission to download this file", "error")
        return redirect("/dashboard")
    try:
        encrypted_data = file_manager.read_ecrypted_file(
            file_record.stored_filename)
        salt = decode_salt(file_record.salt)
        decrypted_data = decrypt_file(
            encrypted_data, current_user.password, salt)
        
        # Silent integrity verification - no user notification unless logging
        if file_record.file_hash:
            current_hash = file_manager.hash_file_sha256(decrypted_data)
            if current_hash != file_record.file_hash:
                # Log the integrity failure for admin/developer review
                print(f" Integrity check failed for file ID {file_id}")
                # Continue with download despite integrity issue
                # (You could choose to abort here if you want strict validation)
        
        temp_path = file_manager.creat_temp_file(
            decrypted_data, file_record.original_filename)
        file_record.download_count += 1
        db.session.commit()
        return send_file(temp_path,
                         as_attachment=True,
                         download_name=file_record.original_filename
                         )
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect("/dashboard")
# deleting a file


@app.route("/delete-file/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    file_record = UploadedFile.query.get_or_404(file_id)

    if file_record.user_id != current_user.id:
        flash("You don't have permission to delete this file", "error")
        return redirect("/dashboard")
    try:
        file_manager.delete_file(file_record.stored_filename)
        db.session.delete(file_record)
        db.session.commit()

        flash(
            f"File '{file_record.original_filename}' deleted successfully 🗑️", "success")
        return redirect("/dashboard")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting file: {str(e)}", "error")
        return redirect("/dashboard")

# choosing favorite files


@app.route("/toggle-favorite/<int:file_id>")
@login_required
def toggle_favorite(file_id):
    file_record = UploadedFile.query.get_or_404(file_id)
    if file_record.user_id != current_user.id:
        flash("You don't have permission to modify this file", "error")
        return redirect("/dashboard")

    file_record.is_favorite = not file_record.is_favorite
    db.session.commit()
    status = "added to" if file_record.is_favorite else "removed from"
    flash(f"File {status} favorites ⭐", "success")
    return redirect("/dashboard")

# file sharing route


@app.route("/share/<int:file_id>", methods=["GET", "POST"])
@login_required
def share_file(file_id):
    file_record = UploadedFile.query.get_or_404(file_id)
    if file_record.user_id != current_user.id:
        flash("You don't have permission to share this file", "error")
        return redirect("/dashboard")
    if request.method == "POST":
        recipient_email = request.form.get('recipient_email')
        max_access = int(request.form.get('max_access', 5))
        expiry_days = int(request.form.get('expiry_days', 7))
        if not recipient_email:
            flash("Please enter recipient's email", "error")
            return render_template('sahre.html', file=file_record)
        try:
            share_code = generate_share_code()
            expires_at = datetime.now() + timedelta(days=expiry_days)
            new_share = FileShare(
                file_id=file_id,
                sender_id=current_user.id,
                recipient_email=recipient_email,
                share_code=share_code,
                expires_at=expires_at,
                max_access=max_access
            )
            db.session.add(new_share)
            db.session.commit()
            send_share_notification(
                recipient_email,
                current_user.username,
                file_record.original_filename,
                share_code
            )
            flash(
                f"File shared successfully! Share code: {share_code} 🎁", "success")
            return redirect("/dashboard")
        except Exception as e:
            db.session.rollback()
            flash(f"Error sharing file: {str(e)}", "error")
            return render_template('share.html', file=file_record)

    return render_template('share.html', file=file_record)

# a route to acces the shared files


@app.route("/access-shared", methods=["GET", "POST"])
def access_shared():
    if request.method == "POST":
        share_code = request.form.get('share_code')
        if not share_code:
            flash("Please enter a share code", "error")
            return render_template('access_shared.html')
        share = FileShare.query.filter_by(
            share_code=share_code.upper()).first()
        if not share:
            flash("Invalid share code", "error")
            return render_template('access_shared.html')
        if share.expires_at and datetime.now() > share.expires_at:
            flash("This share link has expired", "error")
            return render_template('access_shared.html')
        if share.access_count >= share.max_access:
            flash("Maximum access limit reached for this share", "error")
            return render_template('access_shared.html')
        share.access_count += 1
        db.session.commit()
        file_record = UploadedFile.query.get(share.file_id)
        owner = Account.query.get(file_record.user_id)
        try:
            encrypted_data = file_manager.read_ecrypted_file(
                file_record.stored_filename)
            salt = decode_salt(file_record.salt)
            decrypted_data = decrypt_file(encrypted_data, owner.password, salt)
            
            # integrity verification for shared files
            if file_record.file_hash:
                current_hash = file_manager.hash_file_sha256(decrypted_data)
                if current_hash != file_record.file_hash:
                    print(f" Integrity check failed for shared file ID {share.file_id}")
            
            temp_path = file_manager.creat_temp_file(
                decrypted_data, file_record.original_filename)
            flash(f"Shared file accessed successfully!", "success")
            return send_file(temp_path,
                             as_attachment=True,
                             download_name=file_record.original_filename)
        except Exception as e:
            flash(f"Error accessing file: {str(e)}", "error")
            return render_template('access_shared.html')
    return render_template('access_shared.html')

# access accounts


#@app.route("/accounts")
#@login_required
#def view_accounts():
    #accounts = Account.query.order_by(Account.id).all()
    #return render_template('accounts.html', accounts=accounts)

# delete an account by the id


@app.route("/delete/<int:id>")
@login_required
def delete(id: int):
    if current_user.id != id:
        flash("You can only delete your own account", "error")
        return redirect("/dashboard")
    delete_account = Account.query.get_or_404(id)
    try:
        user_files = UploadedFile.query.filter_by(user_id=id).all()
        for file in user_files:
            file_manager.delete_file(file.stored_filename)
        db.session.delete(delete_account)
        db.session.commit()
        logout_user()
        flash("Account deleted successfullt", "success")
        return redirect("/")
    except Exception as e:
        db.session.rollback()
        flash(f"error{e}", "error")
        return redirect("/dashboard")


# edit an account in the database
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id: int):
    if current_user.id != id:
        flash("You can only edit your own account", "error")
        return redirect("/dashboard")
    account = Account.query.get_or_404(id)
    if request.method == "POST":
        account.username = request.form.get('username')
        account.email = request.form.get('email')
        new_password = request.form.get('password')
        profile_color = request.form.get('profile_color')
        if profile_color:
            account.profile_color = profile_color
        if new_password:
            account.password = encrypt_password(new_password)
        try:
            db.session.commit()
            logout_user()
            login_user(account)
            flash("Account updated successfully! ✨", "success")
            from time import time
            return redirect(f"/dashboard?t={int(time())}")
        except Exception as e:
            db.session.rollback()
            flash(f"error{e}", "error")
            return redirect(f"/edit/{id}")
    else:
        return render_template("edit.html",
                               account=account,
                               username=account.username)
    

# collaboration feature 

# View all collaborative folders
@app.route("/collaborations")
@login_required
def collaborations():
    # Folders where user is a member
    my_collabs = CollabMember.query.filter_by(user_id=current_user.id).all()
    folders = [collab.folder for collab in my_collabs]
    
    return render_template('collaborations.html', 
                         folders=folders,
                         username=current_user.username,
                         profile_color=current_user.profile_color)

# Create new collaborative folder
@app.route("/collab/create", methods=["POST"])
@login_required
def create_collab_folder():
    name = request.form.get('folder_name')
    description = request.form.get('description', '')
    is_public = request.form.get('is_public') == 'on'
    
    if not name:
        flash("Folder name is required", "error")
        return redirect("/collaborations")
    
    try:
        new_folder = CollabFolder(
            name=name,
            description=description,
            created_by=current_user.id,
            is_public=is_public
        )
        db.session.add(new_folder)
        db.session.flush()
        
        # Add creator as owner
        creator_member = CollabMember(
            folder_id=new_folder.id,
            user_id=current_user.id,
            role='owner'
        )
        db.session.add(creator_member)
        db.session.commit()
        
        flash(f"Folder '{name}' created successfully! 📁", "success")
        return redirect("/collaborations")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating folder: {str(e)}", "error")
        return redirect("/collaborations")

# View specific collaborative folder
@app.route("/collab/<int:folder_id>")
@login_required
def view_collab_folder(folder_id):
    folder = CollabFolder.query.get_or_404(folder_id)
    
    if not user_has_folder_access(current_user.id, folder_id):
        flash("You don't have access to this folder", "error")
        return redirect("/collaborations")
    
    # Get user's role
    member = CollabMember.query.filter_by(
        user_id=current_user.id,
        folder_id=folder_id
    ).first()
    
    files = CollabFile.query.filter_by(folder_id=folder_id).order_by(
        CollabFile.upload_date.desc()
    ).all()
    
    members = CollabMember.query.filter_by(folder_id=folder_id).all()
    
    return render_template('collaborations.html',
                         folder=folder,
                         files=files,
                         members=members,
                         user_role=member.role,
                         username=current_user.username,
                         profile_color=current_user.profile_color)

# Upload file to collaborative folder
@app.route("/collab/<int:folder_id>/upload", methods=["POST"])
@login_required
def upload_collab_file(folder_id):
    folder = CollabFolder.query.get_or_404(folder_id)
    
    if not user_has_folder_access(current_user.id, folder_id, 'editor'):
        flash("You don't have permission to upload files", "error")
        return redirect(f"/collab/{folder_id}")
    
    if 'file' not in request.files:
        flash("No file selected", "error")
        return redirect(f"/collab/{folder_id}")
    
    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(f"/collab/{folder_id}")
    
    try:
        file_data = file.read()
        file_size = len(file_data)
        
        if not file_manager.is_file_size_valid(file_size):
            flash("File size exceeds 16MB limit", "error")
            return redirect(f"/collab/{folder_id}")
        
        file_hash = file_manager.hash_file_sha256(file_data)
        
        # Use folder creator's password for encryption
        creator = Account.query.get(folder.created_by)
        encrypted_data, salt = encrypt_file(file_data, creator.password)
        
        unique_filename = file_manager.generate_unique_filename(
            folder_id, file.filename
        )
        file_manager.save_encrypted_file(encrypted_data, unique_filename)
        
        salt_encoded = encode_salt(salt)
        category = get_file_category(file.filename)
        
        new_file = CollabFile(
            folder_id=folder_id,
            uploaded_by=current_user.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_size=file_manager.format_file_size(file_size),
            salt=salt_encoded,
            category=category,
            file_hash=file_hash
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        flash(f"File '{file.filename}' uploaded successfully! 📤", "success")
        return redirect("/collaborations#folder-" + str(folder_id))  # Scroll to folder
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading file: {str(e)}", "error")
        return redirect("/collaborations#folder-" + str(folder_id))

# Download file from collaborative folder
@app.route("/collab/<int:folder_id>/download/<int:file_id>")
@login_required
def download_collab_file(folder_id, file_id):
    if not user_has_folder_access(current_user.id, folder_id):
        flash("You don't have access to this folder", "error")
        return redirect("/collaborations")
    
    file_record = CollabFile.query.get_or_404(file_id)
    folder = CollabFolder.query.get(folder_id)
    
    try:
        encrypted_data = file_manager.read_ecrypted_file(file_record.stored_filename)
        salt = decode_salt(file_record.salt)
        
        # Use folder creator's password for decryption
        creator = Account.query.get(folder.created_by)
        decrypted_data = decrypt_file(encrypted_data, creator.password, salt)
        
        if file_record.file_hash:
            current_hash = file_manager.hash_file_sha256(decrypted_data)
            if current_hash != file_record.file_hash:
                print(f"⚠️ Integrity check failed for collab file ID {file_id}")
        
        temp_path = file_manager.creat_temp_file(
            decrypted_data, file_record.original_filename
        )
        
        file_record.download_count += 1
        db.session.commit()
        
        return send_file(temp_path,
                        as_attachment=True,
                        download_name=file_record.original_filename)
        
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(f"/collab/{folder_id}")

# Invite member to folder
@app.route("/collab/<int:folder_id>/invite", methods=["POST"])
@login_required
def invite_collab_member(folder_id):
    folder = CollabFolder.query.get_or_404(folder_id)
    
    if not user_has_folder_access(current_user.id, folder_id, 'owner'):
        flash("Only owners can invite members", "error")
        return redirect(f"/collab/{folder_id}")
    
    email = request.form.get('member_email')
    role = request.form.get('role', 'viewer')
    
    if not email:
        flash("Email is required", "error")
        return redirect(f"/collab/{folder_id}")
    
    # Check if user exists
    invited_user = Account.query.filter_by(email=email).first()
    
    if not invited_user:
        flash("User with this email doesn't exist", "error")
        return redirect(f"/collab/{folder_id}")
    
    # Check if already a member
    existing_member = CollabMember.query.filter_by(
        folder_id=folder_id,
        user_id=invited_user.id
    ).first()
    
    if existing_member:
        if existing_member.invite_status == 'pending':
            flash("Invitation is already pending for this user", "warning")
        else:
            flash("User is already a member of this folder", "error")
        return redirect(f"/collab/{folder_id}")
    
    try:
        # Generate unique invite token
        invite_token = generate_invite_token()
        
        # Create invitation record
        invitation = CollabMember(
            folder_id=folder_id,
            user_id=invited_user.id,
            role=role,
            invite_token=invite_token,
            invite_status='pending',
            invited_by=current_user.id
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        # Generate invite link
        invite_link = url_for('view_invitation', token=invite_token, _external=True)
        
        # Send email with link
        send_collab_invite(
            email, 
            folder.name, 
            current_user.username, 
            invite_link
        )
        
        flash(f"Invitation sent to {email}! They'll receive a link to accept. 📧", "success")
        
        # Stay on the same page (use the referrer)
        referrer = request.referrer or url_for('view_collab_folder', folder_id=folder_id)
        return redirect(f"{referrer}#folder-{folder_id}")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error inviting member: {str(e)}", "error")
        return redirect(f"/collab/{folder_id}")

# Remove member from folder
@app.route("/collab/<int:folder_id>/remove/<int:member_id>", methods=["POST"])
@login_required
def remove_collab_member(folder_id, member_id):
    if not user_has_folder_access(current_user.id, folder_id, 'owner'):
        flash("Only owners can remove members", "error")
        return redirect(f"/collab/{folder_id}")
    
    member = CollabMember.query.get_or_404(member_id)
    
    if member.role == 'owner' and member.user_id != current_user.id:
        flash("Cannot remove other owners", "error")
        return redirect(f"/collab/{folder_id}")
    
    try:
        db.session.delete(member)
        db.session.commit()
        flash("Member removed successfully", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing member: {str(e)}", "error")
    
    return redirect("/collaborations#folder-" + str(folder_id))

# Delete collaborative folder
@app.route("/collab/<int:folder_id>/delete", methods=["POST"])
@login_required
def delete_collab_folder(folder_id):
    folder = CollabFolder.query.get_or_404(folder_id)
    
    if not user_has_folder_access(current_user.id, folder_id, 'owner'):
        flash("Only owners can delete folders", "error")
        return redirect("/collaborations")
    
    try:
        # Delete all files in the folder
        files = CollabFile.query.filter_by(folder_id=folder_id).all()
        for file in files:
            file_manager.delete_file(file.stored_filename)
        
        db.session.delete(folder)
        db.session.commit()
        
        flash(f"Folder '{folder.name}' deleted successfully! 🗑️", "success")
        return redirect("/collaborations")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting folder: {str(e)}", "error")
        return redirect("/collaborations")
    
#  route for leaving a collaboration
@app.route("/collab/<int:folder_id>/leave", methods=["POST"])
@login_required
def leave_collab_folder(folder_id):
    folder = CollabFolder.query.get_or_404(folder_id)
    
    # Find the current user's membership
    member = CollabMember.query.filter_by(
        folder_id=folder_id,
        user_id=current_user.id
    ).first()
    
    if not member:
        flash("You are not a member of this folder", "error")
        return redirect("/collaborations")
    
    # Prevent the last owner from leaving
    owner_count = CollabMember.query.filter_by(
        folder_id=folder_id,
        role='owner'
    ).count()
    
    if member.role == 'owner' and owner_count <= 1:
        flash("You are the only owner. Please delete the folder or assign another owner first.", "error")
        return redirect("/collaborations")
    
    try:
        db.session.delete(member)
        db.session.commit()
        flash(f"You have left '{folder.name}' successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error leaving folder: {str(e)}", "error")
    
    return redirect("/collaborations")

@app.route("/invite/<token>")
def view_invitation(token):
    """View invitation page (accessible without login)"""
    invitation = CollabMember.query.filter_by(invite_token=token).first()
    
    if not invitation:
        flash("Invalid or expired invitation link", "error")
        return redirect("/")
    
    if invitation.invite_status != 'pending':
        flash("This invitation has already been processed", "info")
        return redirect("/")
    
    # Check if invitation expired (7 days)
    if datetime.now() > invitation.invited_at + timedelta(days=7):
        flash("This invitation has expired", "error")
        return redirect("/")
    
    folder = CollabFolder.query.get(invitation.folder_id)
    inviter = Account.query.get(invitation.invited_by)
    
    return render_template('view_invitation.html',
                         invitation=invitation,
                         folder=folder,
                         inviter=inviter,
                         token=token)

@app.route("/invite/<token>/accept", methods=["POST"])
def accept_invitation(token):
    """Accept an invitation"""
    invitation = CollabMember.query.filter_by(invite_token=token).first()
    
    if not invitation:
        flash("Invalid or expired invitation", "error")
        return redirect("/")
    
    # Check if user is logged in
    if not current_user.is_authenticated:
        # Store the token in session and redirect to login
        session['pending_invite_token'] = token
        return redirect(url_for('login', next=url_for('view_invitation', token=token)))
    
    # Verify this is the correct user
    if invitation.user_id != current_user.id:
        flash("This invitation is not for you", "error")
        return redirect("/collaborations")
    
    if invitation.invite_status != 'pending':
        flash("This invitation has already been processed", "info")
        return redirect("/collaborations")
    
    try:
        invitation.invite_status = 'accepted'
        invitation.invite_token = None
        invitation.joined_at = datetime.now()
        db.session.commit()
        
        flash(f"You've joined '{invitation.folder.name}' successfully! 🎉", "success")
        return redirect("/collaborations")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error accepting invitation: {str(e)}", "error")
        return redirect("/collaborations")

@app.route("/invite/<token>/decline", methods=["POST"])
def decline_invitation(token):
    """Decline an invitation"""
    invitation = CollabMember.query.filter_by(invite_token=token).first()
    
    if not invitation:
        flash("Invalid or expired invitation", "error")
        return redirect("/")
    
    # Similar logic for decline
    if not current_user.is_authenticated:
        session['pending_invite_token'] = token
        return redirect(url_for('login', next=url_for('view_invitation', token=token)))
    
    if invitation.user_id != current_user.id :
        flash("This invitation is not for you", "error")
        return redirect("/collaborations")
    
    try:
        invitation.invite_status = 'rejected'
        db.session.commit()
        
        flash("Invitation declined", "info")
        return redirect("/collaborations")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error declining invitation: {str(e)}", "error")
        return redirect("/collaborations")
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
