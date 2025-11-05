
from enum import unique
from flask import Flask, flash, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'

db = SQLAlchemy(app)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:
        return f"account{self.id},{self.username}"


# checking if the account is in the database bu the id
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

# registration page


@app.route("/register", methods=["POST", "GET"])
def register():
    # add account
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
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

    else:  # to see all accounts
        accounts = Account.query.order_by(Account.id).all()
        return render_template('registration.html', accounts=accounts)
# login page


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        account = Account.query.filter_by(username=username).first()

        if account and check_password_hash(account.password, password):
            flash("login successful", "success")
            return redirect("/")
        else:
            flash("invalid username or password", "error")
            return redirect("/login")
    else:
        render_template('login.html')


# delete an account by the id
@app.route("/delete/<int:id>")
def delete(id: int):
    delete_account = Account.query.get_or_404(id)
    try:
        db.session.delete(delete_account)
        db.session.commit()
        flash("Account deleted successfullt", "success")
        return redirect("/register")
    except Exception as e:
        flash(f"error{e}", "error")
        return redirect("/register")


# edit an account in the database

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    account = Account.query.get_or_404(id)
    if request.method == "POST":  # send information
        account.username = request.form.get('username')
        account.email = request.form.get('email')
        new_password = request.form.get('password')
        if new_password:
            account.password = encrypt_password(new_password)
        try:
            db.session.commit()
            flash("Account updated successfully", "success")
            return redirect("/register")
        except Exception as e:
            db.session.rollback()
            flash(f"error{e}", "error")
            return redirect("/register")
    else:
        return render_template("/edit")


# add a method to check the password confirmation
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
