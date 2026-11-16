# Edor Peter's Memorial School — School Portal

A Django student portal for **Edor Peter's Memorial Secondary School**, Ogore-Ito, Obi LGA, Benue State.

Students sign in to view exam results — unlocked with a 12-digit scratch-card PIN — and to view and settle school fee invoices. Staff and administrators have their own areas, and `/admin/` provides full record management.

Everything runs locally. No internet connection or external service is required once the dependencies are installed.

| | |
|---|---|
| **Framework** | Django 5.2.19 |
| **Language** | Python 3.12 |
| **Database** | SQLite (`db.sqlite3`) |
| **Also required** | Pillow (student passport photographs) |

---

## Contents

- [Before you start](#before-you-start)
- [Project layout](#project-layout)
- [Setting it up](#setting-it-up)
- [Signing in](#signing-in)
- [Guided walkthrough](#guided-walkthrough)
- [Stopping and restarting](#stopping-and-restarting)
- [If something goes wrong](#if-something-goes-wrong)
- [Useful commands](#useful-commands)
- [Resetting to a clean state](#resetting-to-a-clean-state)
- [Known rough edges](#known-rough-edges)

---

## Before you start

| Requirement | Notes |
|---|---|
| **Python 3.12** | Check with `python3 --version`. Create the project's virtual environment using this Python version. |
| **Project folder** | `/home/student/school_portal` — all commands below are run from here. |
| **A web browser** | Chrome, Firefox or similar. |
| **Port 8000 free** | Django's development server binds to `127.0.0.1:8000` by default. |

> [!TIP]
> **Check your local environment first.** The `venv/` folder is created locally and is not included in Git. If it already contains Django and Pillow, skip Step 3 — otherwise create it and install the dependencies below.

---

## Project layout

You do not need to understand every file to run the app, but these are the ones that matter when something goes wrong.

```text
school_portal/
├── manage.py                  ← every command starts with this
├── db.sqlite3                 local database, created by migrate
├── venv/                      virtual environment with Django + Pillow
├── school_system/
│   ├── settings.py            ← ALLOWED_HOSTS, TIME_ZONE, database
│   └── urls.py                routes /admin/ and the portal
└── portal/
    ├── models.py              StudentProfile, ExamResult, SchoolFeeInvoice
    ├── views.py               ← the page logic
    ├── urls.py                /login/, /student/, /staff/, /portal-admin/
    ├── admin.py               Django admin configuration
    ├── signals.py             auto-creates a profile for each new user
    ├── templates/portal/      dashboard.html, home.html, login.html, …
    └── management/commands/
        └── seed_demo.py       ← creates the demo accounts
```

---

## Setting it up

### 1. Open a terminal in the project folder

```bash
cd /home/student/school_portal
```

Every command in this guide assumes you are in this folder.

### 2. Confirm the virtual environment is present

```bash
ls venv/bin/python
```

If that prints a path, you are ready — jump to **Step 4**. If it reports *No such file or directory*, do Step 3 first.

### 3. Rebuild the environment (only if Step 2 failed)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

> [!WARNING]
> **Pillow is not optional.** The student profile stores a passport photograph in an `ImageField`. Without Pillow, Django refuses to start and reports *Cannot use ImageField because Pillow is not installed*.

### 4. Create the database tables

```bash
./venv/bin/python manage.py migrate
```

This applies the four migrations in `portal/migrations/` and creates the local database and tables for student profiles, exam results and fee invoices. If you have already migrated this checkout, *No migrations to apply* is success.

### 5. Create the demo accounts

```bash
./venv/bin/python manage.py seed_demo
```

On success it prints:

```text
Student: demo.student / EPMdemo2026! | Result PIN: 123456789012
Administrator: demo.admin / AdminDemo2026!
```

It also creates four SS 2 subjects for the demo student and one unpaid fee invoice of **NGN 185,000.00**, so there is real data on screen.

> [!NOTE]
> **Safe to re-run.** The command uses `get_or_create`, so running it again will not duplicate records or wipe anything.

### 6. Start the server

```bash
./venv/bin/python manage.py runserver
```

Wait for the line `Starting development server at http://127.0.0.1:8000/`, then open that address in your browser. Leave this terminal running — it is the web server. You will need a second terminal for any other command.

> [!WARNING]
> **Use `127.0.0.1`, not `localhost`.** `localhost` usually works too, but the project's `ALLOWED_HOSTS` permits only `127.0.0.1`, `localhost` and `testserver`. Any other hostname — a machine name, an IP from another device — is rejected with a *DisallowedHost* error.

---

## Signing in

Open **http://127.0.0.1:8000/** and click **Portal login** in the top-right of the menu bar.

| Role | Username | Password |
|---|---|---|
| Student | `demo.student` | `EPMdemo2026!` |
| Administrator | `demo.admin` | `AdminDemo2026!` |

> [!NOTE]
> **Students can use their admission number or username.** For the demo student, enter `EPM/2026/0042` or `demo.student`, then the password `EPMdemo2026!`, and click **Log in**. Admission numbers accept upper- or lowercase letters. The result-checker PIN is used on the dashboard after login. Staff and administrators use their usernames on the same login page.

Use **Show password** to check what you typed. If you need your login details or a password reset, open the help section on the login page and visit the school ICT office.

Where each account lands after signing in:

| Account type | Redirected to |
|---|---|
| Student | `/student/` — the student dashboard |
| Staff (not superuser) | `/staff/` — the staff workspace |
| Superuser | `/portal-admin/` — the management overview |

---

## Guided walkthrough

### 1. The public home page

Before logging in you land on the school's marketing page — about the school, academic pathways, admissions. Click **Portal login** when you are ready.

### 2. The student dashboard

Sign in as `demo.student`. The dashboard has three metric cards (current class, outstanding balance, current term), then panels for results, fees and study materials.

Look at the **date in the top-right corner of the header**. It previously read `Friday, 21 August 2026` — a fixed string typed into the template when the project was built, so every student was shown that same stale date forever. It now reports the real current date and advances on its own:

| Before | After |
|---|---|
| `Friday, 21 August 2026` | Today's date, e.g. `Monday, 14 September 2026` |

The timezone was also corrected from UTC to `Africa/Lagos`, so the date is Nigeria local time rather than an hour behind — which also fixes the "Date issued" column in the fees table.

### 3. Unlock the exam results

In the **Academic results** panel, type the result-checker PIN `123456789012` and press **Check result**. The table unlocks with four SS 2 subjects, each showing CA score out of 30, exam score out of 70 and the total, plus a print button.

- Try a **wrong** PIN first (for example `000000000000`) to see the red scratch-card error.
- The results are never sent to the browser until the PIN matches — the check happens on the server.
- Reloading the page re-locks the results and asks for the PIN again. The PIN is not remembered between page loads.

### 4. Fees & payments

The **Outstanding balance** card shows **NGN 185000.00**, matching the single unpaid invoice below it. Each unpaid invoice carries a **Pay now** button.

> [!WARNING]
> **This button does not take money.** "Pay now" marks the invoice as paid immediately and writes a fabricated reference such as `EPM-DEMO-20260914…`. There is no payment gateway behind it. It is a deliberate placeholder — the view and URL are both named `demo_payment` — but be aware that anyone with a student login can clear a fee balance with one click. Press it to see the balance fall to NGN 0.

### 5. Enter and update student details

Sign out, then sign in as `demo.admin`. The administrator lands on `/portal-admin/`, which lists the school's actual student records.

1. Click **Add student**.
2. Fill in **Personal details**: first name and surname are required. Middle name, date of birth, email and passport photograph are optional.
3. Fill in **School details**: enter a unique admission number and choose the class.
4. Set the **Login password**. The optional **Result-checker PIN** must contain exactly 12 digits.
5. Click **Save student**. This creates the account and student profile together. Give the student their admission number and password so they can log in.

To make corrections, search by name or admission number and click **Edit details**. Leave **New login password** blank to keep the current password, or enter a new one to reset it. Click **Save changes** when finished. The links below the form open exam-result and fee-invoice entry with the student selected.

Passport photographs are saved under `media/` and can be opened by the student who owns the photograph or a school administrator. Staff accounts continue to use `/staff/`, whose schedule and figures remain placeholders.

### 6. The Django admin

Visit **http://127.0.0.1:8000/admin/** as `demo.admin`. From here you can add and edit students, record exam results, post fee invoices and upload passport photographs.

---

## Stopping and restarting

In the terminal running the server, press **Ctrl + C** to stop it. To start it again, re-run `./venv/bin/python manage.py runserver` — the database keeps your data between runs, so you do not need to re-run `migrate` or `seed_demo`.

Because the server auto-reloads when you save a Python file, most edits take effect without a restart. Template changes appear on the next page refresh.

---

## If something goes wrong

| Message | What to do |
|---|---|
| `DisallowedHost` at `/` | You used a hostname other than `127.0.0.1` or `localhost`. Use `http://127.0.0.1:8000/`, or add your hostname to `ALLOWED_HOSTS` in `school_system/settings.py`. |
| `ModuleNotFoundError: No module named 'django'` | You ran plain `python` instead of the environment's interpreter. Every command must start with `./venv/bin/python`. |
| `Cannot use ImageField because Pillow is not installed` | Install it: `./venv/bin/pip install Pillow`. |
| `no such table: portal_studentprofile` | The migrations have not been applied. Run `./venv/bin/python manage.py migrate`. |
| `That port is already in use` | Another server is still running. Stop it with Ctrl + C in its terminal, or start on a different port: `./venv/bin/python manage.py runserver 8001`. |
| `No time zone found with key Africa/Lagos` | The system timezone database is missing. Install it with `sudo apt install tzdata`. |
| Login rejected with the demo credentials | The accounts may not exist yet, or the password was changed. Re-run `./venv/bin/python manage.py seed_demo` to reset them to the documented values. |
| Styling looks broken or unstyled | Static files failed to load. Confirm `portal/static/portal/site.css` exists and restart the server. |

---

## Useful commands

| Command | Purpose |
|---|---|
| `./venv/bin/python manage.py check` | Reports configuration and model errors without starting the server. |
| `./venv/bin/python manage.py makemigrations --check --dry-run` | Confirms the migrations match the models. Should print *No changes detected*. |
| `./venv/bin/python manage.py seed_demo` | Creates or resets the demo student and administrator. |
| `./venv/bin/python manage.py createsuperuser` | Makes a fresh administrator account of your own. |
| `./venv/bin/python manage.py shell` | Interactive Python console with the models loaded. |

---

## Resetting to a clean state

If the database becomes cluttered and you want to start over, delete it and rebuild. This **erases all data** you have entered.

```bash
rm db.sqlite3
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_demo
```

---

## Known rough edges

These are real limitations of the project as it stands, listed so they are not mistaken for bugs in your setup.

| Area | Issue |
|---|---|
| **Fee payment** | The "Pay now" button clears an invoice without taking payment. The view and URL are both named `demo_payment`; a real gateway (Paystack, Flutterwave, Remita) still needs to be wired in. |
| **Staff profiles** | `seed_demo.py` creates `demo.admin` and *then* promotes it to staff, so the `post_save` guard in `signals.py` has already given it a student profile. Administrators can end up with phantom student records and bogus admission numbers. |
| **Logout** | `/logout/` is a plain GET link with no `@login_required`, so it can be triggered by a cross-site request. |
| **Session scoping** | The dashboard's results query filters by student only, not by term or session, so a student with several terms of results sees them all in one table. |
| **Tests** | Login and student management have automated coverage in `portal/tests.py`; dashboard results and fee payments still need coverage. |
| **Deployment** | `DEBUG = True` and `SECRET_KEY` is committed in `settings.py`. Both must change before this is exposed to the internet. |

---

*Edor Peter's Memorial Secondary School — school portal operator's guide. Updated 16 November 2026 for Django 5.2.19 on Python 3.12.*
