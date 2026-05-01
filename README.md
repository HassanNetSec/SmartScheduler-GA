# SmartScheduler-GA

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A Genetic Algorithm implementation that solves the NP-hard university timetable scheduling problem — automatically assigns courses to rooms and timeslots while enforcing hard constraints (no clashes) and optimizing soft constraints (room fit, teacher workload). Built from scratch in Python with a Streamlit web interface.**

*Design & Analysis of Algorithms — Course Project | GIKI*

[Features](#-features) · [Algorithm](#-algorithm-design) · [Getting Started](#-getting-started) · [Usage](#-usage) · [Results](#-results)

</div>

---

## 🖼️ Screenshots

### Data Tab — Upload & Validate CSV
<img width="959" height="417" alt="image 1" src="https://github.com/user-attachments/assets/e3398b17-7dae-4746-a464-4f1bba61d85b" />

### Timetable Tab — Weekly Grid View
<img width="812" height="412" alt="image 2" src="https://github.com/user-attachments/assets/6af49a0d-5308-44ef-b605-485493713524" />

### Section Legend & Export Options
<img width="807" height="284" alt="image 3" src="https://github.com/user-attachments/assets/9e8455b3-e1dd-4f8d-bb29-647eada81a57" />

### Clash Resolver Tab
<img width="789" height="317" alt="image 4" src="https://github.com/user-attachments/assets/7ba2492c-f8f8-4447-8d83-44fdb8616315" />

---

## 🧩 Problem Statement

University timetable scheduling is a classic **NP-hard combinatorial optimization problem**. Given a set of courses, instructors, student groups, and rooms — find an assignment where:

- No room hosts two classes at the same time
- No instructor teaches two classes simultaneously
- No student group attends two classes at the same time
- All classes fall within valid teaching periods
- Room capacities and types are respected

The search space grows exponentially with input size, making brute-force search impossible. This project uses a **Genetic Algorithm** to navigate the solution space and converge toward a near-optimal schedule.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧬 Genetic Algorithm | Custom implementation with elitism and fitness-based evolution |
| 🔒 Hard Constraints | Room, instructor, and group conflict detection |
| ⚖️ Soft Constraints | Room capacity matching and teacher workload balancing |
| 📅 Real Slot Structure | Teaching periods with Tea Break, Prayer Break, and extended Friday Prayer |
| 🖥️ Streamlit UI | Upload CSV, generate, filter by section or teacher |
| 🔧 Clash Resolver | Automatically relocates a conflicting course to the next free slot |
| 📄 PDF Export | A3 landscape poster-layout master timetable |
| 📊 CSV Export | Flat data table for downstream processing |

---

## 🗂️ Project Structure

```
SmartScheduler-GA/
│
├── app.py                       # Streamlit web application
├── requirements.txt
└── HelperFunction/
    ├── constraints.py           # Hard & soft constraint evaluator
    ├── Validator.py             # Input CSV validation (Pandera)
    ├── GridView.py              # Weekly HTML grid renderer
    └── export_grid_pdf.py       # ReportLab A3 PDF exporter
```

---

## ⚙️ Getting Started

**Requirements:** Python 3.10+

```bash
# 1. Clone the repository
git clone https://github.com/HassanNetSec/SmartScheduler-GA.git
cd SmartScheduler-GA

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### Web Interface

```bash
streamlit run app.py
```

1. Upload your courses CSV from the sidebar
2. Click **Validate & Generate**
3. View the weekly grid in the **Timetable** tab
4. Export as **PDF** or **CSV**
5. Fix any remaining clashes in the **Clash Resolver** tab

### Command Line

```bash
python code.py
```

Reads `cleaned_courses.csv` → runs GA → writes `final_timetable.csv`.

---

## 📋 Input Format

```csv
course,teacher,group,credit_hours,is_lab,students
Artificial Intelligence,Dr. Asad Mehmood,BCS-6A,3,False,60
AI Lab,Dr. Asad Mehmood,BCS-6A,1,True,60
Linear Algebra,Dr. Babar Zaman,DS-Batch,3,False,55
```

| Column | Type | Description |
|--------|------|-------------|
| `course` | string | Course name |
| `teacher` | string | Teacher name(s), comma-separated if multiple |
| `group` | string | Student batch (e.g. `BCS-6A`, `DS-Batch`) |
| `credit_hours` | int | 1 – 4 |
| `is_lab` | bool | `True` for lab sessions |
| `students` | int | Enrolled student count |

---

## 🧬 Algorithm Design

### Chromosome Representation

Each chromosome encodes a **complete timetable** — every course mapped to a `(room, day_pattern, start_slot)` triple.

### Fitness Function

```
fitness  =  placement_rate  +  soft_score

placement_rate  =  (courses_placed / total_courses) × 100

soft_score      =  Σ capacity_reward(course)
                 − Σ |teacher_load − avg_load| × 0.3
```

### Evolutionary Loop

```
Initialize population (30 chromosomes)
│
└── For each generation (50 total):
      1. Evaluate fitness for every chromosome
      2. Sort population by fitness (descending)
      3. Elitism  →  keep top 5 unchanged
      4. Fill remaining 25 slots with newly generated chromosomes
      5. Repeat
│
Return best chromosome
```

### Constraints

**Hard — placement rejected if any violated:**
- Room double-booked at the same timeslot
- Instructor teaching two classes simultaneously
- Student group attending two classes at the same time
- Room type mismatch (lab course in lecture hall, or vice versa)
- Slot overlaps a Tea Break or Prayer Break period

**Soft — influence fitness score:**
- Room capacity below student count → heavy penalty (−200 pts)
- Room capacity within 15 seats of student count → bonus (+30 pts)
- Teacher workload deviation from weekly average → proportional penalty

---

## 🕐 Slot Structure

### Mon – Thu

| # | Time | Status |
|---|------|--------|
| 1 | 08:00 – 08:50 | ✅ Teaching |
| 2 | 09:00 – 09:50 | ✅ Teaching |
| — | 09:50 – 10:30 | ☕ Tea Break |
| 3 | 10:30 – 11:20 | ✅ Teaching |
| 4 | 11:30 – 12:20 | ✅ Teaching |
| 5 | 12:30 – 13:20 | ✅ Teaching |
| — | 13:20 – 14:30 | 🕌 Prayer Break |
| 6 | 14:30 – 15:20 | ✅ Teaching |
| 7 | 15:30 – 16:20 | ✅ Teaching |

### Friday

| # | Time | Status |
|---|------|--------|
| 1 | 08:00 – 08:50 | ✅ Teaching |
| 2 | 09:00 – 09:50 | ✅ Teaching |
| — | 09:50 – 10:30 | ☕ Tea Break |
| 3 | 10:30 – 11:20 | ✅ Teaching |
| 4 | 11:30 – 12:20 | ✅ Teaching |
| — | 12:20 – 14:30 | 🕌 Extended Prayer |
| 5 | 14:30 – 15:20 | ✅ Teaching |
| 6 | 15:30 – 16:20 | ✅ Teaching |
| 7 | 16:30 – 17:20 | ✅ Teaching |

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Courses placed | 163 / 181 **(90%)** |
| Hard constraint violations | **0** |
| Generations to converge | ~30 – 40 |
| Runtime | ~35 seconds |

> The 18 unplaced courses belong to a single batch that exceeds the maximum schedulable courses per week — a data-level infeasibility, not an algorithm failure.

---

## 🗺️ Future Work

- [ ] Crossover operator for true genetic recombination between chromosomes
- [ ] Simulated Annealing hybrid for local search refinement
- [ ] Multi-objective optimization (spread workload, minimize room switching)
- [ ] Per-group individual timetable PDF export
- [ ] Docker containerization for one-command deployment

---

## 👨‍💻 Author

**Hassan** — Cybersecurity Student, GIKI

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/your-profile)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/HassanNetSec)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
