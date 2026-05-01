import pandas as pd
import random
from HelperFunction.constraints import TimetableConstraints

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

# ── Day patterns ─────────────────────────────────────────────
# Lectures : MWF (days 0,2,4) with length=2 per session
#            TTh (days 1,3)   with length=3 per session
# Labs     : any single day, length=6
LEC_DAY_PATTERNS = [[0, 2, 4], [1, 3]]
LAB_DAY_PATTERNS = [[0], [1], [2], [3], [4]]

# 18 half-hour slots → 08:00–17:00
MAX_SLOTS = 18


# ============================================================
# CHROMOSOME
# ============================================================
class Chromosome:
    def __init__(self, data):
        self.fitness = 0
        self.data = {
            'sections':     {k: {'details': {}} for k in data['sections']},
            'instructors':  {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['instructors']},
            'rooms':        {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['rooms']},
            # Per-section grid: O(1) conflict check without scanning all rooms
            'section_grid': {k: [[None] * 6 for _ in range(MAX_SLOTS)]
                             for k in data['sections']},
            'room_types':   {k: v[1] for k, v in data['rooms'].items()},
            'current_subject_type': None,
            'unplaced': {'sections': {k: [] for k in data['sections']}},
        }

    # ----------------------------------------------------------
    def attempt_insert(self, schedule):
        """
        Try to place a course session.  Returns True on success.
        schedule = [room_id, [section_ids], subject_id,
                    instructor_id, [day_indices], start_slot, length]
        """
        r_id, sects, subj_id, inst_id, days, start, length = schedule

        if TimetableConstraints.is_valid_placement(
            self, r_id, sects, inst_id, days, start, length
        ):
            details = [r_id, inst_id, days, start, length]

            for s in sects:
                self.data['sections'][s]['details'][subj_id] = details
                for ts in range(start, start + length):
                    for d in days:
                        self.data['section_grid'][s][ts][d] = sects

            for ts in range(start, start + length):
                for d in days:
                    if inst_id is not None:
                        self.data['instructors'][inst_id][ts][d] = sects
                    self.data['rooms'][r_id][ts][d] = sects

            return True
        return False


# ============================================================
# GENETIC ALGORITHM
# ============================================================
class GeneticAlgorithm:
    def __init__(self, data):
        self.data = data
        self.pop_size = 30
        self.gen = 50

    # ----------------------------------------------------------
    def run(self):
        population = [self._generate() for _ in range(self.pop_size)]

        for g in range(self.gen):
            total = sum(len(v[2]) for v in self.data['sections'].values())
            for c in population:
                unplaced = sum(
                    len(v) for v in c.data['unplaced']['sections'].values()
                )
                base = ((total - unplaced) / total) * 100 if total else 0
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

            # Elite 5 survive; rest are regenerated
            population = (
                population[:5]
                + [self._generate() for _ in range(self.pop_size - 5)]
            )

        return population[0]

    # ----------------------------------------------------------
    def _build_valid_rooms(self, subj_type):
        """Return rooms matching subject type, or all rooms as fallback."""
        matched = [
            r_id for r_id, r_val in self.data['rooms'].items()
            if r_val[1] == subj_type
        ]
        return matched if matched else list(self.data['rooms'].keys())

    # ----------------------------------------------------------
    def _try_place(self, c, s_id, subj_id, room_pool, day_patterns, length,
                   relax_rooms=False):
        """
        FIX 1 — Exhaustive shuffled search instead of 100 random retries.
        Iterates every (room, day_pattern, start) combination exactly once
        (in random order) so late afternoon slots are guaranteed to be tried.

        Returns True if placed.
        """
        subj     = self.data['subjects'][subj_id]
        inst_id  = subj[4][0] if subj[4] else None
        max_start = MAX_SLOTS - length

        if max_start < 0:
            return False

        # FIX 1 — build ALL valid start slots and shuffle them
        all_starts   = list(range(0, max_start + 1))
        rooms_copy   = room_pool.copy()
        days_copy    = day_patterns.copy()

        random.shuffle(all_starts)   # ← guarantees slot 12-17 will be tried
        random.shuffle(rooms_copy)
        random.shuffle(days_copy)

        c.data['current_subject_type'] = subj[6]

        for r_id in rooms_copy:
            for days in days_copy:
                for start in all_starts:
                    if c.attempt_insert(
                        [r_id, [s_id], subj_id, inst_id, days, start, length]
                    ):
                        return True

        return False

    # ----------------------------------------------------------
    def _generate(self):
        c = Chromosome(self.data)

        # ── First pass: place every course with type-matched rooms ─────────
        for s_id, s_info in self.data['sections'].items():
            for subj_id in s_info[2]:
                subj      = self.data['subjects'][subj_id]
                subj_type = subj[6]

                if subj_type == "lab":
                    length       = 6
                    day_patterns = LAB_DAY_PATTERNS
                else:
                    length       = 2
                    day_patterns = LEC_DAY_PATTERNS

                valid_rooms = self._build_valid_rooms(subj_type)

                placed = self._try_place(
                    c, s_id, subj_id, valid_rooms, day_patterns, length
                )
                if not placed:
                    c.data['unplaced']['sections'][s_id].append(subj_id)

        # ── FIX 2 — Second pass: retry unplaced with relaxed room pool ─────
        # Allows a lab into a lecture room if no lab room is free, and
        # vice-versa, rather than silently discarding the course.
        all_rooms = list(self.data['rooms'].keys())

        for s_id in list(c.data['unplaced']['sections'].keys()):
            still_unplaced = []
            for subj_id in c.data['unplaced']['sections'][s_id]:
                subj      = self.data['subjects'][subj_id]
                subj_type = subj[6]

                if subj_type == "lab":
                    length       = 6
                    day_patterns = LAB_DAY_PATTERNS
                else:
                    length       = 2
                    day_patterns = LEC_DAY_PATTERNS

                placed = self._try_place(
                    c, s_id, subj_id, all_rooms, day_patterns, length,
                    relax_rooms=True
                )
                if not placed:
                    still_unplaced.append(subj_id)

            c.data['unplaced']['sections'][s_id] = still_unplaced

        return c


# ============================================================
# TIME FORMAT
# ============================================================
def format_time(start, length):
    """Convert half-hour slot indices to a human-readable time range."""
    end = min(start + length, MAX_SLOTS)   # clamp to 17:00

    def slot_to_str(s):
        h = 8 + s // 2
        m = "00" if s % 2 == 0 else "30"
        return f"{h:02d}:{m}"

    return f"{slot_to_str(start)} - {slot_to_str(end)}"


# ============================================================
# SOFT-SCORE HELPER  (add this to TimetableConstraints or call inline)
# ============================================================
def afternoon_spread_bonus(chromosome):
    """
    FIX 3 — Reward chromosomes that actually use afternoon slots (12–17).
    Returns up to +20 fitness points for full afternoon utilisation.
    This guides the GA to prefer timetables spread across the whole day.
    """
    afternoon_slots = range(12, 18)
    rooms_with_afternoon = 0

    for r_data in chromosome.data['rooms'].values():
        for slot in afternoon_slots:
            if any(r_data[slot][d] is not None for d in range(6)):
                rooms_with_afternoon += 1
                break   # count each room at most once

    total_rooms = len(chromosome.data['rooms'])
    return (rooms_with_afternoon / total_rooms) * 20 if total_rooms else 0


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    df = pd.read_csv("cleaned_courses.csv")

    # ── Rooms ─────────────────────────────────────────────────
    rooms = {
        i: [r["name"], r["type"], None, r["capacity"]]
        for i, r in enumerate(GIKI_ROOMS)
    }

    # ── Instructors ───────────────────────────────────────────
    # Split comma-separated teacher names into individual entries
    all_teachers: list[str] = []
    for raw in df["teacher"].unique():
        for name in [n.strip() for n in raw.split(",")]:
            if name and name not in all_teachers:
                all_teachers.append(name)

    instructors          = {i: [name, 30] for i, name in enumerate(all_teachers)}
    teacher_name_to_id   = {v[0]: k for k, v in instructors.items()}

    # ── Sections (groups) ─────────────────────────────────────
    groups           = list(df["group"].unique())
    group_name_to_id = {g: i for i, g in enumerate(groups)}
    sections         = {i: [g, None, []] for i, g in enumerate(groups)}

    # ── Subjects ──────────────────────────────────────────────
    subjects: dict = {}
    for idx, row in df.iterrows():
        grp_id = group_name_to_id[row["group"]]

        teacher_names = [n.strip() for n in str(row["teacher"]).split(",")]
        inst_ids = [
            teacher_name_to_id[n]
            for n in teacher_names
            if n in teacher_name_to_id
        ]

        subjects[idx] = [
            row["course"],                              # 0 name
            float(row["credit_hours"]),                 # 1 credits
            [grp_id],                                   # 2 section ids
            [idx],                                      # 3 subject id list
            inst_ids,                                   # 4 instructor ids
            True,                                       # 5 active
            "lab" if row["is_lab"] else "lec",          # 6 type
            int(row["students"]),                       # 7 student count
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

    for s_id, s in best.data["sections"].items():
        for sub_id, d in s["details"].items():
            output.append({
                "Course":    subjects[sub_id][0],
                "Group":     sections[s_id][0],
                "Room":      rooms[d[0]][0],
                "Days":      ",".join(days_map[x] for x in d[2]),
                "Time":      format_time(d[3], d[4]),
                "Type":      subjects[sub_id][6],
                "Students":  subjects[sub_id][7],
                "Instructor": (
                    instructors[d[1]][0] if d[1] is not None else "TBA"
                ),
            })

    unplaced_count = sum(
        len(v) for v in best.data["unplaced"]["sections"].values()
    )
    placed_count = len(output)

    print(f"\n{'='*50}")
    print(f"Placed  : {placed_count}")
    print(f"Unplaced: {unplaced_count}")
    print(f"{'='*50}")

    pd.DataFrame(output).to_csv("final_timetable.csv", index=False)
    print("Saved → final_timetable.csv  ✔")