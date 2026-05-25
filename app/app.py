from flask import Flask, jsonify
import redis
import os

app = Flask(__name__)

# Resolve connection details via environment or default to internal service discovery
redis_host = os.environ.get('REDIS_HOST', 'redis-service')

r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

@app.route('/')
def hello():
 return jsonify({'message': 'FluidAI DevOps Demo', 'status': 'ok'})

@app.route('/health')
def health():
 try:
 r.ping()
 return jsonify({'status': 'healthy', 'redis': 'connected'}), 200
 except Exception as e:
 return jsonify({'status': 'unhealthy', 'redis': str(e)}), 503

@app.route('/count')
def count():
 hits = r.incr('hits')
 return jsonify({
 'hits': hits,
 'message': f'This page has been visited {hits} times'
 })

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)