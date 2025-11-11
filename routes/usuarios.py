from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.auth_helpers import roles_required
from models.database import get_connection
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint('usuarios', __name__)

# CREAR USUARIO (solo admin)
@usuarios_bp.route('/usuarios', methods=['POST'])
@jwt_required()
@roles_required('admin')
def crear_usuario():
    data = request.get_json()
    required = ['nombre','email','password','rol']
    if not all(k in data and data[k] for k in required):
        return jsonify({'msg': 'Datos incompletos'}), 400
    if data['rol'] not in ['admin','medico']:
        return jsonify({'msg': 'Rol no válido'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Email ya existe'}), 409
    password_hash = generate_password_hash(data['password'])
    cursor.execute(
        "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s,%s,%s,%s)",
        (data['nombre'], data['email'], password_hash, data['rol'])
    )
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Usuario creado'}), 201

# LISTAR USUARIOS (solo admin)
@usuarios_bp.route('/usuarios', methods=['GET'])
@jwt_required()
@roles_required('admin')
def listar_usuarios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, email, rol FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(usuarios)

# EDITAR USUARIO (solo admin)
@usuarios_bp.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin')
def editar_usuario(id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email=%s AND id!=%s", (data['email'], id))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Email ya existe en otro usuario'}), 409
    values = [data['nombre'], data['email'], data['rol']]
    query_set = "nombre=%s, email=%s, rol=%s"
    # Solo actualiza password si se envía
    if data.get('password'):
        password_hash = generate_password_hash(data['password'])
        query_set += ", password=%s"
        values.append(password_hash)
    values.append(id)
    cursor.execute(f"UPDATE usuarios SET {query_set} WHERE id=%s", values)
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Usuario actualizado'}), 200

# BORRAR USUARIO (solo admin)
@usuarios_bp.route('/usuarios/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin')
def borrar_usuario(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Usuario eliminado'}), 200
