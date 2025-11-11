from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import get_connection
from utils.auth_helpers import roles_required

medicos_bp = Blueprint('medicos', __name__)

# LISTAR
@medicos_bp.route('/medicos', methods=['GET'])
@jwt_required()
def listar_medicos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id, m.nombre, m.especialidad_id, e.nombre AS especialidad, m.registro_medico, m.telefono, m.email
        FROM medicos m
        LEFT JOIN especialidades e ON m.especialidad_id = e.id
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

# CREAR
@medicos_bp.route('/medicos', methods=['POST'])
@jwt_required()
@roles_required('admin')
def crear_medico():
    data = request.get_json()
    required = ['nombre', 'especialidad_id', 'registro_medico', 'telefono', 'email']
    if not all(k in data and data[k] for k in required):
        return jsonify({'msg': 'Datos incompletos'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    # Validación de especialidad existente
    cursor.execute("SELECT id FROM especialidades WHERE id=%s", (data['especialidad_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Especialidad no válida'}), 400
    # Validar email único
    cursor.execute("SELECT id FROM medicos WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Email ya existe'}), 409
    cursor.execute("""
        INSERT INTO medicos (nombre, especialidad_id, registro_medico, telefono, email)
        VALUES (%s,%s,%s,%s,%s)
    """, (data['nombre'], data['especialidad_id'], data['registro_medico'], data['telefono'], data['email']))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Médico creado'}), 201

# EDITAR
@medicos_bp.route('/medicos/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin')
def editar_medico(id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    # Validar especialidad
    cursor.execute("SELECT id FROM especialidades WHERE id=%s", (data['especialidad_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Especialidad no válida'}), 400
    cursor.execute("SELECT id FROM medicos WHERE email=%s AND id!=%s", (data['email'], id))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Email ya existe en otro médico'}), 409
    cursor.execute("""
        UPDATE medicos SET nombre=%s, especialidad_id=%s, registro_medico=%s, telefono=%s, email=%s
        WHERE id=%s
    """, (data['nombre'], data['especialidad_id'], data['registro_medico'], data['telefono'], data['email'], id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Médico actualizado'}), 200

# BORRAR
@medicos_bp.route('/medicos/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin')
def borrar_medico(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medicos WHERE id=%s", (id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Médico eliminado'}), 200

@medicos_bp.route('/especialidades', methods=['GET'])
@jwt_required()
def listar_especialidades():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM especialidades")
    especialidades = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(especialidades)
# CREAR ESPECIALIDAD
