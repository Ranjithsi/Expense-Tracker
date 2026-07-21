"""
app.py
------
Application factory and entry point for the Expense Tracker.
Run with:  python app.py
"""

import os
from flask import Flask
from config import config_by_name
from extensions import db, bcrypt, login_manager, csrf


def create_app(env=None):
    app = Flask(__name__)
    env = env or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env, config_by_name["development"]))

    # --- init extensions ---
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # make sure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- register blueprints ---
    from routes import auth_bp, main_bp, income_bp, expense_bp, reports_bp, register_error_handlers
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(reports_bp)
    register_error_handlers(app)

    # --- template globals ---
    @app.context_processor
    def inject_globals():
        from datetime import date
        return {"current_year": date.today().year}

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        from models import seed_default_categories
        db.create_all()
        seed_default_categories()
    app.run(debug=True, host="0.0.0.0", port=5000)
