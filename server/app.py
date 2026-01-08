from flask import Flask, request, jsonify
import pandas as pd
from database import init_db, upsert_dataframe, db_session
from models import ShipmentPlan
import logging
import socket

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
with app.app_context():
    init_db()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route('/upsert_shipment_plan', methods=['POST'])
def upsert_shipment_plan():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Rename columns to match model attributes
        df = df.rename(columns={
            'From Site': 'From_Site',
            'To Site': 'To_Site',
            'Mapping Model.Suffix': 'Mapping_Model_Suffix',
            'Rep PMS': 'Rep_PMS',
            'Week Name': 'Week_Name'
        })
        
        # Perform upsert
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
    print(f"\n * Server is running on:")
    print(f" * Local:   http://127.0.0.1:5000")
    print(f" * Network: http://{local_ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
