from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import get_connection
from utils.auth_helpers import roles_required
from flask_jwt_extended import get_jwt_identity

medicos_bp = Blueprint('medicos', __name__)

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
    cursor.close(); conn.close()
    return jsonify(result)

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
    cursor.execute("SELECT id FROM especialidades WHERE id=%s", (data['especialidad_id'],))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'msg': 'Especialidad no válida'}), 400
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

@medicos_bp.route('/medicos/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required('admin')
def editar_medico(id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
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

@medicos_bp.route('/medicos/perfil', methods=['GET', 'POST', 'PUT'])
@jwt_required()
def editar_perfil_medico():
    user_id = get_jwt_identity()  # El id del usuario logueado
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Busca el email y nombre del usuario registrado y verifica rol
    cursor.execute("SELECT email, nombre FROM usuarios WHERE id=%s AND rol='medico'", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close(); conn.close()
        return jsonify({'msg':'Acceso solo para médicos'}), 403

    if request.method == 'GET':
        # Consulta el perfil del médico autenticado
        cursor.execute("""
            SELECT m.id, m.nombre, m.especialidad_id, e.nombre AS especialidad, m.registro_medico, m.telefono, m.email
            FROM medicos m
            LEFT JOIN especialidades e ON m.especialidad_id = e.id
            WHERE m.email=%s
        """, (user['email'],))
        medico_profile = cursor.fetchone()
        
        is_complete = False
        if medico_profile:
            # Un perfil se considera completo si los campos especialidad_id, registro_medico y telefono no son nulos o vacíos
            is_complete = (
                medico_profile.get('especialidad_id') is not None and medico_profile.get('especialidad_id') != 0 and
                medico_profile.get('registro_medico') is not None and medico_profile.get('registro_medico').strip() != '' and
                medico_profile.get('telefono') is not None and medico_profile.get('telefono').strip() != ''
            )
            
        cursor.close(); conn.close()
        return jsonify({
            'profile': medico_profile,
            'is_complete': is_complete,
            'msg': 'Perfil médico cargado' if is_complete else 'Perfil médico incompleto o no configurado. Por favor, complete su información profesional.'
        }), 200

    elif request.method in ['POST', 'PUT']:
        data = request.get_json()
        required = ['especialidad_id', 'registro_medico', 'telefono']
        # Validar que los campos requeridos estén presentes y no vacíos/nulos
        if not all(k in data and data[k] for k in required):
            cursor.close(); conn.close()
            return jsonify({'msg': 'Datos incompletos. Se requieren especialidad, registro médico y teléfono.'}), 400

        # Validar que la especialidad exista
        cursor.execute("SELECT id FROM especialidades WHERE id=%s", (data['especialidad_id'],))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'msg': 'Especialidad no válida'}), 400

        # Ver si ya existe un perfil médico asociado a este email de usuario
        cursor.execute("SELECT id FROM medicos WHERE email=%s", (user['email'],))
        existing_medico = cursor.fetchone()

        if existing_medico:
            # Actualiza el perfil médico existente
            cursor.execute("""
                UPDATE medicos SET nombre=%s, especialidad_id=%s, registro_medico=%s, telefono=%s
                WHERE email=%s
            """, (user['nombre'], data['especialidad_id'], data['registro_medico'], data['telefono'], user['email']))
            conn.commit()
            cursor.close(); conn.close()
            return jsonify({'msg':'Perfil médico actualizado'}), 200
        else:
            # Crea un nuevo registro de perfil médico
            cursor.execute("""
                INSERT INTO medicos (nombre, especialidad_id, registro_medico, telefono, email)
                VALUES (%s,%s,%s,%s,%s)
            """, (user['nombre'], data['especialidad_id'], data['registro_medico'], data['telefono'], user['email']))
            conn.commit()
            cursor.close(); conn.close()
            return jsonify({'msg':'Perfil médico creado'}), 201