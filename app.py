from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__, static_folder="frontend", static_url_path="")
app.config["JWT_SECRET_KEY"] = "m1H_93nd0_aquiVa!TuClave$Unica1248_XYZ"

CORS(app)
jwt = JWTManager(app)

# Importar rutas de API
from routes.auth import auth_bp
from routes.pacientes import pacientes_bp
from routes.medicos import medicos_bp
from routes.citas import citas_bp
from routes.auth import auth_bp
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
    app.run(debug=True)
