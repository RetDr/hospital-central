from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.database import get_connection
import re

auth_bp = Blueprint('auth', __name__)

def validar_password(password):
    """Valida que la contrasena cumpla requisitos de seguridad"""
    if len(password) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contrasena debe tener al menos una mayuscula"
    if not re.search(r'[a-z]', password):
        return False, "La contrasena debe tener al menos una minuscula"
    if not re.search(r'\d', password):
        return False, "La contrasena debe tener al menos un numero"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contrasena debe tener al menos un caracter especial (!@#$%^&*)"
    return True, "OK"

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['nombre', 'email', 'password', 'especialidad_id']
    if not all(k in data and data[k] for k in required):
        return jsonify({'msg': 'Datos incompletos'}), 400

    # Validar formato de email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, data['email']):
        return jsonify({'msg': 'Formato de email invalido'}), 400

    # Validar contrasena
    password_valid, password_msg = validar_password(data['password'])
    if not password_valid:
        return jsonify({'msg': password_msg}), 400

    # Validar confirmacion de contrasena
    if data.get('password') != data.get('confirm_password'):
        return jsonify({'msg': 'Las contrasenas no coinciden'}), 400

    rol = 'medico'

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que la especialidad exista
    cursor.execute("SELECT id FROM especialidades WHERE id=%s", (data['especialidad_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Especialidad no valida'}), 400

    # Verificar email unico en usuarios
    cursor.execute("SELECT id FROM usuarios WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg':'Correo ya registrado'}), 409

    # Verificar email unico en medicos
    cursor.execute("SELECT id FROM medicos WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg':'Ya existe un medico con este correo'}), 409

    password_hash = generate_password_hash(data['password'], method='scrypt')

    # Crear usuario
    cursor.execute(
        "INSERT INTO usuarios (nombre,email,password,rol) VALUES (%s,%s,%s,%s)",
        (data['nombre'], data['email'], password_hash, rol)
    )

    # Crear registro de medico automaticamente
    cursor.execute("""
        INSERT INTO medicos (nombre, especialidad_id, registro_medico, telefono, email)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data['nombre'],
        data['especialidad_id'],
        data.get('registro_medico', ''),
        data.get('telefono', ''),
        data['email']
    ))

    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg':'Usuario y perfil medico registrado exitosamente'}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    from flask import current_app
    import time

    data = request.get_json()
    ip = request.remote_addr

    if not data.get('email') or not data.get('password'):
        return jsonify({'msg': 'Datos incompletos'}), 400

    # Sanitizar email
    email = data['email'].strip().lower()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close(); conn.close()

    # Acceder a login_attempts desde app
    login_attempts = current_app.config.get('LOGIN_ATTEMPTS', {})
    current_time = time.time()

    if not user or not check_password_hash(user['password'], data['password']):
        # Registrar intento fallido
        if ip in login_attempts:
            attempts, _ = login_attempts[ip]
            login_attempts[ip] = (attempts + 1, current_time)
        else:
            login_attempts[ip] = (1, current_time)
        current_app.config['LOGIN_ATTEMPTS'] = login_attempts
        return jsonify({'msg': 'Usuario o contrasena incorrectos'}), 401

    # Login exitoso - resetear intentos
    if ip in login_attempts:
        del login_attempts[ip]
        current_app.config['LOGIN_ATTEMPTS'] = login_attempts

    token = create_access_token(identity=str(user['id']), additional_claims={
        "email": user['email'],
        "nombre": user['nombre'],
        "rol": user['rol'],
    })
    return jsonify({'token': token}), 200

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

@auth_bp.route('/api/especialidades-publicas', methods=['GET'])
def listar_especialidades_publicas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM especialidades ORDER BY nombre")
    especialidades = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(especialidades)