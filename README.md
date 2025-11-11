# Hospital Central

Sistema web de gestión hospitalaria, desarrollado en Python Flask (backend) y Bootstrap (frontend).  
Permite el manejo seguro de usuarios, registro y administración de pacientes, médicos, especialidades y citas.

## Características

- **Control de Acceso:** Inicio de sesión seguro con JWT y roles (admin, médico).
- **CRUD completo:** Usuarios, pacientes, médicos, especialidades, citas.
- **Frontend moderno:** Dashboard con Bootstrap y validaciones.
- **API REST:** Todas las funciones accesibles por endpoints protegidos.
- **Registro de especialidades:** Cada médico asocia una especialidad lógica.

## Requisitos previos

- Python 3.8+
- MySQL/MariaDB instalado y corriendo (usa XAMPP, WAMP o servicio propio)
- pip (instalador de paquetes Python)
- Git

## Instalación

Clona el repositorio:

git clone https://github.com/RetDr/hospital-central

cd hospital-central


## Instala las dependencias:

pip install -r requirements.txt


## Configuración Base de Datos

1. **Crea la base y carga el esquema y datos**  
   Abre tu cliente MySQL y ejecuta:

source base_de_datos.sql;

O desde consola:

mysql -u TU_USUARIO -p < base_de_datos.sql


2. **Configura la conexión en tu archivo `models/database.py`**

Asegúrate de que los parámetros (host, user, password, db) coincidan con tu local.

## Ejecución

Desde la raíz del proyecto ejecuta:

python app.py


El sistema levanta en `http://127.0.0.1:5000/`.

Para acceder al dashboard, ve a `login.html` e inicia sesión con un usuario válido (ejemplo admin).

## Estructura del proyecto

hospital-central/
app.py
requirements.txt
/models
/routes
/frontend
base_de_datos.sql
README.md


## Extras

- Para cargar datos de ejemplo adicionales, edita y vuelve a importar `base_de_datos.sql`.
- Las contraseñas de usuarios deben estar hasheadas (por seguridad).

---

Desarrollado por: [Daniel Rodriguez](https://github.com/RetDr)
