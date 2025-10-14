from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# -----------------------------
# Configuración Neon.tech
# -----------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------
# Modelos
# -----------------------------
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
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id", ondelete="CASCADE"))
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id", ondelete="CASCADE"))
    fecha_inscripcion = db.Column(db.Date, server_default=db.func.current_date())
    __table_args__ = (db.UniqueConstraint('estudiante_id', 'curso_id', name='_est_curso_uc'),)


# -----------------------------
# Ruta principal
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = ""

    if request.method == "POST":
        try:
            tipo = request.form["tipo"]

            if tipo == "estudiante":
                nombre = request.form["nombre"]
                correo = request.form["correo"]
                nuevo = Estudiante(nombre=nombre, correo=correo)
                db.session.add(nuevo)

            elif tipo == "curso":
                titulo = request.form["titulo"]
                descripcion = request.form["descripcion"]
                nuevo = Curso(titulo=titulo, descripcion=descripcion)
                db.session.add(nuevo)

            elif tipo == "inscripcion":
                estudiante_id = int(request.form["estudiante_id"])
                curso_id = int(request.form["curso_id"])
                nuevo = Inscripcion(estudiante_id=estudiante_id, curso_id=curso_id)
                db.session.add(nuevo)

            db.session.commit()
            mensaje = "Dato agregado correctamente ✅"

        except Exception as e:
            db.session.rollback()
            mensaje = f"❌ Error: {e}"

    estudiantes = Estudiante.query.all()
    cursos = Curso.query.all()
    inscripciones = Inscripcion.query.all()

    tabla_estudiantes = "<h3>Estudiantes</h3><table border='1'><tr><th>ID</th><th>Nombre</th><th>Correo</th></tr>"
    for e in estudiantes:
        tabla_estudiantes += f"<tr><td>{e.id}</td><td>{e.nombre}</td><td>{e.correo}</td></tr>"
    tabla_estudiantes += "</table>"

    tabla_cursos = "<h3>Cursos</h3><table border='1'><tr><th>ID</th><th>Título</th><th>Descripción</th></tr>"
    for c in cursos:
        tabla_cursos += f"<tr><td>{c.id}</td><td>{c.titulo}</td><td>{c.descripcion}</td></tr>"
    tabla_cursos += "</table>"

    tabla_inscripciones = "<h3>Inscripciones</h3><table border='1'><tr><th>ID</th><th>Estudiante ID</th><th>Curso ID</th><th>Fecha</th></tr>"
    for i in inscripciones:
        tabla_inscripciones += f"<tr><td>{i.id}</td><td>{i.estudiante_id}</td><td>{i.curso_id}</td><td>{i.fecha_inscripcion}</td></tr>"
    tabla_inscripciones += "</table>"

    formulario = """..."""  # igual al original

    return f"{mensaje}<br>{formulario}<br>{tabla_estudiantes}<br>{tabla_cursos}<br>{tabla_inscripciones}"

# -----------------------------
# Ejecutar servidor
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
