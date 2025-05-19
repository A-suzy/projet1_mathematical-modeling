import json
from ortools.sat.python import cp_model

# Charger les fichiers JSON
with open("/home/awati/Bureau/projet1/subjects.json", "r") as file:
    subjects_data = json.load(file)

with open("/home/awati/Bureau/projet1/rooms.json", "r") as file:
    rooms_data = json.load(file)

# Extraction des niveaux et cours
levels = list(subjects_data["niveau"].keys())

courses = {
    level: [s.get("code", "UNKNOWN") for s in subjects_data["niveau"][level]["s1"]["subjects"]] +
           [s.get("code", "UNKNOWN") for s in subjects_data["niveau"][level]["s2"]["subjects"]]
    for level in levels
}

teachers = {
    level: [s.get("Course Lecturer", ["Enseignant inconnu"]) if s.get("Course Lecturer") 
            else ["Enseignant inconnu"] for s in subjects_data["niveau"][level]["s1"]["subjects"]] +
           [s.get("Course Lecturer", ["Enseignant inconnu"]) if s.get("Course Lecturer") 
            else ["Enseignant inconnu"] for s in subjects_data["niveau"][level]["s2"]["subjects"]]
    for level in levels
}

days = range(5)  # 5 jours de cours
periods = range(1, 6)  # Périodes de 1 à 5 (pas de 0)

# Création du modèle
model = cp_model.CpModel()

# Variables de décision
x = {}
for level in levels:
    for k in courses[level]:
        for j in days:
            for p in periods:
                x[level, k, j, p] = model.new_bool_var(f"x_{level}_{k}_{j}_{p}")

# Contraintes
# C1 : Un seul cours par niveau et jour
for level in levels:
    for j in days:
        model.add_at_most_one(x[level, k, j, p] for k in courses[level] for p in periods)

# C2 : Chaque cours ne peut apparaître **qu'une seule fois par jour** pour un niveau
for level in levels:
    for k in courses[level]:
        for j in days:
            model.add_at_most_one(x[level, k, j, p] for p in periods)

# C3 : Chaque cours doit être enseigné **une seule fois dans la semaine**
for level in levels:
    for k in courses[level]:
        model.add_exactly_one(x[level, k, j, p] for j in days for p in periods)

# Fonction objectif : Maximiser les périodes 1 et 2, minimiser les périodes 3, 4 et 5
weights = {1: 3, 2: 3, 3: -1, 4: -2, 5: -3}  # Périodes 1 et 2 favorisées, les autres réduites
model.maximize(sum(weights[p] * x[level, k, j, p] for level in levels for k in courses[level]
                    for j in days for p in periods))

# Résolution du modèle
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10  # Temps de calcul optimisé
status = solver.solve(model)

# Affichage du résultat formaté
assigned_shifts = 0

print("Emploi du temps généré :")
for j in days:
    print(f"\nDay {j}:")
    for p in periods:
        for level in levels:
            assigned_course = False  # Évite plusieurs cours à la même période
            for k in courses[level]:
                if solver.value(x[level, k, j, p]) and not assigned_course:
                    teacher = teachers[level][courses[level].index(k)]
                    print(f"Niveau {level} : Cours {k} ({', '.join(teacher)}) (Période {p})")
                    assigned_shifts += 1
                    assigned_course = True  # Empêcher une autre affectation à cette période

# Affichage des statistiques
print("\nStatistics")
print(f"  - Number of shift requests met = {assigned_shifts}")
print(f"  - Wall time       : {solver.wall_time}s")
