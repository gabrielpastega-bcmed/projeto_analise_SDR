# Authentication System - Quick Start Guide

**Version**: 1.0.0
**Project**: SDR Analytics Dashboard

---

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
poetry install
```

### 2. Configure Database (.env)
```bash
AUTH_DATABASE_HOST=your-postgres-host.railway.app
AUTH_DATABASE_PORT=5432
AUTH_DATABASE_NAME=railway
AUTH_DATABASE_USER=postgres
AUTH_DATABASE_PASSWORD=your-password
```

### 3. Initialize Database
```bash
poetry run python -m database.init_users
```

### 4. Start Dashboard
```bash
streamlit run dashboard.py
```

### 5. Login
- Username: `admin1`
- Password: `Admin@123!`

⚠️ **Change password immediately!**

---

## 📚 Features

### For All Users
- ✅ Secure login/logout
- ✅ View all dashboard pages
- ✅ Export PDF reports

### For Superadmins Only
- ✅ Create new users
- ✅ Manage existing users
- ✅ View audit logs
- ✅ Activate/deactivate accounts

---

## 🔒 Security

**Password Requirements**:
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, symbols recommended

**Best Practices**:
- Change default passwords immediately
- Never share credentials
- Use unique passwords per user
- Review audit logs regularly

---

## 🆘 Troubleshooting

### Cannot Login
1. Check user is active (Admin Panel → Users)
2. Verify password is correct
3. Check database connection in `.env`

### Cannot Access Admin Panel
- Only superadmins can access
- Check your role with another superadmin

### PDF Export Fails
```bash
poetry add kaleido reportlab
```

### Database Connection Error
- Use **public** hostname, not `.internal`
- Verify database is running
- Check firewall rules

---

## 📖 Full Documentation

For complete documentation, see:
- API Reference
- Database Schema
- Security Best Practices
- Advanced Configuration

**Contact**: System Administrator

---

**Version**: 1.0.0
**Last Updated**: 2025-12-18
