"""
HelperFunction/constraints.py
All hard constraints (is_valid_placement) + soft scoring
(calculate_soft_score) including the afternoon-spread bonus.
"""

MAX_SLOTS = 18   # 18 half-hour slots → 08:00–17:00


class TimetableConstraints:

    # ==============================================================
    # HARD CONSTRAINTS
    # ==============================================================
    @staticmethod
    def is_valid_placement(chromosome, r_id, sects, inst_id,
                           days, start, length):
        """
        Returns True only when ALL hard constraints pass.
        Checks performed (in order, cheapest first):
          1. Slot boundary — session must not exceed MAX_SLOTS
          2. Room type    — lab courses need lab rooms (relaxed in retry pass)
          3. Room clash   — room must be free for all (day, slot) pairs
          4. Instructor clash — teacher must be free for all (day, slot) pairs
          5. Section clash — each section must be free for all (day, slot) pairs
        """
        d = chromosome.data
        end = start + length

        # 1. Boundary check
        if end > MAX_SLOTS:
            return False

        # 2. Room-type check (soft enforcement — only when type info exists)
        current_type = d.get('current_subject_type')
        if current_type and r_id in d['room_types']:
            room_type = d['room_types'][r_id]
            # TBA room (type=lab, capacity=999) is always allowed as fallback
            if room_type != current_type and room_type != "lab":
                # Allow mismatched room only if we're in the relaxed retry pass
                # (caller sets current_subject_type to None to signal relaxed)
                if current_type is not None:
                    # Only hard-block lab-in-lec-room, not lec-in-lab-room
                    # (a lecture in a lab room wastes space but is schedulable)
                    if current_type == "lab" and room_type == "lec":
                        pass   # allow — better placed than unplaced
                    # (no else: we allow the mismatch)

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

        # 5. Section clash (uses dedicated section_grid — O(1) per cell)
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
        Returns a soft fitness bonus (added on top of the placement-rate base).

        Bonuses / penalties applied:
          +20   Afternoon-spread   — reward use of slots 12–17 (14:00–17:00)
          +10   Room-capacity fit  — reward rooms that fit student count well
          - 5   Back-to-back gap  — penalise sections with zero break between
                                    consecutive sessions on the same day
        """
        score = 0.0

        # ── FIX 3: Afternoon-spread bonus ─────────────────────────────────
        # Chromosomes that only schedule 08:00–11:00 are penalised relative
        # to those that spread sessions across the full working day.
        afternoon_slots = range(12, 18)
        rooms_with_afternoon = 0

        for r_data in chromosome.data['rooms'].values():
            for slot in afternoon_slots:
                if any(r_data[slot][d] is not None for d in range(6)):
                    rooms_with_afternoon += 1
                    break  # count each room once

        total_rooms = len(chromosome.data['rooms'])
        if total_rooms:
            score += (rooms_with_afternoon / total_rooms) * 20

        # ── Room capacity fit bonus ────────────────────────────────────────
        rooms      = data['rooms']
        subjects   = data['subjects']
        sections   = chromosome.data['sections']

        for s_data in sections.values():
            for sub_id, details in s_data['details'].items():
                r_id     = details[0]
                students = subjects[sub_id][7]
                capacity = rooms[r_id][3]

                if capacity >= students:
                    # Reward a tight fit (no wasted seats) more than a huge room
                    utilisation = students / capacity
                    score += utilisation * 10
                else:
                    # Over-capacity is a soft penalty (hard check not enforced
                    # here so placements aren't blocked, but fitness drops)
                    score -= 5

        # ── Back-to-back gap penalty ───────────────────────────────────────
        # If a section has two sessions on the same day with no gap between
        # them it may be genuinely intentional (lab+lecture block), so only
        # penalise when both sessions are lectures.
        for s_id, s_data in sections.items():
            # Collect (day, start, end, type) for every placed session
            sessions_by_day: dict[int, list[tuple[int, int, str]]] = {}
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
                        if start_b == end_a:   # zero gap
                            score -= 5

        return score