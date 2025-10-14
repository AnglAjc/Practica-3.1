from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuración Neon.tech
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos
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

# Ruta principal
@app.route("/", methods=["GET", "POST"])
def index():
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
    """

    return f"{mensaje}<br>{formulario}<br>{tabla_estudiantes}<br>{tabla_cursos}<br>{tabla_inscripciones}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
