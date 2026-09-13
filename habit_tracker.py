import streamlit as st
import sqlite3
from datetime import date, timedelta

# ---------- DATABASE SETUP ----------
DB_NAME = "habits.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Table 1: list of habits
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    # Table 2: which habit was done on which date
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            UNIQUE(habit_id, log_date),
            FOREIGN KEY(habit_id) REFERENCES habits(id)
        )
    """)
    conn.commit()
    conn.close()

# ---------- DATABASE HELPER FUNCTIONS ----------
def add_habit(name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO habits (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # habit already exists
    conn.close()

def get_habits():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM habits ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_habit(habit_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM logs WHERE habit_id = ?", (habit_id,))
    cur.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()

def mark_done(habit_id, log_date):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO logs (habit_id, log_date) VALUES (?, ?)",
            (habit_id, log_date.isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already marked done for that date
    conn.close()

def is_done_today(habit_id, log_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM logs WHERE habit_id = ? AND log_date = ?",
        (habit_id, log_date.isoformat())
    )
    result = cur.fetchone()
    conn.close()
    return result is not None

def get_all_dates(habit_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT log_date FROM logs WHERE habit_id = ?", (habit_id,))
    rows = cur.fetchall()
    conn.close()
    return set(row[0] for row in rows)

def calculate_streak(habit_id):
    """Counts consecutive days ending today (or yesterday) that are marked done."""
    done_dates = get_all_dates(habit_id)
    streak = 0
    current_day = date.today()

    # If today isn't done yet, streak calculation still starts checking from today.
    # If today isn't marked, we check if yesterday was the last done day (streak continues but shows 0 for today).
    if current_day.isoformat() not in done_dates:
        current_day = current_day - timedelta(days=1)

    while current_day.isoformat() in done_dates:
        streak += 1
        current_day = current_day - timedelta(days=1)

    return streak

# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="Habit Tracker", page_icon="✅")
init_db()

st.title("✅ Habit Tracker")
st.caption("Build habits, one day at a time.")

# --- Add new habit ---
st.subheader("Add a new habit")
col1, col2 = st.columns([3, 1])
with col1:
    new_habit = st.text_input("Habit name", placeholder="e.g. Drink water, Read, Exercise")
with col2:
    st.write("")  # spacing to align button
    st.write("")
    if st.button("Add Habit"):
        if new_habit.strip():
            add_habit(new_habit.strip())
            st.rerun()
        else:
            st.warning("Please type a habit name first.")

st.divider()

# --- Show all habits ---
st.subheader("Your habits")
habits = get_habits()
today = date.today()

if not habits:
    st.info("No habits yet. Add one above to get started!")
else:
    for habit_id, habit_name in habits:
        done_today = is_done_today(habit_id, today)
        streak = calculate_streak(habit_id)

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"**{habit_name}**")
        with col2:
            if done_today:
                st.success("Done today ✅")
            else:
                if st.button("Mark done", key=f"done_{habit_id}"):
                    mark_done(habit_id, today)
                    st.rerun()
        with col3:
            st.metric("🔥 Streak", f"{streak} day{'s' if streak != 1 else ''}")
        with col4:
            if st.button("🗑️", key=f"del_{habit_id}"):
                delete_habit(habit_id)
                st.rerun()

    st.divider()
    st.caption("Streak = number of consecutive days (up to today) you've marked this habit done.")