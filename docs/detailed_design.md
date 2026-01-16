# ORCA Phase 2 - Detailed Technical Design

This document provides specific technical details for the implementation of ORCA Phase 2.

---

## 1. UI Architecture: Collapsible Sidebar

### Layout Structure (`layout.html`)
```html
<div class="app-container">
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <img src="/static/images/logo.svg" alt="ORCA">
            <span class="brand-name">ORCA</span>
            <button id="toggle-sidebar"><i class="icon-chevron-left"></i></button>
        </div>
        <nav class="sidebar-nav">
            <a href="/window" class="nav-item"><i class="icon-dashboard"></i> <span>Outsourcing Window</span></a>
            <a href="/glop-report" class="nav-item"><i class="icon-report"></i> <span>GLOP Report</span></a>
            <!-- ... other menus ... -->
        </nav>
    </aside>
    <main class="main-content">
        <header class="top-bar">
            <div class="page-title">Current Menu Name</div>
            <div class="user-profile">...</div>
        </header>
        <section class="content-area">
            {% block content %}{% endblock %}
        </section>
    </main>
</div>
```

---

## 2. Database Schema (SQLAlchemy)

### New Tables
```python
class Issue(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False) # HTML content
    author_id = Column(Integer, ForeignKey('users.id'))
    hashtags = Column(String(500)) # Stored as comma-separated string
    created_at = Column(DateTime, default=datetime.utcnow)

class StuffingData(Base):
    __tablename__ = 'stuffing_data'
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), unique=True)
    qty_20ft = Column(Integer)
    qty_40ft = Column(Integer)
    qty_40hc = Column(Integer)
```

---

## 3. Issue Board: Ctrl+V Image Handling

### Frontend Logic (`issue_board.js`)
1. Listen for `paste` event on the contenteditable area.
2. Iterate through `event.clipboardData.items`.
3. If item is an image:
   - Convert to Blob.
   - Check size (< 500KB).
   - Send to server via `/api/upload-image`.
   - Insert returned image URL into the editor.

### Backend Logic (`app.py`)
- Save image to `static/uploads/issues/YYYYMM/`.
- Generate unique filename (UUID).
- Return relative path for frontend display.

---

## 4. Generic Master Data Tool

### Dynamic Model Access
```python
@app.route('/api/master/<table_name>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_master_data(table_name):
    model = getattr(models, table_name, None)
    if not model:
        return jsonify({"error": "Table not found"}), 404
    
    # Generic CRUD logic using model.query
    # ...
```

---

## 5. Container Simulation Logic

### Calculation Formula
For each `ShipmentPlan` entry:
1. Match `Mapping_Model_Suffix` with `StuffingData.model_name`.
2. `Required_20FT = Plan_Qty / Qty_20FT`
3. `Required_40FT = Plan_Qty / Qty_40FT`
4. `Required_40HC = Plan_Qty / Qty_40HC`
5. Display results in a pivot-style table grouped by Week/Month.

---

## 6. Visualization Strategy

- **GLOP Report & Forecast**: Use `plotly.express.bar` and `plotly.express.line` for interactive time-series analysis.
- **SP Visualization**: Use `Chart.js` for lightweight, animated bar charts on the dashboard.
- **Data Aggregation**: Use Pandas `groupby` and `resample` on the backend to prepare JSON for Plotly.
