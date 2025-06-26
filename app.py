from flask import Flask, request, redirect, jsonify, render_template
from datetime import datetime, timedelta
import string, random, re
from logger import CustomLoggerMiddleware

app = Flask(__name__)
app.wsgi_app = CustomLoggerMiddleware(app.wsgi_app)

URLS = {}
CLICKS = {}

def is_valid_url(url):
    return re.match(r'^https?://', url)

def generate_shortcode(length=5):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in URLS:
            return code

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shorturls', methods=['POST'])
def create_short_url():
    data = request.get_json() or request.form
    url = data.get('url')
    validity = int(data.get('validity', 30))
    shortcode = data.get('shortcode')

    if not url or not is_valid_url(url):
        return jsonify({'error': 'Invalid URL'}), 400

    if shortcode:
        if not re.match(r'^[A-Za-z0-9]{3,10}$', shortcode):
            return jsonify({'error': 'Invalid shortcode'}), 400
        if shortcode in URLS:
            return jsonify({'error': 'Shortcode already exists'}), 409
    else:
        shortcode = generate_shortcode()

    expiry = datetime.utcnow() + timedelta(minutes=validity)
    URLS[shortcode] = {
        'url': url,
        'created': datetime.utcnow(),
        'expiry': expiry,
        'clicks': 0
    }
    CLICKS[shortcode] = []

    return jsonify({
        'shortLink': request.host_url + shortcode,
        'expiry': expiry.isoformat() + 'Z'
    }), 201

@app.route('/<shortcode>')
def redirect_short_url(shortcode):
    entry = URLS.get(shortcode)
    if not entry:
        return jsonify({'error': 'Shortcode not found'}), 404
    if datetime.utcnow() > entry['expiry']:
        return jsonify({'error': 'Shortcode expired'}), 410

    entry['clicks'] += 1
    CLICKS[shortcode].append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'referrer': request.referrer,
        'ip': request.remote_addr
    })
    return redirect(entry['url'])

@app.route('/shorturls/<shortcode>', methods=['GET'])
def get_stats(shortcode):
    entry = URLS.get(shortcode)
    if not entry:
        return jsonify({'error': 'Shortcode not found'}), 404

    return jsonify({
        'original_url': entry['url'],
        'created': entry['created'].isoformat() + 'Z',
        'expiry': entry['expiry'].isoformat() + 'Z',
        'clicks': entry['clicks'],
        'click_data': CLICKS[shortcode]
    })

if __name__ == '__main__':
    app.run(debug=True)

# i tried to use middle ware logging by using the geo2