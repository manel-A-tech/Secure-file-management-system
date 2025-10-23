from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, redirect, request, render_template
from flask_scss import Scss


app = Flask(__name__)


@app.route("/loging")
def index():
    return render_template("loging.html")


if __name__ == "__main__":
    app.run(debug=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'advanced programming project'
db = SQLAlchemy(app)


class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"account{self.id}"


@app.route("/", methods=["POST", "GET"])
def index():

    if request.method == "POST":
        current_account = request.form['']
        new_account = Accounts()
        try:
            db.session.add(new_account)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"
    else:
        accounts = Accounts.query.order_by(Accounts.id).all()
        return render_template('index.html', accounts=accounts)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
