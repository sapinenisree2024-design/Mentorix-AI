from flask import Flask, render_template, request, redirect, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mentorix_ai_final_key"

DB = "mentorix.db"


# ================= DB =================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


# ================= INIT DB =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        streak INTEGER DEFAULT 0,
        coach TEXT DEFAULT 'strict'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        goal TEXT,
        time TEXT
    )
    """)

    # ✅ ADD (REAL GRAPH TABLE)
    c.execute("""
    CREATE TABLE IF NOT EXISTS focus_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================
@app.route("/")
def home():
    return redirect("/login")


# ================= SIGNUP =================
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    db = get_db()

    try:
        db.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, password)
        )
        db.commit()
    except:
        return "User already exists ❌"

    session["user"] = username
    return redirect("/dashboard")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT username FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if not user:
            return "❌ Invalid login"

        session["user"] = user[0]
        return redirect("/dashboard")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    db = get_db()
    user_name = session.get("user")

    if not user_name:
        return render_template("dashboard.html",
                               username="Guest",
                               streak=0,
                               coach="none")

    user = db.execute(
        "SELECT streak, coach FROM users WHERE username=?",
        (user_name,)
    ).fetchone()

    if not user:
        return render_template("dashboard.html",
                               username="Guest",
                               streak=0,
                               coach="none")

    return render_template("dashboard.html",
                           username=user_name,
                           streak=user[0],
                           coach=user[1])


# ================= STREAK =================
@app.route("/streak", methods=["POST"])
def streak():
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    try:
        streak_value = int(request.form.get("streak", 0))
    except:
        streak_value = 0

    db.execute(
        "UPDATE users SET streak=? WHERE username=?",
        (streak_value, session["user"])
    )
    db.commit()

    return redirect("/dashboard")


# ================= COACH =================
@app.route("/set_coach", methods=["POST"])
def set_coach():
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    db.execute(
        "UPDATE users SET coach=? WHERE username=?",
        (request.form["coach"], session["user"])
    )
    db.commit()

    return redirect("/dashboard")


# ================= GOAL (FIXED + GRAPH SAVE) =================
@app.route("/goal", methods=["POST"])
def goal():
    if "user" not in session:
        return redirect("/dashboard")

    goal_text = request.form.get("goal", "").strip()

    if not goal_text:
        return redirect("/dashboard")

    db = get_db()

    db.execute(
        "INSERT INTO goals(username,goal,time) VALUES(?,?,?)",
        (session["user"], goal_text, str(datetime.now()))
    )

    # ✅ REAL GRAPH DATA
    today = datetime.now().strftime("%Y-%m-%d")
    db.execute(
        "INSERT INTO focus_log(username,date,score) VALUES(?,?,?)",
        (session["user"], today, 50)
    )

    db.commit()

    goal_id = db.execute(
        "SELECT id FROM goals WHERE username=? ORDER BY id DESC LIMIT 1",
        (session["user"],)
    ).fetchone()

    return redirect(f"/mentor/{goal_id[0]}")


# ================= MENTOR =================
@app.route("/mentor/<int:id>")
def mentor(id):
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    goal = db.execute(
        "SELECT goal,time FROM goals WHERE id=? AND username=?",
        (id, session["user"])
    ).fetchone()

    if not goal:
        return redirect("/dashboard")

    coach_data = db.execute(
        "SELECT coach FROM users WHERE username=?",
        (session["user"],)
    ).fetchone()

    coach = coach_data[0] if coach_data else "strict"
    goal_text = goal[0]

    if coach == "strict":
        response = f"""🧠 MENTOR AI (STRICT MODE)

🎯 Goal: {goal_text}
⚠ No excuses.
🔥 Discipline first.
⏱ Work NOW.
🚫 No distractions."""

    elif coach == "motivator":
        response = f"""🔥 MENTOR AI (MOTIVATOR MODE)

🎯 Goal: {goal_text}
💪 You are powerful.
🚀 Start NOW.
✨ Keep going."""

    elif coach == "chill":
        response = f"""😌 MENTOR AI (CHILL MODE)

🎯 Goal: {goal_text}
🌿 Relax & focus.
⏱ Take it easy but start."""

    else:
        response = f"""😊 MENTOR AI (FRIENDLY MODE)

🎯 Goal: {goal_text}
🌟 You are doing great!
🔥 Keep going!"""

    return render_template(
        "mentor.html",
        goal=goal_text,
        time=goal[1],
        coach=coach,
        response=response
    )


# ================= FOCUS (REAL GRAPH DATA) =================
@app.route("/focus")
def focus():
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    rows = db.execute("""
        SELECT date, score
        FROM focus_log
        WHERE username=?
        ORDER BY date ASC
    """, (session["user"],)).fetchall()

    # Convert DB → JS arrays
    labels = [row[0] for row in rows]
    scores = [row[1] for row in rows]

    return render_template(
        "focus.html",
        labels=labels,
        scores=scores
    )

# ================= LEADERBOARD =================
# ================= LEADERBOARD =================
# ================= LEADERBOARD =================
@app.route("/leaderboard")
def leaderboard():

    db = get_db()

    users = db.execute("""
        SELECT u.username,
        COALESCE(
            (
                SELECT score
                FROM focus_log f
                WHERE f.username = u.username
                ORDER BY f.id DESC
                LIMIT 1
            ), 0
        ) as total_score

        FROM users u
        ORDER BY total_score DESC
    """).fetchall()

    return render_template("leaderboard.html", users=users)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# ================= HISTORY (ADD IF MISSING) =================
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    data = db.execute("""
        SELECT id, goal, time
        FROM goals
        WHERE username=?
        ORDER BY id DESC
    """, (session["user"],)).fetchall()

    return render_template("history.html", history=data)
# ================= DELETE GOAL =================
@app.route("/delete_goal/<int:id>")
def delete_goal(id):
    if "user" not in session:
        return redirect("/dashboard")

    db = get_db()

    db.execute("""
        DELETE FROM goals
        WHERE id=? AND username=?
    """, (id, session["user"]))

    db.commit()

    return redirect("/history")

@app.route("/save_focus", methods=["POST"])
def save_focus():
    if "user" not in session:
        return {"status": "no-user"}

    data = request.get_json()
    score = int(data.get("score", 0))
    today = datetime.now().strftime("%Y-%m-%d")

    username = session["user"]
    db = get_db()

    # FORCE clean update logic
    db.execute("""
        DELETE FROM focus_log
        WHERE username=? AND date=?
    """, (username, today))

    db.execute("""
        INSERT INTO focus_log(username,date,score)
        VALUES(?,?,?)
    """, (username, today, score))

    db.commit()

    print("UPDATED:", username, score)

    return {"status": "saved"}
# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)