# ORCA Expansion - Phase 2 Implementation Plan

## Overview
Transform ORCA into a comprehensive SCM platform with a modern sidebar layout, advanced data visualization (Plotly), an interactive issue board with image pasting, and a generic Master Data management tool.

---

## User Review Required

> [!IMPORTANT]
> **Security Policy Compliance**: Image uploads in the Issue Board will be handled exclusively via `Ctrl+V` (clipboard) to comply with the user's security policy.
> **Database Migration**: New columns (`contact`) and tables (`issues`, `comments`, `stuffing_data`) will be added to `mnt_data.db`.

---

## Proposed Changes

### 1. UI/UX Overhaul
- **Sidebar Layout**: Implement a collapsible left sidebar with icons for all 9 menus.
- **Responsive Design**: Ensure the sidebar works well on wide monitors and can be toggled to save space.
- **Theme**: Maintain the premium dark glassmorphism theme with whale accents.

### 2. Database Schema Updates (`models.py`)

#### [MODIFY] `User` Model
- Add `contact` (String) field.

#### [NEW] `Issue` & `Comment` Models
- `Issue`: id, title, content (HTML with embedded base64 or path-linked images), author_id, hashtags, created_at.
- `Comment`: id, issue_id, content, author_id, created_at.

#### [NEW] `StuffingData` Model
- id, model_name, qty_20ft, qty_40ft, qty_40hc.

### 3. Backend (Flask - `app.py`)
- **Generic CRUD API**: Create a route that handles dynamic table selection for Master Data management.
- **Visualization Endpoints**: Data aggregation routes for GLOP Report, Forecast, and SP Visualization.
- **Issue Board Logic**: Handle image saving to a local folder and hashtag parsing.
- **Container Simulation Logic**: Implement the calculation formula based on `StuffingData` and `ShipmentPlan`.

### 4. Frontend (Templates & JS)

#### [NEW] `templates/layout.html`
- Base template with the new sidebar structure.

#### [NEW] `templates/issue_board.html`
- Implementation of the board with pagination (20 items).
- `Ctrl+V` listener for image pasting into the editor.

#### [NEW] `templates/master_data.html`
- Generic table viewer/editor with pagination.

#### [NEW] `static/js/visualization.js`
- Plotly.js and Chart.js integration for all report pages.

---

## Menu Implementation Details

| Menu | Title | Description | Tech |
|------|-------|-------------|------|
| 1 | Outsourcing Window | High-level dashboard (Placeholder for now) | Plotly |
| 2 | GLOP Report | `shipment_data` analysis (Annual/Monthly/Weekly) | Plotly/Table |
| 3 | Forecast | `shipment_plans` analysis (Quarterly/Monthly/Weekly) | Plotly/Table |
| 4 | SP Visualization | `planweek` vs SP quantity bar charts | Chart.js |
| 5 | Container Simulation | Prediction based on `StuffingData` | Logic/Table |
| 6 | Issue Board | Collaborative board with image pasting & hashtags | JS/SQL |
| 7 | My Page | User profile management | Form |
| 8 | Master Data | Generic CRUD for all master tables | Generic UI |
| 9 | Admin Page | User approval (Existing) | Table |

---

## Verification Plan

### Automated Tests
- Test dynamic CRUD API with different table names.
- Verify image size limit (500KB) enforcement in JS.

### Manual Verification
1. Verify sidebar toggle functionality.
2. Test `Ctrl+V` image pasting in the Issue Board.
3. Check pagination on Master Data and Issue Board.
4. Validate Container Simulation results against manual calculations.
