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
            category=category
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
            temp_path = file_manager.creat_temp_file(
                decrypted_data, file_record.original_filename)
            flash(f"Shared file accessed successfully!", "success")
            return send_file(temp_path,
                             as_attachment=True,
                             download_name=file_record.original_filename)
        except Exception as e:
            flash(f"Error eccessing file: {str(e)}", "error")
            return render_template('access_shared.html')
    return render_template('access_shared.html')

# access accounts


@app.route("/accounts")
@login_required
def view_accounts():
    accounts = Account.query.order_by(Account.id).all()
    return render_template('accounts.html', accounts=accounts)

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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
