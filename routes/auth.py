from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_connection

auth_bp = Blueprint('auth', __name__)

# Registro de usuario (acceso público)
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['nombre', 'email', 'password', 'rol']
    if not all(k in data and data[k] for k in required):
        return jsonify({'msg': 'Datos incompletos'}), 400
    if data['rol'] not in ['admin','medico']:
        return jsonify({'msg':'Rol no válido'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg':'Correo ya registrado'}), 409
    password_hash = generate_password_hash(data['password'])
    cursor.execute("INSERT INTO usuarios (nombre,email,password,rol) VALUES (%s,%s,%s,%s)",
                   (data['nombre'], data['email'], password_hash, data['rol']))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg':'Usuario registrado'}), 201

# Login
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'msg': 'Datos incompletos'}), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (data['email'],))
    user = cursor.fetchone()
    cursor.close(); conn.close()
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'msg': 'Usuario o contraseña incorrectos'}), 401
    token = create_access_token(identity=str(user['id']), additional_claims={
        "email": user['email'],
        "nombre": user['nombre'],
        "rol": user['rol'],
    })
    return jsonify({'token': token}), 200

# Obtener usuario actual por JWT
@auth_bp.route('/api/user', methods=['GET'])
@jwt_required()
def current_user():
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    return jsonify({
        "id": get_jwt_identity(),
        "nombre": claims.get('nombre'),
        "email": claims.get('email'),
        "rol": claims.get('rol')
    })
