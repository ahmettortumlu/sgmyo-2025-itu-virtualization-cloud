#!/usr/bin/env python3
"""
DNS Sorgulama ve MongoDB Kayıt Uygulaması
"""
import os
import socket
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# MongoDB bağlantı bilgilerini ortam değişkenlerinden al
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', '27017'))
MONGO_USER = os.environ.get('MONGO_USER', '')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')
MONGO_DB = os.environ.get('MONGO_DB', 'dns_lookup_db')

def get_mongo_client():
    """MongoDB client oluştur"""
    try:
        if MONGO_USER and MONGO_PASSWORD:
            # Kullanıcı adı ve şifre varsa authentication ile bağlan
            connection_string = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        else:
            # Kullanıcı adı ve şifre yoksa (local development)
            connection_string = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
        
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # Bağlantıyı test et
        client.admin.command('ping')
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return None

def perform_dns_lookup(domain):
    """DNS lookup işlemini gerçekleştir"""
    results = {
        'domain': domain,
        'timestamp': datetime.utcnow(),
        'success': False,
        'ip_addresses': [],
        'error': None
    }
    
    try:
        # DNS çözümlemesi yap
        ip_addresses = socket.gethostbyname_ex(domain)
        results['ip_addresses'] = ip_addresses[2]
        results['success'] = True
        results['canonical_name'] = ip_addresses[0]
    except socket.gaierror as e:
        results['error'] = f"DNS çözümleme hatası: {str(e)}"
    except Exception as e:
        results['error'] = f"Beklenmeyen hata: {str(e)}"
    
    return results

def save_to_mongodb(data):
    """DNS lookup sonucunu MongoDB'ye kaydet"""
    try:
        client = get_mongo_client()
        if client is None:
            return False, "MongoDB bağlantısı kurulamadı"
        
        db = client[MONGO_DB]
        collection = db['dns_lookups']
        
        # Veriyi kaydet
        result = collection.insert_one(data)
        client.close()
        
        return True, str(result.inserted_id)
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/lookup', methods=['POST'])
def lookup():
    """DNS lookup işlemi"""
    domain = request.form.get('domain', '').strip()
    
    if not domain:
        flash('Lütfen bir domain adresi girin!', 'error')
        return redirect(url_for('index'))
    
    # DNS lookup yap
    result = perform_dns_lookup(domain)
    
    # MongoDB'ye kaydet
    saved, message = save_to_mongodb(result)
    
    if saved:
        if result['success']:
            flash(f"✓ '{domain}' başarıyla sorgulandı ve kaydedildi!", 'success')
        else:
            flash(f"⚠ Sorgu tamamlandı ancak hata oluştu: {result['error']}", 'warning')
    else:
        flash(f"✗ MongoDB kayıt hatası: {message}", 'error')
    
    return render_template('index.html', result=result, saved=saved)

@app.route('/api/lookup', methods=['POST'])
def api_lookup():
    """API endpoint - JSON response"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'error': 'Domain parametresi gerekli'}), 400
    
    domain = data['domain'].strip()
    
    if not domain:
        return jsonify({'error': 'Domain boş olamaz'}), 400
    
    # DNS lookup yap
    result = perform_dns_lookup(domain)
    
    # MongoDB'ye kaydet
    saved, message = save_to_mongodb(result)
    result['saved_to_db'] = saved
    result['save_message'] = message
    
    # Timestamp'i string'e çevir (JSON serialization için)
    result['timestamp'] = result['timestamp'].isoformat()
    
    return jsonify(result)

@app.route('/health')
def health():
    """Sağlık kontrolü endpoint'i"""
    mongo_status = "connected"
    client = get_mongo_client()
    if client is None:
        mongo_status = "disconnected"
    else:
        client.close()
    
    return jsonify({
        'status': 'ok',
        'mongodb': mongo_status,
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    # Development sunucusunu başlat
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
app.py    port = int(os.environ.get('FLASK_PORT', '5889'))
    
    print("=" * 60)
    print("DNS Lookup Web Uygulaması")
    print("=" * 60)
    print(f"MongoDB Host: {MONGO_HOST}:{MONGO_PORT}")
    print(f"MongoDB Database: {MONGO_DB}")
    print(f"Port: {port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

