class TimetableConstraints:

    # ==============================================================
    # HARD CONSTRAINTS
    # ==============================================================
    @staticmethod
    def is_valid_placement(chromosome, r_id, sects, inst_id,
                           days, start, length):

        d   = chromosome.data
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
    # SOFT CONSTRAINTS (UPGRADED)
    # ==============================================================
    @staticmethod
    def calculate_soft_score(chromosome, data):
        score = 0.0

        sections = chromosome.data['sections']
        rooms    = chromosome.data['rooms']
        subjects = chromosome.data['subjects']

        # ----------------------------------------------------------
        # 1. Afternoon spread bonus
        # ----------------------------------------------------------
        rooms_with_afternoon = 0

        for r_data in chromosome.data['rooms'].values():
            for slot in range(AFTERNOON_START, MAX_SLOTS):
                if any(r_data[slot][d] is not None for d in range(6)):
                    rooms_with_afternoon += 1
                    break

        total_rooms = len(rooms)
        if total_rooms:
            score += (rooms_with_afternoon / total_rooms) * 20

        # ----------------------------------------------------------
        # 2. Room capacity efficiency
        # ----------------------------------------------------------
        for s_data in sections.values():
            for sub_id, details in s_data['details'].items():

                r_id     = details[0]
                students = subjects[sub_id][7]
                capacity = rooms[r_id][3]

                if capacity >= students:
                    score += (students / capacity) * 10
                else:
                    score -= 5

        # ----------------------------------------------------------
        # 3. Back-to-back penalty (improved)
        # ----------------------------------------------------------
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
                    start_a, end_a, type_a = day_sessions[i]
                    start_b, end_b, type_b = day_sessions[i + 1]

                    # back-to-back lectures
                    if type_a == "lec" and type_b == "lec":
                        if start_b - end_a <= 1:   # stricter (gap ≤ 1 slot)
                            score -= 5

        # ----------------------------------------------------------
        # 4. GAP minimization (NEW ⭐ IMPORTANT)
        # ----------------------------------------------------------
        for s_id, s_data in sections.items():
            daily_slots = {}

            for sub_id, details in s_data['details'].items():
                _, _, days, start, length = details
                end = start + length

                for day in days:
                    daily_slots.setdefault(day, []).append((start, end))

            for day, slots in daily_slots.items():
                slots.sort()

                for i in range(len(slots) - 1):
                    _, end_a = slots[i]
                    start_b, _ = slots[i + 1]

                    gap = start_b - end_a
                    if gap > 2:   # large gap penalty
                        score -= gap * 0.5

        # ----------------------------------------------------------
        # 5. Teacher workload balance (NEW ⭐)
        # ----------------------------------------------------------
        teacher_load = {}

        for s_data in sections.values():
            for sub_id, details in s_data['details'].items():
                inst_id = details[1]
                if inst_id is not None:
                    teacher_load[inst_id] = teacher_load.get(inst_id, 0) + 1

        if teacher_load:
            avg = sum(teacher_load.values()) / len(teacher_load)

            for load in teacher_load.values():
                score -= abs(load - avg) * 0.5

        # ----------------------------------------------------------
        # 6. Session completion reward (NEW ⭐ HARD-CONSTRAINT SUPPORT)
        # ----------------------------------------------------------
        for s_data in sections.values():
            assigned = len(s_data['details'])
            required = len(s_data.get('required', []))  # if you add later

            if required:
                score += (assigned / required) * 15

        return score
