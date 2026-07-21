"""
models.py
---------
SQLAlchemy ORM models representing the MySQL database schema:
    users, categories, income, expenses, budgets
"""

from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    monthly_budget = db.Column(db.Numeric(12, 2), default=0)
    dark_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    incomes = db.relationship("Income", backref="user", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    """Categories for both income and expense transactions."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    icon = db.Column(db.String(50), default="bi-tag")  # bootstrap icon class
    is_default = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # null = global/default

    __table_args__ = (
        db.UniqueConstraint("name", "type", "user_id", name="uq_category_name_type_user"),
    )

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": float(self.amount),
            "category": self.category.name if self.category else "Uncategorized",
            "date": self.date.strftime("%Y-%m-%d"),
            "notes": self.notes or "",
            "type": "income",
        }


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(255))
    receipt_image = db.Column(db.String(255))  # filename stored in static/images/receipts
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # weekly / monthly / yearly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": float(self.amount),
            "category": self.category.name if self.category else "Uncategorized",
            "date": self.date.strftime("%Y-%m-%d"),
            "notes": self.notes or "",
            "receipt_image": self.receipt_image,
            "is_recurring": self.is_recurring,
            "type": "expense",
        }


DEFAULT_EXPENSE_CATEGORIES = [
    ("Food", "bi-cup-hot"),
    ("Transport", "bi-bus-front"),
    ("Shopping", "bi-bag"),
    ("Bills", "bi-receipt"),
    ("Entertainment", "bi-film"),
    ("Healthcare", "bi-heart-pulse"),
    ("Education", "bi-book"),
    ("Others", "bi-three-dots"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "bi-cash-stack"),
    ("Freelance", "bi-laptop"),
    ("Business", "bi-briefcase"),
    ("Investment", "bi-graph-up-arrow"),
    ("Gift", "bi-gift"),
    ("Others", "bi-three-dots"),
]


def seed_default_categories():
    """Insert the fixed default categories if they do not already exist."""
    for name, icon in DEFAULT_EXPENSE_CATEGORIES:
        if not Category.query.filter_by(name=name, type="expense", user_id=None).first():
            db.session.add(Category(name=name, type="expense", icon=icon, is_default=True))
    for name, icon in DEFAULT_INCOME_CATEGORIES:
        if not Category.query.filter_by(name=name, type="income", user_id=None).first():
            db.session.add(Category(name=name, type="income", icon=icon, is_default=True))
    db.session.commit()
