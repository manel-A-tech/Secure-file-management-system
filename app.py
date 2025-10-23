from flask import Flask , render_template
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

@app.route("/loging")
def index():
  return render_template("loging.html")


if __name__ == "__main__":
  app.run(debug=True)