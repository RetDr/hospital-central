# hospital/models/user.py

from models.database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

def find_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, email, password, nombre, rol FROM usuarios WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def register_user(nombre, email, password, rol):
    conn = get_connection()
    cur = conn.cursor()
    # Hash seguro de la contraseña
    password_hash = generate_password_hash(password)
    cur.execute(
        "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)",
        (nombre, email, password_hash, rol)
    )
    conn.commit()
    cur.close()
    conn.close()
    return True

def verify_password(stored_password_hash, provided_password):
    return check_password_hash(stored_password_hash, provided_password)
