# app.py - añade registro de usuarios y login usando DB (hash de contraseñas)
from flask import Flask, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave-secreta")  # ¡Reemplaza esto en producción!

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///practica_demo.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

class Estudiante(db.Model):
    __tablename__ = "estudiantes"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)

class Curso(db.Model):
    __tablename__ = "cursos"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)

class Inscripcion(db.Model):
    __tablename__ = "inscripciones"
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    fecha_inscripcion = db.Column(db.Date, server_default=db.func.current_date())
    __table_args__ = (db.UniqueConstraint('estudiante_id', 'curso_id', name='_est_curso_uc'),)


# --- UTILIDADES ---
def create_initial_users():
    """Crea usuarios de prueba si no existen (opcional)."""
    if User.query.first() is not None:
        return
    sample = [
        ("admin", "adminpass"),
        ("angel", "1234"),
        ("juan", "password123"),
    ]
    for u, p in sample:
        hashed = generate_password_hash(p)
        user = User(username=u, password_hash=hashed)
        db.session.add(user)
    db.session.commit()
    app.logger.info("Usuarios de prueba creados.")


# --- RUTAS DE AUTENTICACIÓN ---

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registro de nuevos usuarios.
    Guarda username y hash de la contraseña en la tabla users.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Validaciones básicas
        if not username or not password:
            return "<h3>❌ Debes completar usuario y contraseña.</h3><a href='/register'>Volver</a>"
        if password != password2:
            return "<h3>❌ Las contraseñas no coinciden.</h3><a href='/register'>Volver</a>"

        # Verificar si el usuario ya existe
        existing = User.query.filter_by(username=username).first()
        if existing:
            return "<h3>❌ El nombre de usuario ya existe.</h3><a href='/register'>Volver</a>"

        # Crear usuario con hash de contraseña
        hashed = generate_password_hash(password)
        nuevo = User(username=username, password_hash=hashed)
        try:
            db.session.add(nuevo)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"<h3>❌ Error al crear usuario: {str(e)}</h3><a href='/register'>Volver</a>"

        return "<h3>✅ Registro exitoso. Ya puedes iniciar sesión.</h3><a href='/login'>Ir a login</a>"

    # Formulario de registro
    return """
        <h2>Registrarse</h2>
        <form method="POST">
            Usuario: <input type="text" name="username" required><br>
            Contraseña: <input type="password" name="password" required><br>
            Repite Contraseña: <input type="password" name="password2" required><br>
            <input type="submit" value="Registrar">
        </form>
        <p>¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login que verifica contra la tabla users (usando hash).
    """
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "")

        if not usuario or not contrasena:
            return "<h3>❌ Completa usuario y contraseña.</h3><a href='/login'>Volver</a>"

        user = User.query.filter_by(username=usuario).first()
        if user and check_password_hash(user.password_hash, contrasena):
            session["usuario"] = usuario
            return redirect("/")
        else:
            return "<h3>❌ Usuario o contraseña incorrectos</h3><a href='/login'>Volver</a>"

    return """
        <h2>Iniciar sesión</h2>
        <form method="POST">
            Usuario: <input type="text" name="usuario" required><br>
            Contraseña: <input type="password" name="contrasena" required><br>
            <input type="submit" value="Entrar">
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate</a></p>
    """


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/login")


# --- RUTAS PRINCIPALES PROTEGIDAS ---
@app.route("/", methods=["GET", "POST"])
def index():
    if "usuario" not in session:
        return redirect("/login")

    mensaje = ""

    if request.method == "POST":
        try:
            tipo = request.form.get("tipo")

            if tipo == "estudiante":
                nombre = request.form.get("nombre")
                correo = request.form.get("correo")
                if not nombre or not correo:
                    raise ValueError("Nombre y correo son obligatorios")
                nuevo = Estudiante(nombre=nombre, correo=correo)
                db.session.add(nuevo)

            elif tipo == "curso":
                titulo = request.form.get("titulo")
                descripcion = request.form.get("descripcion")
                if not titulo:
                    raise ValueError("Título es obligatorio")
                nuevo = Curso(titulo=titulo, descripcion=descripcion)
                db.session.add(nuevo)

            elif tipo == "inscripcion":
                estudiante_id = request.form.get("estudiante_id")
                curso_id = request.form.get("curso_id")
                if not estudiante_id or not curso_id:
                    raise ValueError("ID Estudiante y ID Curso son obligatorios")
                nuevo = Inscripcion(estudiante_id=int(estudiante_id), curso_id=int(curso_id))
                db.session.add(nuevo)

            db.session.commit()
            mensaje = "✅ Dato agregado correctamente."

        except Exception as e:
            db.session.rollback()
            mensaje = f"❌ Error: {str(e)}"

    estudiantes = Estudiante.query.all()
    cursos = Curso.query.all()
    inscripciones = Inscripcion.query.all()

    tabla_estudiantes = "<h3>Estudiantes</h3><table border='1'><tr><th>ID</th><th>Nombre</th><th>Correo</th></tr>"
    for e in estudiantes:
        tabla_estudiantes += f"<tr><td>{e.id}</td><td>{e.nombre}</td><td>{e.correo}</td></tr>"
    tabla_estudiantes += "</table>"

    tabla_cursos = "<h3>Cursos</h3><table border='1'><tr><th>ID</th><th>Título</th><th>Descripción</th></tr>"
    for c in cursos:
        tabla_cursos += f"<tr><td>{c.id}</td><td>{c.titulo}</td><td>{c.descripcion or ''}</td></tr>"
    tabla_cursos += "</table>"

    tabla_inscripciones = "<h3>Inscripciones</h3><table border='1'><tr><th>ID</th><th>Estudiante ID</th><th>Curso ID</th><th>Fecha</th></tr>"
    for i in inscripciones:
        tabla_inscripciones += f"<tr><td>{i.id}</td><td>{i.estudiante_id}</td><td>{i.curso_id}</td><td>{i.fecha_inscripcion}</td></tr>"
    tabla_inscripciones += "</table>"

    formulario = """
    <h2>Agregar Estudiante</h2>
    <form method="POST">
        <input type="hidden" name="tipo" value="estudiante">
        Nombre: <input type="text" name="nombre" required><br>
        Correo: <input type="email" name="correo" required><br>
        <input type="submit" value="Agregar Estudiante">
    </form>

    <h2>Agregar Curso</h2>
    <form method="POST">
        <input type="hidden" name="tipo" value="curso">
        Título: <input type="text" name="titulo" required><br>
        Descripción: <input type="text" name="descripcion"><br>
        <input type="submit" value="Agregar Curso">
    </form>

    <h2>Agregar Inscripción</h2>
    <form method="POST">
        <input type="hidden" name="tipo" value="inscripcion">
        ID Estudiante: <input type="number" name="estudiante_id" required><br>
        ID Curso: <input type="number" name="curso_id" required><br>
        <input type="submit" value="Agregar Inscripción">
    </form>

    <br><a href="/logout">Cerrar sesión 🔒</a>
    """

    return f"<p>{mensaje}</p>{formulario}<br>{tabla_estudiantes}<br>{tabla_cursos}<br>{tabla_inscripciones}"


# --- EJECUCIÓN ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Descomenta si quieres crear usuarios de prueba automáticamente:
        # create_initial_users()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
