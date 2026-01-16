# ORCA - Outsourcing Resource & Control Application

## Overview
A modern web application for managing GLOP driver automation with user authentication and real-time log streaming.

---

## Created Files

### Backend
| File | Description |
|------|-------------|
| [models.py](file:///d:/MNT%20Shipment%20data%20server/server/models.py) | User, LoginHistory models added |
| [app.py](file:///d:/MNT%20Shipment%20data%20server/server/app.py) | Flask-Login, auth routes, SSE endpoint |

### Frontend Templates
| File | Description |
|------|-------------|
| [login.html](file:///d:/MNT%20Shipment%20data%20server/server/templates/login.html) | Whale-themed login/signup page |
| [dashboard.html](file:///d:/MNT%20Shipment%20data%20server/server/templates/dashboard.html) | GLOP Driver interface |
| [admin.html](file:///d:/MNT%20Shipment%20data%20server/server/templates/admin.html) | User management panel |

### Static Assets
| File | Description |
|------|-------------|
| [style.css](file:///d:/MNT%20Shipment%20data%20server/server/static/css/style.css) | Glassmorphism dark theme |
| [app.js](file:///d:/MNT%20Shipment%20data%20server/server/static/js/app.js) | SSE client for real-time logs |

---

## Features

### 🔐 Authentication
- User signup with pending status
- Admin approval workflow
- Login history tracking
- Password hashing with werkzeug

### 🐋 GLOP Driver Interface
- Product category selection (Monitor/PC)
- Supplier category selection (LGEKR/LGECH)
- **Actual Selenium Driver Integration**: Runs the real automation logic from `driver/main.py`.
- Real-time log streaming via SSE
- Status indicator

### 👥 Admin Panel
- User list with status badges
- Approve/Reject buttons
- User status management

---

## Running the Server

```bash
cd "d:\MNT Shipment data server"
.\.venv\Scripts\python server\app.py
```

**Access URLs:**
- Local: http://127.0.0.1:5000
- Network: http://10.21.108.69:5000

**Default Admin:**
- ID: `admin`
- Password: `admin123`

---

## Next Steps
- [ ] Integrate actual GLOP driver with SSE log queue
- [ ] Add login history view in admin panel
- [ ] Add password change functionality
