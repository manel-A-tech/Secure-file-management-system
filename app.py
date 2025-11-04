from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'
db = SQLAlchemy(app)


class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:
        return f"account{self.id}"


# checking if the account is in the database bu the id
def check_account_exists(id):
    account = Accounts.query.filter_by(id=id).first()
    if account:
        return True
    return False
# encryption

def encrypt_password(password):
    return generate_password_hash(password)

# creating a new account


def create_new_account(username, email, password):
    encrypted_pass = encrypt_password(password)
    new_account = Accounts(username=username, email=email,
                           password=encrypted_pass)
    db.session.add(new_account)
    db.session.commit()


@app.route("/", methods=["POST", "GET"])
def index():
    # add account
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if check_account_exists(username):
            return "ERROR: Account already exists"
        try:
            create_new_account(username, email, password)
            return redirect("/")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"
    else:  # to see all accounts
        accounts = Accounts.query.order_by(Accounts.id).all()
        # Changed: removed 'templates/' prefix
        return render_template('registration.html', accounts=accounts)


# delete an account by the id
@app.route("/delete/<int:id>")
def delete(id: int):
    delete_account = Accounts.query.get_or_404(id)
    try:
        db.session.delete(delete_account)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        print(f"ERROR: {e}")
        return f"ERROR: {e}"


# edit an account in the database

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    account = Accounts.query.get_or_404(id)
    if request.method == "POST":  # send information
        account.username = request.form['username']
        account.email = request.form['email']
        new_password = request.form.get('password')
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"


# add a method to check the password confirmation
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
