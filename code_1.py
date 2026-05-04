import pandas as pd
import random
from HelperFunction.cnts import TimetableConstraints

# ============================================================
# ROOMS
# ============================================================
GIKI_ROOMS = [
    # ── CS Building ──────────────────────────────
    {"name": "CS LH1",          "capacity": 80,  "type": "lec"},
    {"name": "CS LH2",          "capacity": 80,  "type": "lec"},
    {"name": "CS LH3",          "capacity": 80,  "type": "lec"},
    {"name": "CS LH4",          "capacity": 80,  "type": "lec"},
    # ── EE Building ──────────────────────────────
    {"name": "EE LH1",          "capacity": 60,  "type": "lec"},
    {"name": "EE LH2",          "capacity": 80,  "type": "lec"},
    {"name": "EE LH3",          "capacity": 80,  "type": "lec"},
    {"name": "EE LH4",          "capacity": 80,  "type": "lec"},
    {"name": "EE Main",         "capacity": 150, "type": "lec"},
    {"name": "FEE Quiz Hall",   "capacity": 120, "type": "lec"},
    # ── ES Building ──────────────────────────────
    {"name": "ES LH1",          "capacity": 60,  "type": "lec"},
    {"name": "ES LH2",          "capacity": 60,  "type": "lec"},
    {"name": "ES LH3",          "capacity": 60,  "type": "lec"},
    {"name": "ES LH4",          "capacity": 60,  "type": "lec"},
    {"name": "ES Main",         "capacity": 150, "type": "lec"},
    {"name": "FES Quiz Hall",   "capacity": 120, "type": "lec"},
    # ── Academic Block (AcB) ─────────────────────
    {"name": "AcB LH1",         "capacity": 60,  "type": "lec"},
    {"name": "AcB LH2",         "capacity": 60,  "type": "lec"},
    {"name": "AcB LH3",         "capacity": 60,  "type": "lec"},
    {"name": "AcB LH4",         "capacity": 80,  "type": "lec"},
    {"name": "AcB LH5",         "capacity": 80,  "type": "lec"},
    {"name": "AcB LH6",         "capacity": 80,  "type": "lec"},
    {"name": "AcB LH7",         "capacity": 60,  "type": "lec"},
    {"name": "AcB LH8",         "capacity": 80,  "type": "lec"},
    {"name": "AcB LH9",         "capacity": 60,  "type": "lec"},
    {"name": "AcB LH10",        "capacity": 80,  "type": "lec"},
    {"name": "AcB LH11",        "capacity": 60,  "type": "lec"},
    {"name": "AcB LH12",        "capacity": 60,  "type": "lec"},
    {"name": "AcB Main1",       "capacity": 150, "type": "lec"},
    {"name": "AcB Main2",       "capacity": 200, "type": "lec"},
    {"name": "AcB Main3",       "capacity": 200, "type": "lec"},
    # ── Bio Block (BB) ───────────────────────────
    {"name": "BB LH2",          "capacity": 80,  "type": "lec"},
    {"name": "BB EH1",          "capacity": 80,  "type": "lec"},
    {"name": "BB EH2",          "capacity": 80,  "type": "lec"},
    {"name": "BB EH3",          "capacity": 80,  "type": "lec"},
    {"name": "BB EH4",          "capacity": 80,  "type": "lec"},
    {"name": "BB Main",         "capacity": 150, "type": "lec"},
    # ── ME Building ──────────────────────────────
    {"name": "ME LH1",          "capacity": 80,  "type": "lec"},
    {"name": "ME LH2",          "capacity": 80,  "type": "lec"},
    {"name": "ME LH3",          "capacity": 80,  "type": "lec"},
    {"name": "ME Main",         "capacity": 150, "type": "lec"},
    {"name": "FME Quiz Hall",   "capacity": 120, "type": "lec"},
    # ── MCE Building ─────────────────────────────
    {"name": "MCE LH1",         "capacity": 60,  "type": "lec"},
    {"name": "MCE LH2",         "capacity": 60,  "type": "lec"},
    {"name": "MCE LH3",         "capacity": 60,  "type": "lec"},
    {"name": "MCE LH4",         "capacity": 60,  "type": "lec"},
    {"name": "MCE Main",        "capacity": 150, "type": "lec"},
    {"name": "FCME Quiz Hall",  "capacity": 120, "type": "lec"},
    # ── Labs ─────────────────────────────────────
    {"name": "FES - PH Lab",    "capacity": 100, "type": "lab"},
    {"name": "FES - PH Lab 2",  "capacity": 100, "type": "lab"},
    {"name": "FES - SE Lab",    "capacity": 60,  "type": "lab"},
    {"name": "ACB - AI Lab",    "capacity": 50,  "type": "lab"},
    {"name": "ACB - CYS Lab",   "capacity": 40,  "type": "lab"},
    {"name": "ACB - DA Lab",    "capacity": 50,  "type": "lab"},
    {"name": "BB PC Lab",       "capacity": 60,  "type": "lab"},
    {"name": "FME Lab",         "capacity": 130, "type": "lab"},
    {"name": "FCME - MM Lab",   "capacity": 40,  "type": "lab"},
    {"name": "FCME - CH Lab",   "capacity": 40,  "type": "lab"},
    {"name": "FBS Lab",         "capacity": 120, "type": "lab"},
    {"name": "TBA",             "capacity": 999, "type": "lab"},
]

# ============================================================
# SLOT SYSTEM — 1 slot = 10 minutes, 08:00–17:00 = 54 slots
# ============================================================
SLOT_UNIT = 10            # minutes per slot
DAY_START = 8 * 60        # 08:00 in minutes
DAY_END = 18 * 60       # 17:00 in minutes
MAX_SLOTS = (DAY_END - DAY_START) // SLOT_UNIT   # = 54

# ── Break windows ────────────────────────────────────────────
# Tea break   : 09:50–10:30  → slots 11–14  (4 slots = 40 min)
# Prayer break: 13:30–14:30  → slots 33–38  (6 slots = 60 min)
TEA_BREAK_START    = (9  * 60 + 50 - DAY_START) // SLOT_UNIT   # 11
TEA_BREAK_END      = (10 * 60 + 30 - DAY_START) // SLOT_UNIT   # 15 (exclusive)
PRAYER_BREAK_START = (13 * 60 + 30 - DAY_START) // SLOT_UNIT   # 33
PRAYER_BREAK_END   = (14 * 60 + 30 - DAY_START) // SLOT_UNIT   # 39 (exclusive)

# Frozenset for O(1) membership check — computed once at import
BLOCKED_SLOTS: frozenset = frozenset(
    list(range(TEA_BREAK_START,    TEA_BREAK_END)) +
    list(range(PRAYER_BREAK_START, PRAYER_BREAK_END))
)

# ── Session lengths (slots) ──────────────────────────────────
LEC_LENGTH = 5    # 5 × 10 min = 50 min  ✔
LAB_LENGTH = 18   # 18 × 10 min = 180 min (3 hours)  ✔

# ── Day patterns ─────────────────────────────────────────────
LEC_DAY_PATTERNS = [[0, 2, 4], [1, 3]]       # MWF or TTh
LAB_DAY_PATTERNS = [[0], [1], [2], [3], [4]] # any single day


# ============================================================
# VALID START-SLOT CACHE
# Pre-compute once: all starts where session fits without
# touching any blocked slot. Zero filtering cost in hot loop.
# ============================================================
def _build_valid_starts(length: int) -> list:
    return [
        s for s in range(0, MAX_SLOTS - length + 1)
        if not any(sl in BLOCKED_SLOTS for sl in range(s, s + length))
    ]

VALID_LEC_STARTS: list = _build_valid_starts(LEC_LENGTH)
VALID_LAB_STARTS: list = _build_valid_starts(LAB_LENGTH)


# ============================================================
# HELPER — count occupied cells in a nested-list grid
# ============================================================
def _count_occupied(grid: list) -> int:
    """Count non-None cells in a MAX_SLOTS×6 nested list."""
    return sum(1 for row in grid for cell in row if cell is not None)


# ============================================================
# CHROMOSOME
# ============================================================
class Chromosome:
    def __init__(self, data):
        self.fitness = 0
        self.data = {
            'sections':     {k: {'details': {}} for k in data['sections']},

            # Nested lists [slot][day] — required by TimetableConstraints
            'instructors':  {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['instructors']},
            'rooms':        {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['rooms']},
            'section_grid': {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['sections']},

            'room_types':   {k: v[1] for k, v in data['rooms'].items()},
            'current_subject_type': None,
            'unplaced': {'sections': {k: [] for k in data['sections']}},
        }

    # ----------------------------------------------------------
    def attempt_insert(self, schedule):
        """
        Try to place a course session. Returns True on success.
        schedule = [room_id, [section_ids], subject_id,
                    instructor_id, [day_indices], start_slot, length]
        """
        r_id, sects, subj_id, inst_id, days, start, length = schedule

        # Delegates all hard constraint checks to TimetableConstraints
        # (boundary, break overlap, room clash, instructor clash, section clash)
        if not TimetableConstraints.is_valid_placement(
            self, r_id, sects, inst_id, days, start, length
        ):
            return False

        # ── Commit placement to all grids ─────────────────────
        details = [r_id, inst_id, days, start, length]

        for ts in range(start, start + length):
            for d in days:
                self.data['rooms'][r_id][ts][d] = sects
                if inst_id is not None:
                    self.data['instructors'][inst_id][ts][d] = sects
                for s in sects:
                    self.data['section_grid'][s][ts][d] = sects

        for s in sects:
            self.data['sections'][s]['details'][subj_id] = details

        return True


# ============================================================
# GENETIC ALGORITHM
# ============================================================
class GeneticAlgorithm:
    def __init__(self, data):
        self.data     = data
        self.pop_size = 15   # reduced from 30 — no real crossover
        self.gen      = 30   # reduced from 50

        # ── Room pools built once, reused every generation ────
        self._lec_rooms = self._build_valid_rooms("lec")
        self._lab_rooms = self._build_valid_rooms("lab")
        self._all_rooms = list(data['rooms'].keys())

    # ----------------------------------------------------------
    def run(self):
        population = [self._generate() for _ in range(self.pop_size)]

        for g in range(self.gen):
            total = sum(len(v[2]) for v in self.data['sections'].values())
            for c in population:
                unplaced = sum(
                    len(v) for v in c.data['unplaced']['sections'].values()
                )
                base      = ((total - unplaced) / total) * 100 if total else 0
                c.fitness = base + TimetableConstraints.calculate_soft_score(
                    c, self.data
                )

            population.sort(key=lambda x: x.fitness, reverse=True)
            best_unplaced = sum(
                len(v)
                for v in population[0].data['unplaced']['sections'].values()
            )
            print(
                f"Gen {g:02d}  "
                f"Best fitness: {population[0].fitness:.2f}  "
                f"Unplaced: {best_unplaced}"
            )

            # Elite 3 survive; rest regenerated
            population = (
                population[:3]
                + [self._generate() for _ in range(self.pop_size - 3)]
            )

        return population[0]

    # ----------------------------------------------------------
    def _build_valid_rooms(self, subj_type: str) -> list:
        matched = [
            r_id for r_id, r_val in self.data['rooms'].items()
            if r_val[1] == subj_type
        ]
        return matched if matched else list(self.data['rooms'].keys())

    # ----------------------------------------------------------
    def _try_place(self, c: Chromosome, s_id: int, subj_id: int,
                   room_pool: list, day_patterns: list, length: int) -> bool:
        """
        Exhaustive shuffled search over (room × day_pattern × start).
        Start slots come from pre-computed VALID_*_STARTS (break-safe).
        Room pools and day patterns are pre-shuffled once per _generate().
        """
        subj    = self.data['subjects'][subj_id]
        inst_id = subj[4][0] if subj[4] else None

        # Pick correct pre-filtered start list
        starts = VALID_LAB_STARTS if length == LAB_LENGTH else VALID_LEC_STARTS
        if not starts:
            return False

        # Shuffle starts once per placement call (~35 elements, cheap)
        starts_shuf = starts.copy()
        random.shuffle(starts_shuf)

        c.data['current_subject_type'] = subj[6]

        # ── Early exit: fully-booked instructor ───────────────
        # FIXED: use _count_occupied() on nested list, not len()
        max_cells = MAX_SLOTS * 5   # 54 slots × 5 days = 270
        if inst_id is not None:
            if _count_occupied(c.data['instructors'][inst_id]) >= max_cells:
                return False

        for r_id in room_pool:
            # FIXED: use _count_occupied() on nested list, not len()
            if _count_occupied(c.data['rooms'][r_id]) >= max_cells:
                continue
            for days in day_patterns:
                for start in starts_shuf:
                    if c.attempt_insert(
                        [r_id, [s_id], subj_id, inst_id, days, start, length]
                    ):
                        return True
        return False

    # ----------------------------------------------------------
    def _generate(self) -> Chromosome:
        c = Chromosome(self.data)

        # ── Shuffle pools and patterns ONCE per chromosome ────
        # (not per course — saves hundreds of shuffle calls)
        lec_rooms = self._lec_rooms.copy(); random.shuffle(lec_rooms)
        lab_rooms = self._lab_rooms.copy(); random.shuffle(lab_rooms)
        all_rooms = self._all_rooms.copy(); random.shuffle(all_rooms)

        lec_days = LEC_DAY_PATTERNS.copy(); random.shuffle(lec_days)
        lab_days = LAB_DAY_PATTERNS.copy(); random.shuffle(lab_days)

        # ── First pass: type-matched rooms ────────────────────
        for s_id, s_info in self.data['sections'].items():
            for subj_id in s_info[2]:
                subj_type = self.data['subjects'][subj_id][6]

                # FIXED: use LEC_LENGTH / LAB_LENGTH constants, not 2 / 6
                if subj_type == "lab":
                    length, day_pat, room_pool = LAB_LENGTH, lab_days, lab_rooms
                else:
                    length, day_pat, room_pool = LEC_LENGTH, lec_days, lec_rooms

                if not self._try_place(c, s_id, subj_id, room_pool,
                                       day_pat, length):
                    c.data['unplaced']['sections'][s_id].append(subj_id)

        # ── Second pass: relaxed room pool for unplaced ───────
        for s_id in list(c.data['unplaced']['sections'].keys()):
            still_unplaced = []
            for subj_id in c.data['unplaced']['sections'][s_id]:
                subj_type = self.data['subjects'][subj_id][6]

                # FIXED: use LEC_LENGTH / LAB_LENGTH constants, not 2 / 6
                if subj_type == "lab":
                    length, day_pat = LAB_LENGTH, lab_days
                else:
                    length, day_pat = LEC_LENGTH, lec_days

                if not self._try_place(c, s_id, subj_id, all_rooms,
                                       day_pat, length):
                    still_unplaced.append(subj_id)

            c.data['unplaced']['sections'][s_id] = still_unplaced

        return c


# ============================================================
# TIME FORMAT
# ============================================================
def format_time(start: int, length: int) -> str:
    """Convert 10-min slot index + length to a readable time range."""
    start_min = DAY_START + start * SLOT_UNIT
    end_min   = min(start_min + length * SLOT_UNIT, DAY_END)

    def m2s(m: int) -> str:
        return f"{m // 60:02d}:{m % 60:02d}"

    return f"{m2s(start_min)} - {m2s(end_min)}"


# ============================================================
# AFTERNOON SPREAD BONUS  (soft-score helper)
# ============================================================
def afternoon_spread_bonus(chromosome: Chromosome) -> float:
    """
    Reward chromosomes that use post-prayer slots (14:30 onward).
    Returns up to +20 fitness points.
    FIXED: uses nested-list syntax [slot][day] instead of set lookup.
    """
    rooms_with_pm = 0

    for r_data in chromosome.data['rooms'].values():
        for slot in range(PRAYER_BREAK_END, MAX_SLOTS):
            # FIXED: r_data is [[None]*6 ...], use [slot][d] not (slot,d) in set
            if any(r_data[slot][d] is not None for d in range(5)):
                rooms_with_pm += 1
                break   # count each room once

    total = len(chromosome.data['rooms'])
    return (rooms_with_pm / total) * 20 if total else 0


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    df = pd.read_csv("CouresesList.csv")

    # ── Rooms ─────────────────────────────────────────────────
    rooms = {
        i: [r["name"], r["type"], None, r["capacity"]]
        for i, r in enumerate(GIKI_ROOMS)
    }

    # ── Instructors ───────────────────────────────────────────
    all_teachers: list = []
    for raw in df["teacher"].unique():
        for name in [n.strip() for n in raw.split(",")]:
            if name and name not in all_teachers:
                all_teachers.append(name)

    instructors        = {i: [name, 30] for i, name in enumerate(all_teachers)}
    teacher_name_to_id = {v[0]: k for k, v in instructors.items()}

    # ── Sections ──────────────────────────────────────────────
    groups           = list(df["group"].unique())
    group_name_to_id = {g: i for i, g in enumerate(groups)}
    sections         = {i: [g, None, []] for i, g in enumerate(groups)}

    # ── Subjects ──────────────────────────────────────────────
    subjects: dict = {}
    for idx, row in df.iterrows():
        grp_id = group_name_to_id[row["group"]]
        inst_ids = [
            teacher_name_to_id[n]
            for n in [t.strip() for t in str(row["teacher"]).split(",")]
            if n in teacher_name_to_id
        ]
        subjects[idx] = [
            row["course"],                          # 0 name
            float(row["credit_hours"]),             # 1 credits
            [grp_id],                               # 2 section ids
            [idx],                                  # 3 subject id list
            inst_ids,                               # 4 instructor ids
            True,                                   # 5 active
            "lab" if row["is_lab"] else "lec",      # 6 type
            int(row["students"]),                   # 7 student count
        ]
        sections[grp_id][2].append(idx)

    data = {
        "rooms":       rooms,
        "instructors": instructors,
        "sections":    sections,
        "subjects":    subjects,
    }

    # ── Run GA ────────────────────────────────────────────────
    ga   = GeneticAlgorithm(data)
    best = ga.run()

    # ── Output ────────────────────────────────────────────────
    days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat"}
    output   = []

    print("\n===== DEBUG LENGTH CHECK =====")

    for s_id, s in best.data["sections"].items():
        for sub_id, d in s["details"].items():

            # 🔴 DEBUG LINE (THIS WILL SHOW REAL LENGTH)
            print("DEBUG →", subjects[sub_id][0], "| Length:", d[4])

            output.append({
                "Course":     subjects[sub_id][0],
                "Group":      sections[s_id][0],
                "Room":       rooms[d[0]][0],
                "Days":       ",".join(days_map[x] for x in d[2]),
                "Time":       format_time(d[3], d[4]),
                "Type":       subjects[sub_id][6],
                "Students":   subjects[sub_id][7],
                "Instructor": (
                    instructors[d[1]][0] if d[1] is not None else "TBA"
                ),
            })

    # ── Summary ───────────────────────────────────────────────
    unplaced_count = sum(
        len(v) for v in best.data["unplaced"]["sections"].values()
    )

    print(f"\n{'='*50}")
    print(f"Placed  : {len(output)}")
    print(f"Unplaced: {unplaced_count}")
    print(f"{'='*50}")

    print(f"\nBreak schedule enforced:")
    print(f"  Tea break   : 09:50 – 10:30")
    print(f"  Prayer break: 13:30 – 14:30")

    print(f"\nSession durations:")
    print(f"  Lecture : {LEC_LENGTH * SLOT_UNIT} min")
    print(f"  Lab     : {LAB_LENGTH * SLOT_UNIT} min")

    # ── Save CSV ──────────────────────────────────────────────
    pd.DataFrame(output).to_csv("final_timetable.csv", index=False)
    print("\nSaved → final_timetable.csv  ✔")