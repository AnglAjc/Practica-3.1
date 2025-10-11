import express from "express";
import bodyParser from "body-parser";
import { Sequelize, DataTypes } from "sequelize";

const app = express();
const port = 5000;

app.use(bodyParser.urlencoded({ extended: true }));

// -----------------------------
// Configuración Neon.tech
// -----------------------------
const sequelize = new Sequelize(
  "postgresql://neondb_owner:npg_sJIC50aAExNc@ep-rough-fog-ad5oueso-pooler.c-2.us-east-1.aws.neon.tech/neondb",
  {
    dialect: "postgres",
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false,
      },
    },
  }
);

// -----------------------------
// Modelos
// -----------------------------
const Estudiante = sequelize.define("Estudiante", {
  nombre: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  correo: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
  },
});

const Curso = sequelize.define("Curso", {
  titulo: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  descripcion: {
    type: DataTypes.TEXT,
  },
});

const Inscripcion = sequelize.define("Inscripcion", {
  fecha_inscripcion: {
    type: DataTypes.DATEONLY,
    defaultValue: Sequelize.NOW,
  },
});

// Relaciones
Estudiante.hasMany(Inscripcion, { onDelete: "CASCADE" });
Curso.hasMany(Inscripcion, { onDelete: "CASCADE" });
Inscripcion.belongsTo(Estudiante);
Inscripcion.belongsTo(Curso);

// -----------------------------
// Ruta principal con formularios
// -----------------------------
app.get("/", async (req, res) => {
  const estudiantes = await Estudiante.findAll();
  const cursos = await Curso.findAll();
  const inscripciones = await Inscripcion.findAll();

  let tablaEstudiantes = `
    <h3>Estudiantes</h3>
    <table border="1"><tr><th>ID</th><th>Nombre</th><th>Correo</th></tr>
    ${estudiantes.map(e => `<tr><td>${e.id}</td><td>${e.nombre}</td><td>${e.correo}</td></tr>`).join("")}
    </table>`;

  let tablaCursos = `
    <h3>Cursos</h3>
    <table border="1"><tr><th>ID</th><th>Título</th><th>Descripción</th></tr>
    ${cursos.map(c => `<tr><td>${c.id}</td><td>${c.titulo}</td><td>${c.descripcion}</td></tr>`).join("")}
    </table>`;

  let tablaInscripciones = `
    <h3>Inscripciones</h3>
    <table border="1"><tr><th>ID</th><th>Estudiante ID</th><th>Curso ID</th><th>Fecha</th></tr>
    ${inscripciones.map(i => `<tr><td>${i.id}</td><td>${i.EstudianteId}</td><td>${i.CursoId}</td><td>${i.fecha_inscripcion}</td></tr>`).join("")}
    </table>`;

  const formulario = `
    <h2>Agregar Estudiante</h2>
    <form method="POST" action="/agregar">
        <input type="hidden" name="tipo" value="estudiante">
        Nombre: <input type="text" name="nombre" required><br>
        Correo: <input type="email" name="correo" required><br>
        <input type="submit" value="Agregar Estudiante">
    </form>

    <h2>Agregar Curso</h2>
    <form method="POST" action="/agregar">
        <input type="hidden" name="tipo" value="curso">
        Título: <input type="text" name="titulo" required><br>
        Descripción: <input type="text" name="descripcion"><br>
        <input type="submit" value="Agregar Curso">
    </form>

    <h2>Agregar Inscripción</h2>
    <form method="POST" action="/agregar">
        <input type="hidden" name="tipo" value="inscripcion">
        ID Estudiante: <input type="number" name="estudiante_id" required><br>
        ID Curso: <input type="number" name="curso_id" required><br>
        <input type="submit" value="Agregar Inscripción">
    </form>
  `;

  res.send(`${formulario}<br>${tablaEstudiantes}<br>${tablaCursos}<br>${tablaInscripciones}`);
});

app.post("/agregar", async (req, res) => {
  const { tipo } = req.body;

  try {
    if (tipo === "estudiante") {
      await Estudiante.create({
        nombre: req.body.nombre,
        correo: req.body.correo,
      });
    } else if (tipo === "curso") {
      await Curso.create({
        titulo: req.body.titulo,
        descripcion: req.body.descripcion,
      });
    } else if (tipo === "inscripcion") {
      await Inscripcion.create({
        EstudianteId: req.body.estudiante_id,
        CursoId: req.body.curso_id,
      });
    }
    res.redirect("/");
  } catch (err) {
    res.send(`Error: ${err.message}`);
  }
});

// -----------------------------
// Ejecutar servidor
// -----------------------------
(async () => {
  try {
    await sequelize.authenticate();
    console.log("✅ Conexión establecida correctamente.");

    await sequelize.sync({ force: true }); // Elimina y crea tablas nuevas
    console.log("🧱 Tablas sincronizadas con éxito.");

    app.listen(port, () => console.log(`🚀 Servidor ejecutándose en http://localhost:${port}`));
  } catch (error) {
    console.error("❌ Error al conectar con la base de datos:", error);
  }
})();
