import pandas as pd
import streamlit as st

# =====================================================
# CONSTANTS
# =====================================================

DAY_ORDER  = ["MON", "TUE", "WED", "THU", "FRI"]
DAY_LABELS = {
    "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
    "THU": "Thursday", "FRI": "Friday",
}

TIME_ORDER = [
    "08:00", "08:10", "08:20", "08:30", "08:40", "08:50",
    "09:00", "09:10", "09:20", "09:30", "09:40", "09:50",
    "10:00", "10:10", "10:20", "10:30", "10:40", "10:50",
    "11:00", "11:10", "11:20", "11:30", "11:40", "11:50",
    "12:00", "12:10", "12:20", "12:30", "12:40", "12:50",
    "13:00", "13:10", "13:20", "13:30", "13:40", "13:50",
    "14:00", "14:10", "14:20", "14:30", "14:40", "14:50",
    "15:00", "15:10", "15:20", "15:30", "15:40", "15:50",
    "16:00", "16:10", "16:20", "16:30", "16:40", "16:50",
]

SLOT_UNIT  = 10        # minutes per slot — must match TimeTableCreater.py
DAY_START  = 8 * 60   # 08:00 in minutes
LEC_LENGTH = 5         # slots
LAB_LENGTH = 18        # slots

SECTION_PALETTE = [
    ("#DBEAFE", "#1E3A5F"),
    ("#D1FAE5", "#134E2A"),
    ("#FEF3C7", "#78350F"),
    ("#FCE7F3", "#831843"),
    ("#EDE9FE", "#3B0764"),
    ("#FFEDD5", "#7C2D12"),
    ("#CFFAFE", "#164E63"),
    ("#F0FDF4", "#14532D"),
    ("#FEE2E2", "#7F1D1D"),
    ("#F5F3FF", "#2E1065"),
    ("#ECFDF5", "#022C22"),
    ("#FFF7ED", "#431407"),
]

LAB_SUFFIX = " ★"
EMPTY_CELL = "—"


# =====================================================
# SLOT ↔ TIME HELPERS  (10-min slot system)
# =====================================================

def _time_to_slot(time_str: str) -> int:
    """'HH:MM' → 10-min slot index from 08:00."""
    h, m = map(int, time_str.split(":"))
    return ((h * 60 + m) - DAY_START) // SLOT_UNIT


def _slot_to_time(slot_idx: int) -> str:
    """10-min slot index → 'HH:MM'."""
    total = DAY_START + slot_idx * SLOT_UNIT
    return f"{total // 60:02d}:{total % 60:02d}"


def _all_slots_for(start_time: str, is_lab: bool) -> list:
    """
    Return all 'HH:MM' time strings occupied by a course starting at start_time.
    Lecture: 5 slots × 10 min = 50 min
    Lab    : 18 slots × 10 min = 180 min
    """
    start_slot = _time_to_slot(start_time)
    length     = LAB_LENGTH if is_lab else LEC_LENGTH
    return [
        _slot_to_time(start_slot + i)
        for i in range(length)
        if _slot_to_time(start_slot + i) in TIME_ORDER   # stay in bounds
    ]


# =====================================================
# PARSE SLOT STRING  (supports multi-day keys)
#
# "MON-08:00"         → [("MON", "08:00")]
# "MON+WED+FRI-08:00" → [("MON","08:00"),("WED","08:00"),("FRI","08:00")]
# "TUE+THU-10:00"     → [("TUE","10:00"),("THU","10:00")]
# =====================================================

def _parse_slot(slot: str) -> list:
    """
    Returns a list of (day_short, time_str) tuples.
    Uses rsplit on '-' so the HH:MM part is always safe.
    """
    day_part, time_part = slot.rsplit("-", 1)
    return [(d.strip(), time_part) for d in day_part.split("+")]


# =====================================================
# BUILD PIVOT TABLE
# Returns a styled HTML string for st.markdown()
# =====================================================

def build_grid(
    scheduled: list,
    section_filter: list = None,
    show_room: bool = True,
) -> tuple:
    if not scheduled:
        return "<p style='color:gray'>No timetable data.</p>", {}

    sections  = sorted({item["group"] for item in scheduled})
    color_map = {
        sec: SECTION_PALETTE[i % len(SECTION_PALETTE)]
        for i, sec in enumerate(sections)
    }

    data = scheduled
    if section_filter:
        data = [x for x in scheduled if x["group"] in section_filter]

    # --------------------------------------------------
    # Build cell_map: (day, time) → list of (label, section, is_lab)
    # Each course fills ALL its occupied time slots, not just the start
    # --------------------------------------------------
    cell_map:   dict = {}
    used_times: set  = set()

    for item in data:
        is_lab = item.get("is_lab", False)

        label = item["course"]
        if show_room:
            label += f"\n{item['room']}"
        label += f"\n{item['group']}"
        if is_lab:
            label += LAB_SUFFIX

        for day, start_time in _parse_slot(item["timeslot"]):
            # ✅ Fill every 10-min slot the course occupies
            for time in _all_slots_for(start_time, is_lab):
                key = (day, time)
                # Only store label on the START slot; rest get a continuation marker
                if time == start_time:
                    cell_map.setdefault(key, []).append(
                        (label, item["group"], is_lab, "start")
                    )
                else:
                    cell_map.setdefault(key, []).append(
                        (label, item["group"], is_lab, "cont")
                    )
                used_times.add(time)

    # Only show time rows that have at least one entry, in canonical order
    active_times = [t for t in TIME_ORDER if t in used_times]
    active_days  = [
        d for d in DAY_ORDER
        if any((d, t) in cell_map for t in active_times)
    ]

    if not active_times or not active_days:
        return "<p style='color:gray'>No placeable courses in the timetable.</p>", {}

    rows_html = ""

    # Header row
    header_cells = f"<th style='{_th_style(is_time=True)}'>Day / Time</th>"
    for time in active_times:
        header_cells += f"<th style='{_th_style()}'>{time}</th>"
    rows_html += f"<tr>{header_cells}</tr>"

    # Data rows
    for i, day in enumerate(active_days):
        row_bg     = "#FAFAFA" if i % 2 == 0 else "#FFFFFF"
        cells_html = (
            f"<td style='{_time_cell_style(row_bg)}'>"
            f"{DAY_LABELS.get(day, day)}</td>"
        )

        for time in active_times:
            entries = cell_map.get((day, time), [])

            if not entries:
                cells_html += f"<td style='{_empty_cell_style(row_bg)}'>{EMPTY_CELL}</td>"
            else:
                inner = ""
                for label, section, is_lab, slot_type in entries:
                    bg, fg = color_map.get(section, ("#F3F4F6", "#111827"))
                    border = "2px solid rgba(0,0,0,0.25)" if is_lab else "none"

                    if slot_type == "start":
                        # Full pill with course name + details
                        lines       = label.split("\n")
                        course_line = (
                            f"<span style='font-weight:600;font-size:11px'>"
                            f"{lines[0]}</span>"
                        )
                        rest_lines = "".join(
                            f"<span style='display:block;font-size:9px;"
                            f"opacity:0.8'>{l}</span>"
                            for l in lines[1:]
                        )
                        inner += (
                            f"<div style='{_pill_style(bg, fg, border)}'>"
                            f"{course_line}{rest_lines}</div>"
                        )
                    else:
                        # Continuation slot — subtle shaded bar, no repeated text
                        inner += (
                            f"<div style='{_cont_pill_style(bg, border)}'></div>"
                        )

                cells_html += f"<td style='{_data_cell_style(row_bg)}'>{inner}</td>"

        rows_html += f"<tr>{cells_html}</tr>"

    # Split into thead / tbody
    first_tr_end = rows_html.find("</tr>") + 5
    html = f"""
    <div style='overflow-x:auto;margin-bottom:1rem'>
    <table style='{_table_style()}'>
      <thead>{rows_html[:first_tr_end]}</thead>
      <tbody>{rows_html[first_tr_end:]}</tbody>
    </table>
    </div>
    """

    return html, color_map


# =====================================================
# STYLE HELPERS
# =====================================================

def _table_style() -> str:
    return (
        "width:100%;border-collapse:collapse;font-family:sans-serif;"
        "border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;"
    )

def _th_style(is_time: bool = False) -> str:
    bg = "#1B2A4A" if not is_time else "#243656"
    return (
        f"background:{bg};color:white;padding:10px 8px;"
        "font-size:12px;font-weight:600;text-align:center;"
        "border:1px solid #243656;white-space:nowrap;"
    )

def _time_cell_style(row_bg: str) -> str:
    return (
        f"background:{row_bg};padding:8px 10px;"
        "font-size:11px;font-weight:600;color:#374151;"
        "white-space:nowrap;border:1px solid #E5E7EB;"
        "text-align:center;min-width:90px;vertical-align:middle;"
    )

def _empty_cell_style(row_bg: str) -> str:
    return (
        f"background:{row_bg};padding:8px;text-align:center;"
        "color:#D1D5DB;font-size:14px;border:1px solid #E5E7EB;"
        "vertical-align:middle;"
    )

def _data_cell_style(row_bg: str) -> str:
    return (
        f"background:{row_bg};padding:6px;vertical-align:top;"
        "border:1px solid #E5E7EB;min-width:120px;"
    )

def _pill_style(bg: str, fg: str, border: str) -> str:
    return (
        f"background:{bg};color:{fg};border:{border};"
        "border-radius:6px;padding:5px 7px;margin-bottom:3px;"
        "line-height:1.4;"
    )

def _cont_pill_style(bg: str, border: str) -> str:
    """Continuation slot — same color, no text, slightly transparent."""
    return (
        f"background:{bg};border:{border};opacity:0.45;"
        "border-radius:4px;padding:5px 7px;margin-bottom:3px;"
        "min-height:18px;"
    )


# =====================================================
# STREAMLIT RENDER FUNCTION
# =====================================================

def render_grid_view(result: dict) -> None:
    scheduled = result.get("scheduled", [])

    if not scheduled:
        st.info("No timetable generated yet.")
        return

    all_sections = sorted({item["group"]   for item in scheduled})
    all_teachers = sorted({item["teacher"] for item in scheduled})

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])

    with ctrl1:
        selected_sections = st.multiselect(
            "Filter by section",
            options=all_sections,
            default=all_sections,
            placeholder="All sections",
        )
    with ctrl2:
        selected_teachers = st.multiselect(
            "Filter by teacher",
            options=all_teachers,
            default=[],
            placeholder="All teachers (no filter)",
        )
    with ctrl3:
        show_room = st.toggle("Show room", value=True)

    filtered = scheduled
    if selected_teachers:
        filtered = [x for x in filtered if x["teacher"] in selected_teachers]

    section_filter = (
        selected_sections
        if set(selected_sections) != set(all_sections)
        else None
    )

    html, color_map = build_grid(
        filtered,
        section_filter=section_filter,
        show_room=show_room,
    )

    st.markdown(html, unsafe_allow_html=True)

    if color_map:
        st.markdown("**Section legend**")
        legend_cols = st.columns(min(len(color_map), 6))
        for i, (section, (bg, fg)) in enumerate(color_map.items()):
            with legend_cols[i % len(legend_cols)]:
                st.markdown(
                    f"<div style='background:{bg};color:{fg};padding:4px 10px;"
                    f"border-radius:6px;font-size:12px;font-weight:600;"
                    f"text-align:center;margin-bottom:4px'>{section}</div>",
                    unsafe_allow_html=True,
                )

    st.caption(f"{LAB_SUFFIX} = Lab course  |  Shaded cells = course in progress")