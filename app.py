from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder="frontend", static_url_path="")

# Configuracion de seguridad JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "m1H_93nd0_aquiVa!TuClave$Unica1248_XYZ")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"

CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)

# Rate limiting simple (en memoria)
app.config['LOGIN_ATTEMPTS'] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 minutos

@app.before_request
def check_rate_limit():
    if request.endpoint == 'auth.login' and request.method == 'POST':
        ip = request.remote_addr
        import time
        current_time = time.time()
        login_attempts = app.config.get('LOGIN_ATTEMPTS', {})

        if ip in login_attempts:
            attempts, lockout_start = login_attempts[ip]
            if attempts >= MAX_LOGIN_ATTEMPTS:
                if current_time - lockout_start < LOCKOUT_TIME:
                    return jsonify({'msg': 'Demasiados intentos. Intente en 5 minutos.'}), 429
                else:
                    login_attempts[ip] = (0, current_time)
                    app.config['LOGIN_ATTEMPTS'] = login_attempts

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Importar rutas de API
from routes.auth import auth_bp
from routes.pacientes import pacientes_bp
from routes.medicos import medicos_bp
from routes.citas import citas_bp
from routes.usuarios import usuarios_bp

app.register_blueprint(usuarios_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(pacientes_bp)
app.register_blueprint(medicos_bp)
app.register_blueprint(citas_bp)

# Rutas para servir archivos del frontend
@app.route("/")
def root():
    return send_from_directory(app.static_folder, "login.html")

@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(debug=False)
