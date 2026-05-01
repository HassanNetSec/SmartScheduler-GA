import streamlit as st
import pandas as pd
import json
from datetime import datetime

# ── GA engine (code.py lives alongside this file) ──────────────────────────
from HelperFunction.TimeTableCreater import (
    GIKI_ROOMS,
    GeneticAlgorithm,
    MAX_SLOTS,
    LEC_DAY_PATTERNS,
    LAB_DAY_PATTERNS,
    format_time,
)
from HelperFunction.export_grid import export_grid_pdf
from HelperFunction.Validator   import validate_courses_df
from HelperFunction.GridView    import render_grid_view

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

DAYS_SHORT = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT"}
DAYS_LONG  = {
    "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
    "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday",
}

# ═══════════════════════════════════════════════════════════════
# TIME / SLOT HELPERS  (replaces old SLOTS / LAB_BLOCKS helpers)
# ═══════════════════════════════════════════════════════════════

def _slot_to_time(slot_idx: int) -> str:
    """Half-hour slot index → 'HH:MM' string."""
    h = 8 + slot_idx // 2
    m = "00" if slot_idx % 2 == 0 else "30"
    return f"{h:02d}:{m}"


def timeslot_str(days: list, start: int, length: int) -> str:
    """
    Build a canonical timeslot key used throughout the app.
    For lectures (multi-day) we store one key per day joined by '+':
        "MON+WED+FRI-08:00"
    For labs (single day):
        "MON-08:00"
    """
    day_part  = "+".join(DAYS_SHORT[d] for d in days)
    time_part = _slot_to_time(start)
    return f"{day_part}-{time_part}"


def parse_timeslot(ts: str):
    """
    Inverse of timeslot_str.
    Returns (day_shorts: list[str], time_str: str)
    e.g. "MON+WED+FRI-08:00" → (["MON","WED","FRI"], "08:00")
    """
    day_part, time_part = ts.rsplit("-", 1)
    return day_part.split("+"), time_part


def format_timeslot_display(ts: str, is_lab: bool) -> str:
    """Human-readable time range from a timeslot key."""
    _, time_part = ts.rsplit("-", 1)
    # Reconstruct start slot index
    h, m   = map(int, time_part.split(":"))
    start  = (h - 8) * 2 + (1 if m == 30 else 0)
    length = 6 if is_lab else 2
    return format_time(start, length)


def slots_occupied_by(ts: str, is_lab: bool) -> set:
    """
    Return a set of (day_short, slot_idx) tuples that this assignment occupies.
    Used by detect_clashes and try_move.
    """
    day_shorts, time_part = parse_timeslot(ts)
    h, m   = map(int, time_part.split(":"))
    start  = (h - 8) * 2 + (1 if m == 30 else 0)
    length = 6 if is_lab else 2
    occupied = set()
    for d in day_shorts:
        for s in range(start, start + length):
            occupied.add((d, s))
    return occupied


# ═══════════════════════════════════════════════════════════════
# DATA BUILDER  (CSV → GA data dict)
# ═══════════════════════════════════════════════════════════════

def build_ga_data(df: pd.DataFrame) -> dict:
    """Convert the uploaded DataFrame into the dict expected by GeneticAlgorithm."""

    rooms = {
        i: [r["name"], r["type"], None, r["capacity"]]
        for i, r in enumerate(GIKI_ROOMS)
    }

    # Teachers — split comma-separated names
    all_teachers = []
    for raw in df["teacher"].unique():
        for name in [n.strip() for n in str(raw).split(",")]:
            if name and name not in all_teachers:
                all_teachers.append(name)
    instructors        = {i: [name, 30] for i, name in enumerate(all_teachers)}
    teacher_name_to_id = {v[0]: k for k, v in instructors.items()}

    # Groups / sections
    groups           = list(df["group"].unique())
    group_name_to_id = {g: i for i, g in enumerate(groups)}
    sections         = {i: [g, None, []] for i, g in enumerate(groups)}

    # Subjects
    subjects = {}
    for idx, row in df.iterrows():
        grp_id       = group_name_to_id[row["group"]]
        teacher_names = [n.strip() for n in str(row["teacher"]).split(",")]
        inst_ids      = [teacher_name_to_id[n] for n in teacher_names if n in teacher_name_to_id]

        subjects[idx] = [
            row["course"],                       # 0  name
            float(row["credit_hours"]),          # 1  credits
            [grp_id],                            # 2  section ids
            [idx],                               # 3  subject id list
            inst_ids,                            # 4  instructor ids
            True,                                # 5  active
            "lab" if row["is_lab"] else "lec",   # 6  type
            int(row["students"]),                # 7  student count
        ]
        sections[grp_id][2].append(idx)

    return {
        "rooms":       rooms,
        "instructors": instructors,
        "sections":    sections,
        "subjects":    subjects,
    }


# ═══════════════════════════════════════════════════════════════
# GA RUNNER  (replaces run_generator / TimeTableCreater)
# ═══════════════════════════════════════════════════════════════

def run_ga(df: pd.DataFrame) -> dict:
    """
    Run the GA on df and return:
        {success, scheduled, unplaced_count}

    Each 'scheduled' item:
        {course, teacher, group, timeslot, room, is_lab, students}
    """
    data = build_ga_data(df)
    ga   = GeneticAlgorithm(data)
    best = ga.run()

    rooms      = data["rooms"]
    sections   = data["sections"]
    subjects   = data["subjects"]
    instructors = data["instructors"]

    scheduled = []
    for s_id, s in best.data["sections"].items():
        for sub_id, d in s["details"].items():
            r_id, inst_id, days, start, length = d

            # Resolve teacher name from instructor id
            teacher_name = instructors[inst_id][0] if inst_id is not None else "TBA"

            scheduled.append({
                "course":   subjects[sub_id][0],
                "teacher":  teacher_name,
                "group":    sections[s_id][0],
                "timeslot": timeslot_str(days, start, length),
                "room":     rooms[r_id][0],
                "is_lab":   subjects[sub_id][6] == "lab",
                "students": subjects[sub_id][7],
            })

    unplaced = sum(len(v) for v in best.data["unplaced"]["sections"].values())

    return {
        "success":       True,
        "scheduled":     scheduled,
        "unplaced_count": unplaced,
    }


# ═══════════════════════════════════════════════════════════════
# OUTPUT HELPERS
# ═══════════════════════════════════════════════════════════════

def build_df(scheduled: list) -> pd.DataFrame:
    rows = []
    for item in scheduled:
        ts        = item["timeslot"]
        is_lab    = item.get("is_lab", False)
        day_shorts, _ = parse_timeslot(ts)
        day_display   = " / ".join(DAYS_LONG.get(d, d) for d in day_shorts)

        rows.append({
            "Course":   item["course"],
            "Teacher":  item["teacher"],
            "Room":     item["room"],
            "Group":    item["group"],
            "Day":      day_display,
            "Time":     format_timeslot_display(ts, is_lab),
            "Type":     "LAB" if is_lab else "THEORY",
            "Students": item.get("students", ""),
        })
    return pd.DataFrame(rows)


def detect_clashes(scheduled: list) -> list:
    clashes = []
    for i in range(len(scheduled)):
        for j in range(i + 1, len(scheduled)):
            c1, c2 = scheduled[i], scheduled[j]
            if c1["group"] != c2["group"]:
                continue
            s1 = slots_occupied_by(c1["timeslot"], c1.get("is_lab", False))
            s2 = slots_occupied_by(c2["timeslot"], c2.get("is_lab", False))
            if s1 & s2:
                clashes.append({
                    "senior_course": c1["course"],
                    "senior_group":  c1["group"],
                    "junior_course": c2["course"],
                    "junior_group":  c2["group"],
                    "timeslot":      c1["timeslot"],
                })
    return clashes


# ═══════════════════════════════════════════════════════════════
# CLASH RESOLVER
# ═══════════════════════════════════════════════════════════════

def _build_busy_sets(scheduled: list, exclude_course: str = None):
    teacher_busy: dict = {}
    group_busy:   dict = {}
    room_busy:    dict = {}

    for item in scheduled:
        if item["course"] == exclude_course:
            continue
        occ = slots_occupied_by(item["timeslot"], item.get("is_lab", False))
        teacher_busy.setdefault(item["teacher"], set()).update(occ)
        group_busy.setdefault(  item["group"],   set()).update(occ)
        room_busy.setdefault(   item["room"],    set()).update(occ)

    return teacher_busy, group_busy, room_busy


def try_move(item_to_move: dict, all_scheduled: list) -> tuple:
    """
    Try every (days_pattern, start_slot, room) combination for item_to_move.
    Returns (new_scheduled, True) on success, (None, False) otherwise.
    """
    is_lab   = item_to_move.get("is_lab", False)
    length   = 6 if is_lab else 2
    patterns = LAB_DAY_PATTERNS if is_lab else LEC_DAY_PATTERNS

    teacher_busy, group_busy, room_busy = _build_busy_sets(
        all_scheduled, exclude_course=item_to_move["course"]
    )

    rooms_list = [r["name"] for r in GIKI_ROOMS if r["type"] == ("lab" if is_lab else "lec")]

    for days in patterns:
        for start in range(MAX_SLOTS - length + 1):
            candidate_ts = timeslot_str(days, start, length)
            if candidate_ts == item_to_move["timeslot"]:
                continue

            occ = slots_occupied_by(candidate_ts, is_lab)
            t   = item_to_move["teacher"]
            g   = item_to_move["group"]

            if any(s in teacher_busy.get(t, set()) for s in occ):
                continue
            if any(s in group_busy.get(g, set()) for s in occ):
                continue

            for room in rooms_list:
                if any(s in room_busy.get(room, set()) for s in occ):
                    continue

                new_item  = {**item_to_move, "timeslot": candidate_ts, "room": room}
                new_sched = [x for x in all_scheduled if x["course"] != item_to_move["course"]]
                new_sched.append(new_item)
                return new_sched, True

    return None, False


# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="Timetable Gen Pro", layout="wide")
st.title("📅 TimeTable Generator")

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

if "course_data" not in st.session_state:
    st.session_state.course_data = pd.DataFrame(columns=[
        "course", "teacher", "group", "credit_hours", "is_lab", "students"
    ])

if "timetable_result" not in st.session_state:
    st.session_state.timetable_result = None

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("🛠️ Control Panel")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state.course_data = df
        st.success("Uploaded!")
    st.caption("Expected columns: `course`, `teacher`, `group`, `credit_hours`, `is_lab`, `students`")

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["Data", "Timetable", "Clash Resolver"])

# ─────────────────────────────────────────────────────────────
with tab1:
    df = st.session_state.course_data

    st.subheader("Course Data")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "course":       st.column_config.TextColumn("Course",       required=True),
            "teacher":      st.column_config.TextColumn("Teacher",      required=True),
            "group":        st.column_config.TextColumn("Group",        help="e.g. BCS-6A", required=True),
            "credit_hours": st.column_config.NumberColumn("Credit Hours", min_value=1, max_value=4, step=1),
            "is_lab":       st.column_config.CheckboxColumn("Is Lab?"),
            "students":     st.column_config.NumberColumn("Students",   min_value=1),
        },
    )

    st.session_state.course_data = edited_df
    st.divider()

    if st.button("Validate & Generate", type="primary", use_container_width=True):
        result = validate_courses_df(edited_df)

        # if result.warnings:
        #     for w in result.warnings:
        #         st.warning(w, icon="⚠️")

        if not result.is_valid:
            st.error(
                f"**{len(result.errors)} validation error(s) found. Fix these before generating:**",
                icon="🚫",
            )
            for i, err in enumerate(result.errors, 1):
                st.markdown(f"&nbsp;&nbsp;`{i}.` {err}")
            st.info(
                "**Expected CSV format:**\n\n"
                "| course | teacher | group | credit_hours | is_lab | students |\n"
                "|--------|---------|-------|--------------|--------|----------|\n"
                "| CS301 | Dr. Ahmed | BCS-6A | 3 | False | 40 |\n"
                "| CS301L | Dr. Ahmed | BCS-6A | 1 | True  | 40 |",
                icon="ℹ️",
            )
        else:
            st.success(f"Validation passed — {len(result.cleaned_df)} courses ready.", icon="✅")
            st.session_state.course_data = result.cleaned_df

            with st.spinner("Running GA… this may take ~30 seconds"):
                try:
                    gen_result = run_ga(result.cleaned_df)
                    gen_result["clashes"] = detect_clashes(gen_result["scheduled"])
                    st.session_state.timetable_result = gen_result
                except Exception as e:
                    st.error(f"GA failed: {e}", icon="❌")
                    st.stop()

            placed   = len(gen_result["scheduled"])
            unplaced = gen_result["unplaced_count"]
            total    = placed + unplaced
            clashes  = len(gen_result["clashes"])

            if unplaced == 0 and clashes == 0:
                st.success(f"All {total} courses scheduled with no clashes! 🎉", icon="✅")
            # elif clashes == 0:
            #     # st.warning(
            #     #     f"Scheduled **{placed}/{total}** courses. "
            #     #     f"**{unplaced}** could not be placed (likely a group has >18 courses/week — "
            #     #     "split into sub-batches to fix).",
            #     #     icon="⚠️",
            #     # )
            else:
                st.warning(
                    f"Scheduled {placed}/{total} courses with **{clashes} clash(es)**. "
                    "Go to the Clash Resolver tab.",
                    icon="⚠️",
                )

# ─────────────────────────────────────────────────────────────
with tab2:
    result = st.session_state.get("timetable_result")

    if not result:
        st.info("Generate a timetable in the Data tab first.")
    else:
        res_df = build_df(result["scheduled"])

        view_mode = st.radio(
            "View as", ["Weekly Grid", "Data Table"],
            horizontal=True, label_visibility="collapsed", key="view_toggle",
        )
        st.divider()

        if view_mode == "Weekly Grid":
            render_grid_view(result)
        else:
            st.dataframe(res_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Export Options")
        dl1, dl2 = st.columns(2)

        with dl1:
            with st.spinner("Preparing PDF…"):
                try:
                    pdf_bytes = export_grid_pdf(result["scheduled"])
                    st.download_button(
                        label="📄 Download PDF (Poster Layout)",
                        data=pdf_bytes,
                        file_name=f"GIKI_Timetable_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"PDF error: {e}")

        with dl2:
            csv_data = res_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"timetable_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        clashes = result.get("clashes", [])
        if clashes:
            with st.expander(f"⚠️ Scheduling Alerts ({len(clashes)})"):
                for c in clashes:
                    st.warning(
                        f"{c['senior_course']} ({c['senior_group']}) clashes with "
                        f"{c['junior_course']} ({c['junior_group']}) at {c['timeslot']}"
                    )

# ─────────────────────────────────────────────────────────────
with tab3:
    st.subheader("⚠️ Clash Resolver (Admin Mode)")
    result = st.session_state.timetable_result

    if result is None:
        st.info("Please generate a timetable in the Data tab first.")
    else:
        scheduled = result["scheduled"]

        st.markdown("### Enter Clash Details")
        col1, col2 = st.columns(2)
        with col1:
            senior_course  = st.text_input("🎓 Senior Course").strip()
            senior_section = st.text_input("Senior Group").strip().upper()
        with col2:
            junior_course  = st.text_input("📚 Junior Course").strip()
            junior_section = st.text_input("Junior Group").strip().upper()

        if st.button("🔧 Resolve Clash", type="primary"):
            if not all([senior_course, senior_section, junior_course, junior_section]):
                st.warning("Please fill all four fields.")
            else:
                def find_item(course, section):
                    return next(
                        (x for x in scheduled
                         if x["course"].strip() == course
                         and x["group"].strip().upper() == section),
                        None,
                    )

                senior_item = find_item(senior_course, senior_section)
                junior_item = find_item(junior_course, junior_section)

                if not senior_item or not junior_item:
                    st.error(
                        f"❌ Could not find: '{senior_course}/{senior_section}' "
                        f"or '{junior_course}/{junior_section}' in the schedule."
                    )
                else:
                    st.info("Searching for a conflict-free slot…")

                    new_sched, ok = try_move(junior_item, scheduled)
                    moved_label = "Junior"

                    if not ok:
                        new_sched, ok = try_move(senior_item, scheduled)
                        moved_label = "Senior"

                    if ok:
                        st.success(f"✅ Resolved! Moved {moved_label} course to a new slot.")
                        result["scheduled"] = new_sched
                        result["clashes"]   = detect_clashes(new_sched)
                        st.session_state.timetable_result = result
                        st.rerun()
                    else:
                        st.error(
                            "❌ No available slots found. "
                            "Try splitting large groups into sub-batches."
                        )