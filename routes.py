"""
routes.py
---------
All application routes, organized into Flask Blueprints:
    auth      -> register, login, logout, profile, change password
    main      -> dashboard, dark mode toggle, chart data API
    income    -> CRUD for income
    expense   -> CRUD for expenses, receipt upload
    reports   -> monthly/yearly reports, CSV/PDF export
"""

import os
import csv
import io
from datetime import datetime, date
from calendar import month_name

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    jsonify, session, send_file, current_app, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import extract, func
from werkzeug.utils import secure_filename

from extensions import db, bcrypt, csrf
from models import User, Category, Income, Expense, seed_default_categories

auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)
income_bp = Blueprint("income", __name__, url_prefix="/income")
expense_bp = Blueprint("expense", __name__, url_prefix="/expense")
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def parse_date(value, default=None):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default or date.today()


def get_user_categories(cat_type):
    """Return default + user-created categories of the given type."""
    return Category.query.filter(
        Category.type == cat_type,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).order_by(Category.name).all()


# ----------------------------------------------------------------------
# AUTH BLUEPRINT
# ----------------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Simplified self-service password reset (no email server required).
    In production this would email a signed token link to the user."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "")
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email address.", "danger")
        elif len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
        else:
            user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
            db.session.commit()
            flash("Password reset successfully. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()

        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash("That email is already in use by another account.", "danger")
        else:
            current_user.full_name = full_name
            current_user.email = email
            db.session.commit()
            flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("profile.html")


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()
        flash("Password changed successfully.", "success")

    return redirect(url_for("auth.profile"))


@auth_bp.route("/budget", methods=["POST"])
@login_required
def set_budget():
    try:
        amount = float(request.form.get("monthly_budget", 0))
        if amount < 0:
            raise ValueError
        current_user.monthly_budget = amount
        db.session.commit()
        flash("Monthly budget updated.", "success")
    except ValueError:
        flash("Please enter a valid budget amount.", "danger")
    return redirect(url_for("auth.profile"))


# ----------------------------------------------------------------------
# MAIN BLUEPRINT (dashboard)
# ----------------------------------------------------------------------
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    today = date.today()

    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)) \
        .filter(Income.user_id == uid).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)) \
        .filter(Expense.user_id == uid).scalar()
    balance = float(total_income) - float(total_expense)

    # This month's totals (for budget alert)
    month_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == uid,
        extract("month", Expense.date) == today.month,
        extract("year", Expense.date) == today.year,
    ).scalar()

    budget_alert = None
    if current_user.monthly_budget and float(current_user.monthly_budget) > 0:
        pct = (float(month_expense) / float(current_user.monthly_budget)) * 100
        if pct >= 100:
            budget_alert = {"level": "danger", "pct": round(pct, 1),
                             "message": "You have exceeded your monthly budget!"}
        elif pct >= 80:
            budget_alert = {"level": "warning", "pct": round(pct, 1),
                             "message": "You are close to your monthly budget limit."}

    # Recent transactions (last 8, combined)
    recent_income = Income.query.filter_by(user_id=uid).order_by(Income.date.desc()).limit(8).all()
    recent_expense = Expense.query.filter_by(user_id=uid).order_by(Expense.date.desc()).limit(8).all()
    recent = sorted(
        [i.to_dict() for i in recent_income] + [e.to_dict() for e in recent_expense],
        key=lambda x: x["date"], reverse=True
    )[:8]

    # Monthly expense summary for current year (for bar chart)
    monthly_totals = [0] * 12
    rows = db.session.query(
        extract("month", Expense.date), func.sum(Expense.amount)
    ).filter(Expense.user_id == uid, extract("year", Expense.date) == today.year) \
     .group_by(extract("month", Expense.date)).all()
    for m, total in rows:
        monthly_totals[int(m) - 1] = float(total)

    # Category distribution (pie chart)
    cat_rows = db.session.query(Category.name, func.sum(Expense.amount)) \
        .join(Expense, Expense.category_id == Category.id) \
        .filter(Expense.user_id == uid) \
        .group_by(Category.name).all()
    category_labels = [r[0] for r in cat_rows]
    category_values = [float(r[1]) for r in cat_rows]

    return render_template(
        "dashboard.html",
        total_income=float(total_income),
        total_expense=float(total_expense),
        balance=balance,
        recent=recent,
        month_names=list(month_name)[1:],
        monthly_totals=monthly_totals,
        category_labels=category_labels,
        category_values=category_values,
        budget_alert=budget_alert,
        current_month_expense=float(month_expense),
    )


@main_bp.route("/api/income-vs-expense")
@login_required
def income_vs_expense_api():
    """JSON data for the Income vs Expense line chart (last 6 months)."""
    uid = current_user.id
    today = date.today()
    labels, income_vals, expense_vals = [], [], []

    y, m = today.year, today.month
    months = []
    for i in range(5, -1, -1):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        months.append((yy, mm))

    for yy, mm in months:
        labels.append(f"{month_name[mm][:3]} {yy}")
        inc = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.user_id == uid, extract("year", Income.date) == yy,
            extract("month", Income.date) == mm).scalar()
        exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == uid, extract("year", Expense.date) == yy,
            extract("month", Expense.date) == mm).scalar()
        income_vals.append(float(inc))
        expense_vals.append(float(exp))

    return jsonify({"labels": labels, "income": income_vals, "expense": expense_vals})


@main_bp.route("/toggle-dark-mode", methods=["POST"])
@login_required
def toggle_dark_mode():
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    return jsonify({"dark_mode": current_user.dark_mode})


# ----------------------------------------------------------------------
# INCOME BLUEPRINT
# ----------------------------------------------------------------------
@income_bp.route("/")
@login_required
def list_income():
    query = Income.query.filter_by(user_id=current_user.id)

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    month = request.args.get("month", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")

    if search:
        query = query.filter(Income.title.ilike(f"%{search}%"))
    if category:
        query = query.join(Category).filter(Category.name == category)
    if month:
        y, m = month.split("-")
        query = query.filter(extract("year", Income.date) == int(y),
                              extract("month", Income.date) == int(m))
    if start_date:
        query = query.filter(Income.date >= parse_date(start_date))
    if end_date:
        query = query.filter(Income.date <= parse_date(end_date))
    if min_amount:
        query = query.filter(Income.amount >= float(min_amount))
    if max_amount:
        query = query.filter(Income.amount <= float(max_amount))

    records = query.order_by(Income.date.desc()).all()
    categories = get_user_categories("income")
    return render_template("income_list.html", records=records, categories=categories)


@income_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_income():
    categories = get_user_categories("income")
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "")
        category_id = request.form.get("category_id")
        income_date = parse_date(request.form.get("date"))
        notes = request.form.get("notes", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Amount must be greater than zero.")
        except ValueError:
            errors.append("Amount must be a valid number.")
        if not category_id:
            errors.append("Please select a category.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("add_income.html", categories=categories, form=request.form)

        new_income = Income(user_id=current_user.id, category_id=category_id,
                             title=title, amount=amount, date=income_date, notes=notes)
        db.session.add(new_income)
        db.session.commit()
        flash("Income added successfully.", "success")
        return redirect(url_for("income.list_income"))

    return render_template("add_income.html", categories=categories, form={})


@income_bp.route("/edit/<int:income_id>", methods=["GET", "POST"])
@login_required
def edit_income(income_id):
    record = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    categories = get_user_categories("income")

    if request.method == "POST":
        record.title = request.form.get("title", "").strip()
        try:
            record.amount = float(request.form.get("amount"))
        except (TypeError, ValueError):
            flash("Amount must be a valid number.", "danger")
            return render_template("edit_income.html", record=record, categories=categories)
        record.category_id = request.form.get("category_id")
        record.date = parse_date(request.form.get("date"))
        record.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Income updated successfully.", "success")
        return redirect(url_for("income.list_income"))

    return render_template("edit_income.html", record=record, categories=categories)


@income_bp.route("/delete/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    record = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    flash("Income deleted.", "info")
    return redirect(url_for("income.list_income"))


# ----------------------------------------------------------------------
# EXPENSE BLUEPRINT
# ----------------------------------------------------------------------
@expense_bp.route("/")
@login_required
def list_expense():
    query = Expense.query.filter_by(user_id=current_user.id)

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    month = request.args.get("month", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")

    if search:
        query = query.filter(Expense.title.ilike(f"%{search}%"))
    if category:
        query = query.join(Category).filter(Category.name == category)
    if month:
        y, m = month.split("-")
        query = query.filter(extract("year", Expense.date) == int(y),
                              extract("month", Expense.date) == int(m))
    if start_date:
        query = query.filter(Expense.date >= parse_date(start_date))
    if end_date:
        query = query.filter(Expense.date <= parse_date(end_date))
    if min_amount:
        query = query.filter(Expense.amount >= float(min_amount))
    if max_amount:
        query = query.filter(Expense.amount <= float(max_amount))

    records = query.order_by(Expense.date.desc()).all()
    categories = get_user_categories("expense")
    return render_template("expense_list.html", records=records, categories=categories)


@expense_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_expense():
    categories = get_user_categories("expense")
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "")
        category_id = request.form.get("category_id")
        expense_date = parse_date(request.form.get("date"))
        notes = request.form.get("notes", "").strip()
        is_recurring = bool(request.form.get("is_recurring"))
        recurring_frequency = request.form.get("recurring_frequency") if is_recurring else None

        errors = []
        if not title:
            errors.append("Title is required.")
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Amount must be greater than zero.")
        except ValueError:
            errors.append("Amount must be a valid number.")
        if not category_id:
            errors.append("Please select a category.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("add_expense.html", categories=categories, form=request.form)

        receipt_filename = None
        file = request.files.get("receipt")
        if file and file.filename and allowed_file(file.filename):
            receipt_filename = secure_filename(f"user{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], receipt_filename))

        new_expense = Expense(user_id=current_user.id, category_id=category_id,
                               title=title, amount=amount, date=expense_date, notes=notes,
                               receipt_image=receipt_filename, is_recurring=is_recurring,
                               recurring_frequency=recurring_frequency)
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added successfully.", "success")
        return redirect(url_for("expense.list_expense"))

    return render_template("add_expense.html", categories=categories, form={})


@expense_bp.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    record = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    categories = get_user_categories("expense")

    if request.method == "POST":
        record.title = request.form.get("title", "").strip()
        try:
            record.amount = float(request.form.get("amount"))
        except (TypeError, ValueError):
            flash("Amount must be a valid number.", "danger")
            return render_template("edit_expense.html", record=record, categories=categories)
        record.category_id = request.form.get("category_id")
        record.date = parse_date(request.form.get("date"))
        record.notes = request.form.get("notes", "").strip()
        record.is_recurring = bool(request.form.get("is_recurring"))
        record.recurring_frequency = request.form.get("recurring_frequency") if record.is_recurring else None

        file = request.files.get("receipt")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"user{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            record.receipt_image = filename

        db.session.commit()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expense.list_expense"))

    return render_template("edit_expense.html", record=record, categories=categories)


@expense_bp.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    record = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expense.list_expense"))


# ----------------------------------------------------------------------
# REPORTS BLUEPRINT
# ----------------------------------------------------------------------
@reports_bp.route("/")
@login_required
def reports():
    uid = current_user.id
    today = date.today()
    report_type = request.args.get("type", "monthly")
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    if report_type == "monthly":
        income_q = Income.query.filter(Income.user_id == uid,
                                        extract("year", Income.date) == year,
                                        extract("month", Income.date) == month)
        expense_q = Expense.query.filter(Expense.user_id == uid,
                                          extract("year", Expense.date) == year,
                                          extract("month", Expense.date) == month)
    else:  # yearly
        income_q = Income.query.filter(Income.user_id == uid, extract("year", Income.date) == year)
        expense_q = Expense.query.filter(Expense.user_id == uid, extract("year", Expense.date) == year)

    total_income = sum(float(i.amount) for i in income_q.all())
    total_expense = sum(float(e.amount) for e in expense_q.all())
    savings = total_income - total_expense

    # Category-wise spending
    cat_totals = {}
    for e in expense_q.all():
        cat_name = e.category.name if e.category else "Others"
        cat_totals[cat_name] = cat_totals.get(cat_name, 0) + float(e.amount)
    category_breakdown = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    highest_category = category_breakdown[0] if category_breakdown else ("N/A", 0)

    years_available = sorted({d.year for d in
                               [i.date for i in Income.query.filter_by(user_id=uid).all()] +
                               [e.date for e in Expense.query.filter_by(user_id=uid).all()]} | {today.year},
                              reverse=True)

    return render_template(
        "reports.html",
        report_type=report_type, year=year, month=month,
        total_income=total_income, total_expense=total_expense, savings=savings,
        category_breakdown=category_breakdown, highest_category=highest_category,
        years_available=years_available, month_names=list(month_name)[1:],
        income_list=income_q.order_by(Income.date.desc()).all(),
        expense_list=expense_q.order_by(Expense.date.desc()).all(),
    )


@reports_bp.route("/export/csv")
@login_required
def export_csv():
    uid = current_user.id
    incomes = Income.query.filter_by(user_id=uid).order_by(Income.date.desc()).all()
    expenses = Expense.query.filter_by(user_id=uid).order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Title", "Category", "Amount", "Date", "Notes"])
    for i in incomes:
        writer.writerow(["Income", i.title, i.category.name, i.amount, i.date, i.notes or ""])
    for e in expenses:
        writer.writerow(["Expense", e.title, e.category.name, e.amount, e.date, e.notes or ""])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True,
                      download_name=f"transactions_{date.today()}.csv")


@reports_bp.route("/export/pdf")
@login_required
def export_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    uid = current_user.id
    incomes = Income.query.filter_by(user_id=uid).order_by(Income.date.desc()).all()
    expenses = Expense.query.filter_by(user_id=uid).order_by(Expense.date.desc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Expense Tracker Report - {current_user.username}", styles["Title"]),
                Spacer(1, 0.5 * cm)]

    total_income = sum(float(i.amount) for i in incomes)
    total_expense = sum(float(e.amount) for e in expenses)
    elements.append(Paragraph(
        f"Total Income: ₹{total_income:,.2f} | Total Expense: ₹{total_expense:,.2f} | "
        f"Balance: ₹{total_income - total_expense:,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    data = [["Type", "Title", "Category", "Amount", "Date"]]
    for i in incomes:
        data.append(["Income", i.title, i.category.name, f"₹{float(i.amount):,.2f}", str(i.date)])
    for e in expenses:
        data.append(["Expense", e.title, e.category.name, f"₹{float(e.amount):,.2f}", str(e.date)])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, mimetype="application/pdf", as_attachment=True,
                      download_name=f"transactions_{date.today()}.pdf")


# ----------------------------------------------------------------------
# Error handlers (registered on the blueprint level via app.py)
# ----------------------------------------------------------------------
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(e):
        flash("File is too large. Maximum upload size is 5MB.", "danger")
        return redirect(request.referrer or url_for("main.dashboard"))
