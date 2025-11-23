from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import get_connection
from utils.auth_helpers import roles_required
from datetime import datetime

citas_bp = Blueprint('citas', __name__)

# LISTAR
@citas_bp.route('/citas', methods=['GET'])
@jwt_required()
def listar_citas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id, c.paciente_id, p.nombre AS paciente, c.medico_id, m.nombre AS medico,
               c.fecha, c.estado, c.motivo, c.prioridad
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN medicos m ON c.medico_id = m.id
        ORDER BY c.fecha DESC
    """)
    citas = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(citas)

# CREAR
@citas_bp.route('/citas', methods=['POST'])
@jwt_required()
@roles_required('admin', 'medico')
def crear_cita():
    data = request.get_json()
    required = ['paciente_id', 'medico_id', 'fecha', 'estado', 'motivo', 'prioridad']
    if not all(k in data and data[k] for k in required):
        print(data)
        return jsonify({'msg': 'Datos incompletos'}), 400
    try:
        # Validar fecha futura
        fecha_obj = datetime.fromisoformat(data['fecha'])
        if fecha_obj <= datetime.now():
            return jsonify({'msg': 'La fecha debe ser futura'}), 400
        # Validar estado
        if data['estado'] not in ['programada', 'atendida', 'cancelada']:
            return jsonify({'msg': 'Estado no valido'}), 400
        # Validar prioridad
        if data['prioridad'] not in ['baja', 'media', 'alta']:
            return jsonify({'msg': 'Prioridad no válida'}), 400
    except Exception as e:
        return jsonify({'msg': 'Error de formato de fecha', 'error': str(e)}), 400
    conn = get_connection()
    cursor = conn.cursor()
    # Validar existencia de paciente y medico
    cursor.execute("SELECT id FROM pacientes WHERE id=%s", (data['paciente_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Paciente no existe'}), 404
    cursor.execute("SELECT id FROM medicos WHERE id=%s", (data['medico_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Médico no existe'}), 404
    cursor.execute("""
        INSERT INTO citas (paciente_id, medico_id, fecha, estado, motivo, prioridad)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (data['paciente_id'], data['medico_id'], data['fecha'], data['estado'], data['motivo'], data['prioridad']))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Cita creada'}), 201

# EDITAR
@citas_bp.route('/citas/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin', 'medico')
def editar_cita(id):
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'Datos no recibidos'}), 400

    paciente_id = data.get('paciente_id')
    medico_id = data.get('medico_id')
    fecha_str = data.get('fecha', '')
    estado = data.get('estado', 'programada')
    prioridad = data.get('prioridad', 'media')
    motivo = data.get('motivo', '')

    if not paciente_id or not medico_id or not fecha_str:
        return jsonify({'msg': 'Paciente, medico y fecha son requeridos'}), 400

    valid_states = ['programada', 'atendida', 'cancelada']
    if estado not in valid_states:
        return jsonify({'msg': 'Estado no valido'}), 400

    valid_priorities = ['baja', 'media', 'alta']
    if prioridad not in valid_priorities:
        return jsonify({'msg': 'Prioridad no valida'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM citas WHERE id=%s", (id,))
        if not cursor.fetchone():
            return jsonify({'msg': 'Cita no encontrada'}), 404

        cursor.execute("SELECT id FROM pacientes WHERE id=%s", (paciente_id,))
        if not cursor.fetchone():
            return jsonify({'msg': 'Paciente no existe'}), 404

        cursor.execute("SELECT id FROM medicos WHERE id=%s", (medico_id,))
        if not cursor.fetchone():
            return jsonify({'msg': 'Medico no existe'}), 404

        cursor.execute("""
            UPDATE citas SET paciente_id=%s, medico_id=%s, fecha=%s, estado=%s, motivo=%s, prioridad=%s
            WHERE id=%s
        """, (paciente_id, medico_id, fecha_str, estado, motivo, prioridad, id))

        return jsonify({'msg': 'Cita actualizada'}), 200
    except Exception as e:
        return jsonify({'msg': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# BORRAR
@citas_bp.route('/citas/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin', 'medico')
def borrar_cita(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM citas WHERE id=%s", (id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'msg': 'Cita eliminada'}), 200
