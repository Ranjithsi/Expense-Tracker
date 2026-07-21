# 💰 Expense Tracker

A full-stack personal finance web app built with **Flask**, **MySQL**, **Bootstrap 5**,
and **Chart.js**. Track income and expenses, visualize spending, set budgets, and
export reports to CSV/PDF.

---

## Features

- 🔐 **Auth** — registration, login/logout, bcrypt password hashing, session management, forgot password, change password
- 📊 **Dashboard** — total income / expenses / balance, recent transactions, monthly summary, budget alerts
- 💵 **Income & Expense CRUD** — add/edit/delete, categories, date picker, receipt image upload, recurring expenses
- 🔍 **Search & Filter** — by title, category, date range, month, amount range
- 📈 **Charts** — pie (category distribution), bar (monthly expenses), line (income vs expense)
- 🧾 **Reports** — monthly & yearly, category-wise spending, highest category, total savings
- 📤 **Export** — CSV and PDF
- 🌗 **Dark mode**, responsive Bootstrap 5 sidebar layout
- 🛡️ **Security** — bcrypt hashing, CSRF protection (Flask-WTF), SQLAlchemy ORM (SQL-injection safe), server-side validation

---

## Tech Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Backend    | Python, Flask, Flask-Login, Flask-Bcrypt, Flask-WTF |
| ORM        | SQLAlchemy (Flask-SQLAlchemy)        |
| Database   | MySQL (via PyMySQL driver)           |
| Frontend   | HTML, CSS, Bootstrap 5, Vanilla JS   |
| Charts     | Chart.js                             |
| PDF Export | ReportLab                            |

---

## Project Structure

```
ExpenseTracker/
│
├── app.py                # App factory & entry point
├── config.py              # Configuration (env-based)
├── extensions.py          # db, bcrypt, login_manager, csrf instances
├── models.py               # SQLAlchemy models (User, Category, Income, Expense)
├── routes.py               # All routes, organized as Blueprints
├── requirements.txt
├── .env.example
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/receipts/    # uploaded receipt images
├── templates/
│   ├── base.html
│   ├── login.html / register.html / forgot_password.html
│   ├── dashboard.html
│   ├── add_income.html / edit_income.html / income_list.html
│   ├── add_expense.html / edit_expense.html / expense_list.html
│   ├── reports.html
│   ├── profile.html
│   ├── partials/_flash.html
│   └── errors/404.html, 500.html
└── database/
    └── schema.sql          # MySQL schema + default category seed data
```

---

## Installation

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (or MariaDB)

### 2. Clone & set up a virtual environment
```bash
cd ExpenseTracker
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and set your MySQL credentials and a strong `SECRET_KEY`.

### 4. Create the database
Option A — let SQLAlchemy create the tables automatically:
```bash
mysql -u root -p -e "CREATE DATABASE expense_tracker CHARACTER SET utf8mb4;"
python app.py    # creates tables + seeds default categories on first run
```

Option B — run the provided schema file directly:
```bash
mysql -u root -p < database/schema.sql
```

### 5. Run the app
```bash
python app.py
```
Visit **http://localhost:5000** in your browser.

---

## Default Expense Categories
Food · Transport · Shopping · Bills · Entertainment · Healthcare · Education · Others

## Default Income Categories
Salary · Freelance · Business · Investment · Gift · Others

---

## Security Notes
- Passwords are hashed with **bcrypt** (`flask-bcrypt`) — never stored in plain text.
- All forms are protected against **CSRF** via `Flask-WTF`'s `CSRFProtect`.
- All database access goes through the **SQLAlchemy ORM**, which parameterizes
  queries and prevents SQL injection.
- Server-side input validation on every form (client-side `required`/`minlength`
  attributes are a UX convenience only, not a security boundary).
- File uploads are restricted by extension and size (5 MB max) and saved with
  `secure_filename()`.

## Notes on Optional Items
- **Email verification** was intentionally left out of the default flow (marked
  optional in the spec) to avoid requiring an SMTP server; `forgot_password.html`
  implements a simplified self-service reset instead. Swap in Flask-Mail +
  `itsdangerous` tokens for production-grade email verification/reset.
- **Recurring expenses** are tracked via `is_recurring` / `recurring_frequency`
  fields; wire up a scheduler (e.g. APScheduler or a cron job calling a Flask
  CLI command) to auto-generate the next occurrence if you want full automation.

---

## License
Provided as-is for learning/demo purposes. Adapt freely for your own projects.
