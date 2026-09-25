import random
from logic.parser import parse_formula
from logic.cnf import formula_to_clauses
from logic.resolution import prove
from logic.models import Clause, Literal

LEVELS = {"Junior Investigator": (4, 0), "Middle Investigator": (6, 1), "Senior Investigator": (8, 3)}
PEOPLE = [
    ("Віктор", "Віктора", "системний адміністратор", "m"),
    ("Андрій", "Андрія", "нічний черговий", "m"),
    ("Богдан", "Богдана", "стажер", "m"),
    ("Тарас", "Тараса", "інженер підтримки", "m"),
    ("Олена", "Олену", "розробниця", "f"),
    ("Ірина", "Ірину", "спеціалістка з безпеки", "f"),
]

PERSON_EVENTS = [
    ("{p} підключи{v} до сервера сторонню флешку о {t}", "підключенні сторонньої флешки до сервера"),
    ("{p} скопіюва{v} базу даних клієнтів о {t}", "копіюванні бази даних клієнтів"),
    ("{p} відкри{v} двері серверної службовим ключем о {t}", "відкритті дверей серверної службовим ключем"),
    ("{p} зміни{v} пароль адміністратора о {t}", "зміні пароля адміністратора"),
    ("{p} видали{v} журнал доступу о {t}", "видаленні журналу доступу"),
    ("{p} бу{v} у серверній о {t}", "перебуванні в серверній без дозволу"),
    ("{p} спа{v} на своєму робочому місці", None),
]

SYSTEM_EVENTS = [
    "Сигналізація в дата-центрі була активована",
    "Камери відеоспостереження були вимкнені",
    "Мережевий екран пропустив зовнішній трафік",
    "Резервний генератор увімкнувся",
    "Систему виявлення вторгнень було відключено",
    "З сервера пішов великий обсяг вихідного трафіку",
]

PLACES = ["головному дата-центрі", "серверній кімнаті філії", "центральному вузлі зв'язку"]
INCIDENTS = ["спрацювала сирена", "зафіксовано несанкціонований доступ", "стався збій системи безпеки"]


def _neg(l):
    return l[1:] if l.startswith("~") else f"~{l}"


def _lower_first(text):
    """Робить першу літеру малою, крім випадку, коли речення починається з імені."""
    if text.split()[0] in {p[0] for p in PEOPLE}:
        return text
    return text[0].lower() + text[1:]


def _join_people(people):
    parts = [f"{role} {nom}" for nom, _, role, _ in people]
    return ", ".join(parts[:-1]) + " та " + parts[-1]


def generate_case(level="Junior Investigator", seed=None):
    rnd = random.Random(seed)
    n, n_decoys = LEVELS[level]
    people = rnd.sample(PEOPLE, 3)

    n_person = max(2, n // 2)
    pairs = [(p, t) for p in people for t in PERSON_EVENTS]
    suspicious = [x for x in pairs if x[1][1] is not None]
    first = rnd.choice(suspicious)  
    rest_pairs = [x for x in pairs if x != first]
    chosen = [first] + rnd.sample(rest_pairs, n_person - 1)

    events = []  
    for (nom, acc, role, g), (tpl, sus) in chosen:
        t = f"03:{rnd.randint(0, 20):02d}"
        text = tpl.format(p=nom, v="в" if g == "m" else "ла", t=t)
        events.append((text, acc if sus else None, sus))
    for text in rnd.sample(SYSTEM_EVENTS, n - n_person):
        events.append((text, None, None))
    rnd.shuffle(events)

    letters = [chr(ord("A") + i) for i in range(n)]
    legend = {l: e[0] for l, e in zip(letters, events)}
    model = {v: rnd.choice([True, False]) for v in letters}

    true_lit = lambda v: v if model[v] else f"~{v}"
    false_lit = lambda v: _neg(true_lit(v))

    chain_len = min(n - 1, {"Junior Investigator" : 3, "Middle Investigator": 4, "Senior Investigator": 5}[level])
    chain_vars = rnd.sample(letters, chain_len)
    chain = [true_lit(v) for v in chain_vars]
    rest = [v for v in letters if v not in chain_vars]

    axioms = []
    if rest and rnd.random() < 0.7:
        f = false_lit(rest.pop())
        axioms += [f"{f} v {chain[0]}", _neg(f)]
    else:
        axioms.append(chain[0])
    for a, b in zip(chain, chain[1:]):
        axioms.append(rnd.choice([f"{a} -> {b}", f"{_neg(b)} -> {_neg(a)}", f"{_neg(a)} v {b}"]))
    for _ in range(n_decoys):  
        x, y = rnd.sample(letters, 2)
        axioms.append(f"{true_lit(x)} v {rnd.choice([true_lit(y), false_lit(y)])}")

    used = set()
    for a in axioms:
        for v in letters:
            if v in a:
                used.add(v)
    for v in letters:
        if v not in used:
            axioms.append(true_lit(v))

    rnd.shuffle(axioms)

    target = chain[-1]

    kb = {c for a in axioms for c in formula_to_clauses(parse_formula(a))}
    h = Clause(frozenset([Literal(target.lstrip("~"), target.startswith("~"))]))
    assert prove(kb, h).status == "PROVED", (axioms, target)
    suspect = rnd.choice([e for e in events if e[1]])
    description = (
        f"О 03:00 ночі в {rnd.choice(PLACES)} {rnd.choice(INCIDENTS)}. "
        f"У цей час там перебували: {_join_people(people)}. "
        f"{suspect[1]} підозрюють у {suspect[2]}. "
        f"Проаналізувавши свідчення та логи безпеки, доведіть за допомогою логіки, "
        f"чи правда, що {_lower_first(legend[target.lstrip('~')])}."
    )

    case_id = seed if seed is not None else rnd.randint(1000, 9999)
    return {
        "id": case_id,
        "title": f"СПРАВА №{case_id}: НІЧНИЙ ІНЦИДЕНТ",
        "mode": "Доведення",
        "level": level,
        "description": description,
        "legend": legend,
        "axioms": axioms,
        "target_hypothesis": target,
    }