from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename
import os
from datetime import datetime

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


from flask import request

@app.route('/upload', methods=['POST'])
def upload_files():
    kullanici_telefon_no = 5554443322
    # Dosya kontrolü
    if 'files' not in request.files:
        return render_template('index.html', error='Dosya seçilmedi.')

    files = request.files.getlist('files')

    for file in files:
        if file.filename == '':
            return render_template('index.html', error='Dosya adı boş olamaz.')

        if file and allowed_file(file.filename):
            # Zaman damgası oluştur
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Klasör yapısı oluştur
            today_folder = datetime.now().strftime('%Y%m%d')
            user_folder = f"{kullanici_telefon_no}"

            # Dosya adına zaman damgasını ve klasör yapısını ekle
            filename_with_timestamp = f"{today_folder}/{user_folder}/{timestamp}_{secure_filename(file.filename)}"

            # Dosya boyut kontrolü
            if len(file.read()) > MAX_CONTENT_LENGTH:
                return render_template('index.html', error='Dosya boyutu çok büyük.')

            # Dosyayı DigitalOcean Spaces'e yükle
            file.seek(0)
            s3.upload_fileobj(file, DO_SPACES_BUCKET_NAME, filename_with_timestamp)

    return render_template('index.html', success='Dosyalar başarıyla yüklendi.')


@app.route('/show_image')
def show_image():
    # URL'den dosya adını al
    file_name = request.args.get('file_name', '')

    # Dosyaya erişim URL'si oluştur
    file_url = get_presigned_url(DO_SPACES_BUCKET_NAME, file_name)

    return render_template('show_image.html', file_url=file_url)

def get_presigned_url(bucket_name, object_key, expiration_time=3600):
    """
    Oluşturulan ön imzalı URL'i döndüren yardımcı fonksiyon.
    :param bucket_name: Dosyanın bulunduğu bucket adı
    :param object_key: Dosyanın anahtarı (isim)
    :param expiration_time: Ön imzalı URL'in ne kadar süre geçerli olacağı (saniye cinsinden)
    :return: Ön imzalı URL
    """
    try:
        # Geçerlilik süresi ekleyerek ön imzalı URL oluştur
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key
            },
            ExpiresIn=expiration_time
        )
        return url
    except ClientError as e:
        # Hata durumunda buraya düşer
        print(f'Hata oluştu: {e}')
        return None


if __name__ == '__main__':
    app.run(debug=True)
