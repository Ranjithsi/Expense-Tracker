"""
extensions.py
-------------
Instantiate Flask extensions here (without binding to an app) so that
models.py, routes.py and app.py can all import the same instances
without causing circular-import problems.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
login_manager.login_message = "Please log in to access this page."
