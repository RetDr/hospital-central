from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import get_connection
from utils.auth_helpers import roles_required

pacientes_bp = Blueprint('pacientes', __name__)

@pacientes_bp.route('/pacientes', methods=['GET'])
@jwt_required()
def listar_pacientes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, documento, nombre, edad, genero FROM pacientes")
    pacientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(pacientes)

# CREAR
@pacientes_bp.route('/pacientes', methods=['POST'])
@jwt_required()
@roles_required('admin', 'medico')
def crear_paciente():
    data = request.get_json()
    required = ['documento', 'nombre', 'edad', 'genero', 'email']
    if not all(k in data and data[k] for k in required):
        return jsonify({'msg': 'Datos incompletos'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    # Validación de documento/email único
    cursor.execute("SELECT id FROM pacientes WHERE documento=%s OR email=%s", (data['documento'], data['email']))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Documento o email ya existen'}), 409
    cursor.execute("INSERT INTO pacientes (documento, nombre, edad, genero, email) VALUES (%s,%s,%s,%s,%s)",
                   (data['documento'], data['nombre'], data['edad'], data['genero'], data['email']))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Paciente creado'}), 201

# EDITAR
@pacientes_bp.route('/pacientes/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin', 'medico')
def editar_paciente(id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    # Validación única, excluyendo el ID actual
    cursor.execute("SELECT id FROM pacientes WHERE (documento=%s OR email=%s) AND id!=%s", (data['documento'], data['email'], id))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Documento o email ya existen en otro paciente'}), 409
    cursor.execute("UPDATE pacientes SET documento=%s, nombre=%s, edad=%s, genero=%s, email=%s WHERE id=%s",
                   (data['documento'], data['nombre'], data['edad'], data['genero'], data['email'], id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Paciente actualizado'}), 200

# BORRAR
@pacientes_bp.route('/pacientes/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin', 'medico')
def borrar_paciente(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pacientes WHERE id=%s", (id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Paciente eliminado'}), 200
