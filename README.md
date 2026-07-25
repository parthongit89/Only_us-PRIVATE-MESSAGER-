# OnlyUs - Secure Private Invitation-Only Messaging Web Application

OnlyUs is a secure, private, invitation-only messaging application built with Flask, SQLAlchemy, PostgreSQL, Flask-SocketIO, and Jinja2 templates styled according to Figma designs in dark mode.

## Core Features
- **Invitation & Request Access Only**: Unapproved users remain in a `Pending` state until approved by an Owner or Administrator.
- **Admin Approval Portal (`admin.png`)**: Desktop dashboard to Accept, Reject, or Report incoming account registration applications in bulk or individually.
- **Role Control (`permit.png`)**: Manage system roles (Owner, Admin, Member/User).
- **Real-Time Messaging (`chats-user.png` & `chats-FEATURE.png`)**: SocketIO direct & group messaging with typing indicators, read receipts, and media attachments.
- **Dark Mode Aesthetic**: Custom dark theme design tokens matching provided Figma assets.
- **OTP Verification (`otp.png`)**: Two-factor OTP validation with SMTP email support.
- **Database Support**: Native PostgreSQL integration with automatic SQLite fallback for rapid local testing.

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Launch Application
```bash
python app.py
```
or
```bash
flask run
```

Access the application in your browser at `http://localhost:5000`.

## Pre-seeded Test Accounts
- **Owner Account**: `owner@onlyus.app` (Password: `OwnerPass123!`)
- **Admin Account**: `admin@onlyus.app` (Password: `AdminPass123!`)
- **User Accounts**: `alex@onlyus.app`, `sarah@onlyus.app` (Password: `UserPass123!`)
