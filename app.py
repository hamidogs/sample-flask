from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# DigitalOcean Spaces konfigürasyonu
DO_SPACES_ACCESS_KEY = 'DO007MNNU87DAEDGHYM2'
DO_SPACES_SECRET_KEY = 'MM1BquBArjjYY4+aN2jOvzK3E2NtaN7eMNEDJhhQjTc'
DO_SPACES_BUCKET_NAME = 'oto'
DO_SPACES_REGION = 'fra1'

# Boto3 ile DigitalOcean Spaces'e bağlanma
s3 = boto3.client('s3',
                  endpoint_url=f'https://{DO_SPACES_REGION}.digitaloceanspaces.com',
                  aws_access_key_id=DO_SPACES_ACCESS_KEY,
                  aws_secret_access_key=DO_SPACES_SECRET_KEY)

# Yükleme klasörü
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Maksimum dosya boyutu: 50 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Dosya kontrolü
    if 'file' not in request.files:
        return render_template('index.html', error='Dosya seçilmedi.')

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error='Dosya adı boş olamaz.')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Dosya boyut kontrolü
        if len(file.read()) > MAX_CONTENT_LENGTH:
            return render_template('index.html', error='Dosya boyutu çok büyük.')

        # DigitalOcean Spaces'e dosyayı yükle
        file.seek(0)
        s3.upload_fileobj(file, DO_SPACES_BUCKET_NAME, filename)

        return render_template('index.html', success='Dosya başarıyla yüklendi.')

    else:
        return render_template('index.html', error='Desteklenmeyen dosya türü.')

if __name__ == '__main__':
    app.run(debug=True)
