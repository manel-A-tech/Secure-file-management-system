from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss


app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'

# Initialize extensions
db = SQLAlchemy(app)
# If you plan to use Flask-Scss, initialize it here (optional)
# Scss(app)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<Account {self.id} - {self.username}>"


@app.route("/")
def home():
    accounts = Account.query.order_by(Account.id).all()
    return render_template('index.html', accounts=accounts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not email or not password:
            flash('Please fill in all fields')
            return render_template('registration.html')

        new_account = Account(username=username, email=email, password=password)
        try:
            db.session.add(new_account)
            db.session.commit()
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            return f"ERROR: {e}"

    return render_template('registration.html')


@app.route("/login")
def loging():
    # Keep the original template name if that's what you have on disk.
    return render_template("login.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
