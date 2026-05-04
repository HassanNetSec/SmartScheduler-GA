
# HelperFunction/cnts.py
# All hard constraints (is_valid_placement) + soft scoring (calculate_soft_score)
# including the afternoon-spread bonus.

# 1 slot = 10 minutes, 08:00–17:00 = 54 slots
MAX_SLOTS = 60

# Break slot boundaries
# Tea break : 09:50–10:30 → slots 11–14
# Prayer break: 13:30–14:30 → slots 33–38

TEA_BREAK_START = 11
TEA_BREAK_END = 15  # exclusive

PRAYER_BREAK_START = 33
PRAYER_BREAK_END = 39  # exclusive

BLOCKED_SLOTS = frozenset(
    list(range(TEA_BREAK_START, TEA_BREAK_END)) +
    list(range(PRAYER_BREAK_START, PRAYER_BREAK_END))
)

# Afternoon = everything after prayer break ends (slot 39 → 14:30)
AFTERNOON_START = PRAYER_BREAK_END


class TimetableConstraints:

    # ==============================================================
    # HARD CONSTRAINTS
    # ==============================================================

    @staticmethod
    def is_valid_placement(chromosome, r_id, sects, inst_id, days, start, length):
        """
        Returns True only when ALL hard constraints pass.
        """

        d = chromosome.data
        end = start + length

        # 1. Boundary check
        if end > MAX_SLOTS:
            return False

        # 2. Break overlap
        for ts in range(start, end):
            if ts in BLOCKED_SLOTS:
                return False

        # 3. Room clash
        room_grid = d['rooms'][r_id]
        for ts in range(start, end):
            for day in days:
                if room_grid[ts][day] is not None:
                    return False

        # 4. Instructor clash
        if inst_id is not None:
            inst_grid = d['instructors'][inst_id]
            for ts in range(start, end):
                for day in days:
                    if inst_grid[ts][day] is not None:
                        return False

        # 5. Section clash
        for s in sects:
            sec_grid = d['section_grid'][s]
            for ts in range(start, end):
                for day in days:
                    if sec_grid[ts][day] is not None:
                        return False

        return True

    # ==============================================================
    # SOFT CONSTRAINTS
    # ==============================================================

    @staticmethod
    def calculate_soft_score(chromosome, data):
        """
        Soft fitness bonus:
        +20 Afternoon spread
        +10 Room capacity fit
        -5 Over-capacity penalty
        -5 Back-to-back lectures penalty
        """

        score = 0.0

        # ── Afternoon spread bonus ─────────────────────────────
        rooms_with_afternoon = 0

        for r_data in chromosome.data['rooms'].values():
            for slot in range(AFTERNOON_START, MAX_SLOTS):
                if any(r_data[slot][d] is not None for d in range(6)):
                    rooms_with_afternoon += 1
                    break

        total_rooms = len(chromosome.data['rooms'])
        if total_rooms:
            score += (rooms_with_afternoon / total_rooms) * 20

        # ── Room capacity fit bonus ────────────────────────────
        rooms = data['rooms']
        subjects = data['subjects']
        sections = chromosome.data['sections']

        for s_data in sections.values():
            for sub_id, details in s_data['details'].items():
                r_id = details[0]
                students = subjects[sub_id][7]
                capacity = rooms[r_id][3]

                if capacity >= students:
                    utilisation = students / capacity
                    score += utilisation * 10
                else:
                    score -= 5

        # ── Back-to-back lecture penalty ───────────────────────
        for s_id, s_data in sections.items():
            sessions_by_day = {}

            for sub_id, details in s_data['details'].items():
                _, _, days, start, length = details
                subj_type = subjects[sub_id][6]
                end = start + length

                for day in days:
                    sessions_by_day.setdefault(day, []).append(
                        (start, end, subj_type)
                    )

            for day_sessions in sessions_by_day.values():
                day_sessions.sort()

                for i in range(len(day_sessions) - 1):
                    _, end_a, type_a = day_sessions[i]
                    start_b, _, type_b = day_sessions[i + 1]

                    if type_a == "lec" and type_b == "lec":
                        if start_b == end_a:
                            score -= 5

        return score
