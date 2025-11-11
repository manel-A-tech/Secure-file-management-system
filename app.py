from enum import unique
from os import access
from flask import Flask, flash, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'

db = SQLAlchemy(app)

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

    def __repr__(self) -> str:
        return f"account{self.id},{self.username}"


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
    new_account = Account(username=username, email=email,
                          password=encrypted_pass)
    db.session.add(new_account)
    db.session.commit()

# home page


@app.route("/")
def home():
    return render_template('index.html')

# dassboard for logged in users only(protected)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

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
            create_new_account(username, email, password)
            flash("Account created successfully! Please login.", "success")
            return redirect("/login")
        except Exception as e:
            db.session.rollback()
            flash(f"error in creating the account :{e}", "error")
            return redirect("/register")

    else:  # for the get request
        return render_template('registration.html')

# to view all accounts for the admin


@app.route("/accounts")
@login_required
def view_accounts():
    accounts = Account.query.order_by(Account.id).all()
    return render_template('accounts.html', accounts=accounts)

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

# delete an account by the id


@app.route("/delete/<int:id>")
@login_required
def delete(id: int):
    if current_user.id != id:
        flash("You can only delete your own account", "error")
        return redirect("/dashboard")
    delete_account = Account.query.get_or_404(id)
    try:
        db.session.delete(delete_account)
        db.session.commit()
        logout_user()
        flash("Account deleted successfullt", "success")
        return redirect("/register")
    except Exception as e:
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
        if new_password:
            account.password = encrypt_password(new_password)
        try:
            db.session.commit()
            flash("Account updated successfully", "success")
            return redirect("/dashboard")
        except Exception as e:
            db.session.rollback()
            flash(f"error{e}", "error")
            return redirect("/register")
    else:
        return render_template("edit.html", account=account)


# add a method to check the password confirmation
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
