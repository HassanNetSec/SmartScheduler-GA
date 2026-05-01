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
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]

TIME_LABELS = {t: t for t in TIME_ORDER}   # show raw time; customise if needed

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

    # Build cell_map: (day, time) → list of (label, section, is_lab)
    cell_map: dict = {}
    used_times: set = set()

    for item in data:
        lab = item.get("is_lab", False)

        label = item["course"]
        if show_room:
            label += f"\n{item['room']}"
        label += f"\n{item['group']}"
        if lab:
            label += LAB_SUFFIX

        # _parse_slot returns one tuple per day in the pattern
        for day, time in _parse_slot(item["timeslot"]):
            key = (day, time)
            cell_map.setdefault(key, []).append((label, item["group"], lab))
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
        header_cells += f"<th style='{_th_style()}'>{TIME_LABELS.get(time, time)}</th>"
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
                for label, section, is_lab in entries:
                    bg, fg = color_map.get(section, ("#F3F4F6", "#111827"))
                    lines       = label.split("\n")
                    course_line = f"<span style='font-weight:600;font-size:11px'>{lines[0]}</span>"
                    rest_lines  = "".join(
                        f"<span style='display:block;font-size:9px;opacity:0.8'>{l}</span>"
                        for l in lines[1:]
                    )
                    border = "2px solid rgba(0,0,0,0.15)" if is_lab else "none"
                    inner += (
                        f"<div style='{_pill_style(bg, fg, border)}'>"
                        f"{course_line}{rest_lines}</div>"
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

    section_filter = selected_sections if set(selected_sections) != set(all_sections) else None

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

    st.caption(f"{LAB_SUFFIX} = Lab course (3-hour block)")