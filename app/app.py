from flask import Flask, Response, jsonify, render_template_string, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
import redis
import os

app = Flask(__name__)
request_counter = Counter(
  'fluidai_http_requests_total',
  'Total HTTP requests served by the FluidAI demo app',
  ['method', 'endpoint', 'http_status']
)
hit_counter = Counter(
  'fluidai_count_hits_total',
  'Total count button/API hits served by the FluidAI demo app'
)

# Resolve connection details via environment or default to internal service discovery
redis_host = os.environ.get('REDIS_HOST', 'redis-service')

r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

@app.after_request
def track_request(response):
  endpoint = request.endpoint or 'unknown'
  request_counter.labels(request.method, endpoint, response.status_code).inc()
  return response

@app.route('/')
def hello():
  return render_template_string('''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FluidAI DevOps Demo</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f4f7fb;
      color: #172033;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }

    main {
      width: min(92vw, 560px);
      padding: 32px;
      background: #ffffff;
      border: 1px solid #d9e2ef;
      border-radius: 8px;
      box-shadow: 0 16px 40px rgba(23, 32, 51, 0.10);
    }

    h1 {
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.2;
    }

    p {
      margin: 0 0 24px;
      color: #4c5870;
      line-height: 1.5;
    }

    .status {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 24px;
    }

    .metric {
      padding: 16px;
      border: 1px solid #d9e2ef;
      border-radius: 8px;
      background: #f8fafc;
    }

    .label {
      display: block;
      margin-bottom: 8px;
      color: #667085;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .value {
      font-size: 24px;
      font-weight: 700;
    }

    button {
      width: 100%;
      min-height: 48px;
      border: 0;
      border-radius: 8px;
      background: #1463ff;
      color: #ffffff;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
    }

    button:disabled {
      cursor: wait;
      opacity: 0.7;
    }

    @media (max-width: 520px) {
      main {
        padding: 24px;
      }

      .status {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main>
    <h1>FluidAI DevOps Demo</h1>
    <p>Redis-backed request counter</p>

    <section class="status" aria-live="polite">
      <div class="metric">
        <span class="label">HTTP status</span>
        <span class="value" id="http-status">Ready</span>
      </div>
      <div class="metric">
        <span class="label">Hit count</span>
        <span class="value" id="hit-count">-</span>
      </div>
    </section>

    <button id="hit-button" type="button">Increase Count</button>
  </main>

  <script>
    const button = document.getElementById('hit-button');
    const statusText = document.getElementById('http-status');
    const hitCount = document.getElementById('hit-count');

    async function increaseCount() {
      button.disabled = true;
      statusText.textContent = 'Loading';

      try {
        const response = await fetch('/count');
        const data = await response.json();

        statusText.textContent = response.status;
        hitCount.textContent = data.hits ?? '-';
      } catch (error) {
        statusText.textContent = 'Error';
        hitCount.textContent = '-';
      } finally {
        button.disabled = false;
      }
    }

    button.addEventListener('click', increaseCount);
  </script>
</body>
</html>
  ''')

@app.route('/health')
def health():
  try:
    r.ping()
    return jsonify({'status': 'healthy', 'redis': 'connected'}), 200
  except Exception as e:
    return jsonify({'status': 'unhealthy', 'redis': str(e)}), 503

@app.route('/count')
def count():
  try:
    hits = r.incr('hits')
    hit_counter.inc()
    return jsonify({
      'hits': hits,
      'message': f'This page has been visited {hits} times'
    }), 200
  except Exception as e:
    return jsonify({'status': 'error', 'redis': str(e)}), 503

@app.route('/metrics')
def metrics():
  return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
