import os, sqlite3, csv, io, json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
IS_RENDER = os.environ.get("RENDER") == "true"
SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if IS_RENDER and (not SECRET_KEY or not ADMIN_PASSWORD):
    raise RuntimeError("Configura SECRET_KEY y ADMIN_PASSWORD en las variables de entorno de Render.")
app.secret_key = SECRET_KEY or "clave-local-solo-para-pruebas"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=IS_RENDER)
DB = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "nexus.db"))
ADMIN_PASSWORD = ADMIN_PASSWORD or "clave-local-solo-para-pruebas"

HOUSES = {
    "Aether": {"element":"Aire", "color":"#b9d8ed", "symbol":"✧", "motto":"La mente que se eleva encuentra nuevos caminos.",
               "description":"Aether reúne a quienes valoran la curiosidad, la imaginación y la libertad de explorar. Observan más allá de lo evidente, conectan ideas y se atreven a contemplar posibilidades nuevas."},
    "Terra": {"element":"Tierra", "color":"#8fbd83", "symbol":"❖", "motto":"La fuerza verdadera nace de raíces profundas.",
              "description":"Terra representa la constancia, la lealtad y la paciencia. Sus integrantes construyen con cuidado, protegen lo que aman y saben que los logros duraderos necesitan raíces firmes."},
    "Ignis": {"element":"Fuego", "color":"#e58b55", "symbol":"♨", "motto":"La pasión enciende aquello que parecía imposible.",
              "description":"Ignis acoge a quienes actúan con valentía, iniciativa y determinación. No temen defender sus convicciones, afrontar desafíos y convertir una idea en acción."},
    "Aqua": {"element":"Agua", "color":"#68b9c9", "symbol":"≈", "motto":"La sensibilidad también puede mover montañas.",
             "description":"Aqua representa la empatía, la intuición y la adaptabilidad. Sus integrantes escuchan, comprenden los matices y encuentran maneras creativas de avanzar incluso cuando el camino cambia."}
}

QUESTIONS = [
("Al llegar a una biblioteca antigua descubres una puerta entreabierta que nadie parece haber visto. ¿Qué haces?", [
("Investigo las pistas y trato de descubrir adónde conduce.","Aether"),
("Aviso a los demás y compruebo que sea seguro entrar.","Terra"),
("Entro con decisión; alguien debe dar el primer paso.","Ignis"),
("Me detengo a escuchar y percibir qué hay al otro lado.","Aqua")]),
("Un proyecto grupal está estancado. ¿Cómo ayudas a que avance?", [
("Propongo una idea diferente que cambie la perspectiva.","Aether"),
("Organizo las tareas y establezco un plan realista.","Terra"),
("Animo al grupo y tomo la iniciativa para empezar.","Ignis"),
("Escucho a todos y busco un acuerdo que los incluya.","Aqua")]),
("Encuentras un mapa incompleto con varias rutas. ¿Cuál te atrae?", [
("La ruta desconocida, aunque plantee preguntas.","Aether"),
("La ruta más estable y con señales confiables.","Terra"),
("La ruta difícil que promete un gran desafío.","Ignis"),
("La ruta que serpentea y permite cambiar de dirección.","Aqua")]),
("Un amigo comete un error que afecta al equipo. ¿Qué haces primero?", [
("Busco entender qué ocurrió y cómo evitarlo otra vez.","Aether"),
("Ayudo a reparar el daño y recuperar la confianza.","Terra"),
("Hablo con franqueza y propongo actuar de inmediato.","Ignis"),
("Le doy espacio para explicarse y escucho su versión.","Aqua")]),
("Te entregan una caja cerrada que contiene un objeto misterioso. ¿Qué te emociona más?", [
("Descifrar el mecanismo que la mantiene cerrada.","Aether"),
("Conocer la historia y el valor que tiene para alguien.","Terra"),
("Abrirla y descubrir qué desafío guarda.","Ignis"),
("Imaginar qué recuerdos o emociones puede contener.","Aqua")]),
("Durante una excursión, el clima cambia repentinamente. ¿Cuál es tu reacción?", [
("Analizo el entorno y busco una alternativa ingeniosa.","Aether"),
("Reúno al grupo y verifico que nadie se quede atrás.","Terra"),
("Tomo una decisión rápida para salir del problema.","Ignis"),
("Me adapto al cambio y mantengo la calma del grupo.","Aqua")]),
("¿Qué reconocimiento te haría sentir más orgulloso?", [
("Que valoren mis ideas y mi creatividad.","Aether"),
("Que sepan que siempre pueden contar conmigo.","Terra"),
("Que reconozcan mi valentía y determinación.","Ignis"),
("Que alguien diga que logré comprenderle de verdad.","Aqua")]),
("Una discusión divide a tus compañeros. ¿Qué papel asumirías?", [
("Planteo otra perspectiva para que vean el problema distinto.","Aether"),
("Busco una solución justa y que pueda sostenerse.","Terra"),
("Defiendo con firmeza lo que considero correcto.","Ignis"),
("Intento comprender las emociones detrás de cada postura.","Aqua")]),
("Puedes aprender una habilidad extraordinaria. ¿Cuál escogerías?", [
("Leer símbolos antiguos y descubrir conocimientos ocultos.","Aether"),
("Cultivar un jardín capaz de sanar tierras agotadas.","Terra"),
("Forjar herramientas resistentes en un fuego encantado.","Ignis"),
("Comprender las corrientes y comunicarse con criaturas acuáticas.","Aqua")]),
("Alguien nuevo llega al colegio y parece sentirse fuera de lugar. ¿Qué haces?", [
("Le muestro los rincones interesantes y las actividades.","Aether"),
("Le acompaño y le ayudo a familiarizarse con todo.","Terra"),
("Le invito a participar directamente en una actividad.","Ignis"),
("Me acerco con calma y le pregunto cómo se siente.","Aqua")]),
("Tienes que tomar una decisión importante con poca información. ¿En qué confías más?", [
("En comparar posibilidades y hacer preguntas.","Aether"),
("En lo que ha demostrado ser confiable con el tiempo.","Terra"),
("En mi convicción y capacidad para afrontar consecuencias.","Ignis"),
("En mi intuición y en cómo afecta a las personas implicadas.","Aqua")]),
("¿Qué lugar explorarías durante una tarde libre en Nexus?", [
("Un observatorio lleno de mapas, libros y artefactos.","Aether"),
("Un invernadero silencioso con senderos escondidos.","Terra"),
("Un taller donde se crean objetos y se entrenan habilidades.","Ignis"),
("Un pabellón junto al agua con pasadizos y reflejos.","Aqua")]),
("Cuando algo no sale como esperabas, ¿qué suele ayudarte a continuar?", [
("Imaginar un enfoque completamente distinto.","Aether"),
("Avanzar paso a paso, sin abandonar el objetivo.","Terra"),
("Recordar por qué empecé y volver a intentarlo.","Ignis"),
("Tomarme un momento, reajustarme y seguir adelante.","Aqua")]),
("Te confían un secreto importante. ¿Qué consideras esencial?", [
("Comprender bien la situación antes de actuar.","Aether"),
("Guardar la confianza y proteger a quien lo compartió.","Terra"),
("Estar dispuesto a intervenir si alguien corre peligro.","Ignis"),
("Respetar lo que siente la persona y acompañarla.","Aqua")]),
("Al terminar tu primer año en Nexus, ¿qué te gustaría haber dejado?", [
("Una idea o descubrimiento que abra nuevas posibilidades.","Aether"),
("Una comunidad más unida y un legado duradero.","Terra"),
("Una hazaña que inspire a otros a ser valientes.","Ignis"),
("Vínculos sinceros y recuerdos que permanezcan.","Aqua")])
]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            house TEXT NOT NULL,
            answers TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = " ".join(request.form.get("name", "").strip().split())
        if len(name) < 2:
            flash("Escribe tu nombre para comenzar.")
            return redirect(url_for("home"))
        if len(name) > 70:
            flash("El nombre no puede superar los 70 caracteres.")
            return redirect(url_for("home"))
        session["student_name"] = name
        return redirect(url_for("quiz"))
    return render_template("home.html")

@app.route("/seleccion", methods=["GET", "POST"])
def quiz():
    name = session.get("student_name")
    if not name:
        return redirect(url_for("home"))
    normalized = name.casefold()
    with db() as c:
        existing = c.execute("SELECT * FROM students WHERE normalized_name=?", (normalized,)).fetchone()
    if existing:
        return render_template("result.html", name=existing["name"], house=existing["house"],
                               info=HOUSES[existing["house"]], already=True)
    if request.method == "POST":
        scores = {h: 0 for h in HOUSES}
        answers = []
        for i, q in enumerate(QUESTIONS):
            choice = request.form.get(f"q{i}")
            valid = {str(j): (label, house) for j, (label, house) in enumerate(q[1])}
            if choice not in valid:
                flash("Responde todas las preguntas antes de continuar.")
                return redirect(url_for("quiz"))
            label, house = valid[choice]
            scores[house] += 1
            answers.append({"question": q[0], "answer": label, "house_score": house})
        # Deterministic tie-breaker keeps results reproducible.
        winner = max(HOUSES, key=lambda h: (scores[h], -list(HOUSES).index(h)))
        try:
            with db() as c:
                c.execute("INSERT INTO students(name, normalized_name, house, answers) VALUES(?,?,?,?)",
                          (name, normalized, winner, json.dumps(answers, ensure_ascii=False)))
        except sqlite3.IntegrityError:
            with db() as c:
                row = c.execute("SELECT * FROM students WHERE normalized_name=?", (normalized,)).fetchone()
            winner = row["house"]
        return render_template("result.html", name=name, house=winner, info=HOUSES[winner], already=False)
    return render_template("quiz.html", name=name, questions=QUESTIONS)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/directivos", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        # ADMIN_PASSWORD is supplied as an environment variable on deployment.
        if password and __import__("hmac").compare_digest(password, ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Contraseña incorrecta.")
    return render_template("admin_login.html")

@app.route("/directivos/panel")
@admin_required
def admin():
    with db() as c:
        students = c.execute("SELECT name, house, created_at FROM students ORDER BY created_at DESC").fetchall()
    counts = {h: 0 for h in HOUSES}
    for s in students:
        counts[s["house"]] += 1
    return render_template("admin.html", students=students, counts=counts, houses=HOUSES)

@app.route("/directivos/exportar")
@admin_required
def export_csv():
    with db() as c:
        rows = c.execute("SELECT name, house, created_at, answers FROM students ORDER BY created_at DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Casa", "Fecha", "Respuestas"])
    for r in rows:
        writer.writerow([r["name"], r["house"], r["created_at"], r["answers"]])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=seleccion_nexus.csv"})

@app.route("/directivos/salir")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/salir")
def restart():
    session.pop("student_name", None)
    return redirect(url_for("home"))

@app.context_processor
def inject_houses():
    return {"houses": HOUSES}

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=not IS_RENDER)
