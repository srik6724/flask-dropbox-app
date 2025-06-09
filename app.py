import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import dropbox
from dotenv import load_dotenv
from flask_mail import Mail, Message

load_dotenv()

# Dropbox setup
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# Flask app
app = Flask(__name__)
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Email setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # zephaiautomation@gmail.com
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Gmail App Password

mail = Mail(app)

@app.route('/upload', methods=['POST'])
def upload_file():
    user = request.form.get('user')
    email = request.form.get('email')  # optional field
    file = request.files.get('file')

    if not user or not file:
        return jsonify({"error": "Missing user or file"}), 400

    filename = secure_filename(file.filename)
    local_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(local_path)

    dropbox_path = f"/uploads/{user}/{filename}"

    try:
        with open(local_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        os.remove(local_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Send notification email
    try:
        msg = Message(
            subject=f"📁 New Upload from {user}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['zephaiautomation@gmail.com'],
            body=f"""
User: {user}
Email: {email or 'N/A'}
File: {filename}
Dropbox Path: {dropbox_path}
"""
        )
        mail.send(msg)
    except Exception as e:
        print(f"Email send failed: {e}")

    return jsonify({"message": f"File uploaded to Dropbox: {dropbox_path}"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
