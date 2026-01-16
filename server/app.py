from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
from database import init_db, upsert_dataframe, db_session, engine
from models import ShipmentPlan, User, LoginHistory
import logging
import socket
import json
import queue
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'orca-secret-key-2026'  # Change in production

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message = '로그인이 필요합니다.'

@login_manager.user_loader
def load_user(user_id):
    return db_session.query(User).get(int(user_id))

# Make User class compatible with Flask-Login
User.is_authenticated = property(lambda self: True)
User.is_active = property(lambda self: self.status == 'active')
User.is_anonymous = property(lambda self: False)
User.get_id = lambda self: str(self.id)

# Initialize database
with app.app_context():
    init_db()
    # Create default admin if not exists
    admin = db_session.query(User).filter_by(userid='admin').first()
    if not admin:
        admin = User(
            userid='admin',
            email='admin@orca.local',
            team='Admin',
            company='ORCA',
            status='active',
            is_admin=True
        )
        admin.set_password('admin123')
        db_session.add(admin)
        db_session.commit()
        logger.info("Default admin user created: admin / admin123")

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    userid = request.form.get('userid')
    password = request.form.get('password')
    
    user = db_session.query(User).filter_by(userid=userid).first()
    
    if user and user.check_password(password):
        if user.status != 'active':
            flash('계정이 아직 승인되지 않았습니다. 관리자에게 문의하세요.', 'warning')
            return redirect(url_for('login_page'))
        
        login_user(user)
        
        # Record login history
        history = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr
        )
        db_session.add(history)
        db_session.commit()
        
        flash(f'{user.userid}님, 환영합니다!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('잘못된 사용자 ID 또는 비밀번호입니다.', 'error')
        return redirect(url_for('login_page'))

@app.route('/signup', methods=['POST'])
def signup():
    userid = request.form.get('userid')
    password = request.form.get('password')
    email = request.form.get('email')
    team = request.form.get('team')
    company = request.form.get('company')
    
    # Check if user already exists
    existing = db_session.query(User).filter_by(userid=userid).first()
    if existing:
        flash('이미 사용 중인 사용자 ID입니다.', 'error')
        return redirect(url_for('login_page'))
    
    # Create new user
    user = User(
        userid=userid,
        email=email,
        team=team,
        company=company,
        status='pending'
    )
    user.set_password(password)
    
    db_session.add(user)
    db_session.commit()
    
    flash('회원가입이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다.', 'success')
    return redirect(url_for('login_page'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('dashboard'))
    
    users = db_session.query(User).all()
    return render_template('admin.html', users=users)

@app.route('/admin/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = db_session.query(User).get(user_id)
    if user:
        user.status = 'active'
        db_session.commit()
        flash(f'{user.userid} 사용자가 승인되었습니다.', 'success')
    
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = db_session.query(User).get(user_id)
    if user:
        user.status = 'rejected'
        db_session.commit()
        flash(f'{user.userid} 사용자가 비활성화되었습니다.', 'warning')
    
    return redirect(url_for('admin'))

# ==================== GLOP DRIVER SSE ====================

# Global queue for log messages
log_queues = {}

@app.route('/api/drive_glop')
@login_required
def drive_glop():
    product = request.args.get('product', 'monitor')
    supplier = request.args.get('supplier', 'LGEKR')
    user_id = current_user.id
    
    def generate():
        q = queue.Queue()
        session_id = f"{user_id}_{datetime.now().timestamp()}"
        log_queues[session_id] = q
        
        # Start driver in background thread
        thread = threading.Thread(
            target=run_glop_driver,
            args=(product, supplier, q)
        )
        thread.start()
        
        try:
            while True:
                try:
                    msg = q.get(timeout=120)
                    if msg is None:
                        break
                    yield f"data: {json.dumps(msg)}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            if session_id in log_queues:
                del log_queues[session_id]
    
    return Response(generate(), mimetype='text/event-stream')

def run_glop_driver(product, supplier, log_queue):
    """Run GLOP driver and send logs to queue"""
    try:
        log_queue.put({'type': 'log', 'message': f'GLOP Driver 시작: Product={product}, Supplier={supplier}'})
        log_queue.put({'type': 'status', 'message': '실행 중', 'status': 'pending'})
        
        # Import and run driver
        import sys
        import os
        driver_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'driver')
        if driver_dir not in sys.path:
            sys.path.insert(0, driver_dir)
        
        from main import main as drive_main
        
        # 실제 드라이버 실행
        drive_main(product_category=product, supplier_category=supplier, log_queue=log_queue)
        
        log_queue.put({'type': 'complete'})
        
    except Exception as e:
        log_queue.put({'type': 'error', 'message': f"드라이버 실행 중 오류 발생: {str(e)}"})
    finally:
        log_queue.put(None)

# ==================== API ROUTES ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "ORCA Server is running"}), 200

@app.route('/upsert_shipment_plan', methods=['POST'])
def upsert_shipment_plan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        df = pd.DataFrame(data)
        
        df = df.rename(columns={
            'From Site': 'From_Site',
            'To Site': 'To_Site',
            'Mapping Model.Suffix': 'Mapping_Model_Suffix',
            'Rep PMS': 'Rep_PMS',
            'Week Name': 'Week_Name'
        })
        
        row_count = upsert_dataframe(df, ShipmentPlan)

        return jsonify({
            "message": "Upsert successful",
            "rows_affected": row_count
        }), 200

    except Exception as e:
        logger.error(f"Error during upsert: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n🐋 ORCA Server Starting...")
    print(f" * Local:   http://127.0.0.1:5000")
    print(f" * Network: http://{local_ip}:5000")
    print(f" * Default Admin: admin / admin123\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
