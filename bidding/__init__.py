import logging
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
from datetime import datetime
import os
import secrets
from flask_migrate import Migrate


load_dotenv()
from pathlib import Path

# adding JWT other app
db_pass = os.getenv('DBPASS')
db_user = os.getenv("DBUSER")
db_host = os.getenv("DBHOST")
db = os.getenv("DB")
project_dir = os.getenv("PROJECT_DIR")
image_path = os.getenv("IMAGE_PATH")

app = Flask(__name__)
home = app.instance_path
app.config["SECRET_KEY"] = secrets.token_hex()
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:3306/{db}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = f"{home}/noqueue/uploads"

try:
    db = SQLAlchemy(app)
    Migrate(app,db)
except sqlalchemy.exc.ProgrammingError as e:
    print("error", e)

ma = Marshmallow(app)

# init bcrypt
bcrypt = Bcrypt(app)



# init the login manager
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# setting the config options for mail
app.config["MAIL_USERNAME"] = "denniskiruku@gmail.com"
app.config["MAIL_PASSWORD"] = "*****"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_PORT"] = 587

mail = Mail()

# print(app.instance_path)
from bidding import routes
