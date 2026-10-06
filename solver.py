"""
Покроковий розв'язувач справ.

Алгоритм:
1. Усі аксіоми -> КНФ -> набір клауз.
2. Unit Propagation: шукаємо клаузу, де всі літерали вже хибні, крім одного.
   Цей один літерал мусить бути істинним -> фіксуємо значення змінної.
   Для кожної виведеної змінної запам'ятовуємо ПРИЧИНУ (аксіому і значення
   змінних, на які вона спиралась).
3. Коли значення цільової змінної знайдено, йдемо назад по причинах і
   лишаємо тільки ті кроки, які реально потрібні для відповіді
   (без зайвих кроків про сторонні змінні).
4. Якщо unit propagation не вистачило, переходимо до резолюції
   (вона повніша), а далі до перебору (DPLL) для перевірки.
"""
from typing import Dict, List, Tuple, Optional

from logic.parser import parse_formula
from logic.cnf import formula_to_clauses
from logic.models import Clause, Literal
from logic.resolution import prove


def _lit_value(lit: Literal, model: Dict[str, int]) -> Optional[int]:
    """1 / 0 / None (ще невідомо)."""
    if lit.name not in model:
        return None
    v = model[lit.name]
    return (1 - v) if lit.negated else v


def _parse_target(target: str) -> Literal:
    t = target.replace(" ", "")
    return Literal(t.lstrip("~"), t.startswith("~") and (len(t) - len(t.lstrip("~"))) % 2 == 1)


def _collect_clauses(axioms: List[str]) -> List[Tuple[Clause, str]]:
    out = []
    for ax in axioms:
        for c in formula_to_clauses(parse_formula(ax)):
            out.append((c, ax))
    return out


def _unit_propagation(clauses: List[Tuple[Clause, str]]):
    """
    Повертає (model, reasons, order, conflict)
      reasons[var] = (orig_axiom, clause, [(інша_змінна, її_значення), ...])
      order        = порядок, у якому виводились змінні
    """
    model: Dict[str, int] = {}
    reasons: Dict[str, tuple] = {}
    order: List[str] = []
    conflict = None

    changed = True
    while changed and conflict is None:
        changed = False
        for clause, orig in clauses:
            satisfied = False
            unknown: List[Literal] = []
            for lit in clause.literals:
                val = _lit_value(lit, model)
                if val == 1:
                    satisfied = True
                    break
                if val is None:
                    unknown.append(lit)
            if satisfied:
                continue

            if not unknown:
                # всі літерали хибні -> аксіоми суперечливі
                conflict = (clause, orig)
                break

            if len(unknown) == 1:
                lit = unknown[0]
                model[lit.name] = 0 if lit.negated else 1
                deps = [(l.name, model[l.name]) for l in clause.literals if l != lit]
                reasons[lit.name] = (orig, clause, deps)
                order.append(lit.name)
                changed = True

    return model, reasons, order, conflict


def _needed_steps(goal_var: str, reasons: Dict[str, tuple], order: List[str]) -> List[str]:
    """Залишає тільки кроки, від яких залежить цільова змінна."""
    needed = set()
    stack = [goal_var]
    while stack:
        v = stack.pop()
        if v in needed or v not in reasons:
            continue
        needed.add(v)
        for dep_var, _ in reasons[v][2]:
            stack.append(dep_var)
    return [v for v in order if v in needed]


def _describe_step(var: str, model: Dict[str, int], reasons: Dict[str, tuple]) -> str:
    orig, clause, deps = reasons[var]
    val = model[var]
    if not deps:
        return f"З аксіоми ({orig}) прямо: {var}={val}"
    cond = ", ".join(f"{n}={v}" for n, v in deps)
    return f"Оскільки {cond}, з аксіоми ({orig}) слідує: {var}={val}"


def _dpll_forced(clauses: List[Clause], var: str) -> Optional[int]:
    """
    Перевірка повним перебором: яке значення var примусове у ВСІХ моделях?
    Повертає 0 / 1 або None, якщо значення не однозначне.
    """
    def sat(cls: List[Clause], assign: Dict[str, int]) -> bool:
        cls = list(cls)
        assign = dict(assign)
        while True:
            unit = None
            new_cls = []
            for c in cls:
                lits = []
                done = False
                for l in c.literals:
                    v = _lit_value(l, assign)
                    if v == 1:
                        done = True
                        break
                    if v is None:
                        lits.append(l)
                if done:
                    continue
                if not lits:
                    return False
                if len(lits) == 1 and unit is None:
                    unit = lits[0]
                new_cls.append(Clause(frozenset(lits)))
            cls = new_cls
            if unit is None:
                break
            assign[unit.name] = 0 if unit.negated else 1
        if not cls:
            return True
        pick = next(iter(next(iter(cls)).literals)).name
        for val in (1, 0):
            a = dict(assign)
            a[pick] = val
            if sat(cls, a):
                return True
        return False

    can1 = sat(clauses, {var: 1})
    can0 = sat(clauses, {var: 0})
    if can1 and not can0:
        return 1
    if can0 and not can1:
        return 0
    return None


def solve_case(case_data: dict) -> dict:
    axioms = case_data["axioms"]
    target = case_data.get("target_hypothesis", "")
    goal = _parse_target(target)

    clauses = _collect_clauses(axioms)
    model, reasons, order, conflict = _unit_propagation(clauses)

    if conflict:
        return {"status": "INCONSISTENT", "steps": [], "model": model}

    if goal.name in model:
        keys = _needed_steps(goal.name, reasons, order)
        steps = [_describe_step(v, model, reasons) for v in keys]
        return {"status": "OK", "steps": steps, "model": model, "value": model[goal.name]}

    # Запасний варіант 1: резолюція
    kb = {c for c, _ in clauses}
    tree = prove(kb, Clause(frozenset([goal])))
    if tree.status == "PROVED":
        steps = [f"{s.parent1}  +  {s.parent2}  -->  {s.result_clause}" for s in tree.steps]
        value = 0 if goal.negated else 1
        return {"status": "OK_RESOLUTION", "steps": steps, "model": model, "value": value}

    # Запасний варіант 2: повний перебір (лише щоб дати чесну відповідь)
    forced = _dpll_forced([c for c, _ in clauses], goal.name)
    if forced is not None:
        return {"status": "OK_BRUTE", "steps": [], "model": model, "value": forced}

    return {"status": "UNDETERMINED", "steps": [], "model": model}


def generate_step_by_step_solution(case_data: dict) -> str:
    legend_str = "\n".join(f"   {k} : {v}" for k, v in case_data["legend"].items())
    axioms_str = "\n".join(f"  [Аксіома {i}]: {ax}" for i, ax in enumerate(case_data["axioms"], 1))
    target = case_data.get("target_hypothesis", "")
    var = target.replace(" ", "").lstrip("~")

    res = solve_case(case_data)
    head = (
        f"[Опис розслідування]:\n {case_data['description']}\n\n"
        f" Легенда змінних:\n{legend_str}\n"
        f"==================================================\n"
        f"--- БАЗА ЗНАНЬ (АКСІОМИ) ---\n{axioms_str}\n\n"
        f"Розв'язання справи:\n Гіпотеза: {target}\n"
    )

    if res["status"] == "INCONSISTENT":
        return head + "[ПОМИЛКА]: Аксіоми суперечать одна одній, справа не має розв'язку."
    if res["status"] == "UNDETERMINED":
        return head + f"Висновок: значення {var} неможливо визначити з наявних аксіом."

    if res["steps"]:
        steps_str = "\n".join(f" Крок {i}: {s}" for i, s in enumerate(res["steps"], 1))
    else:
        steps_str = " (значення випливає з повного перебору можливих моделей)"

    value = res["value"]
    truth = "істинна" if value == 1 else "хибна"
    return (
        head + f"{steps_str}\n\n"
        f"Відповідь: {var}={value}, тобто змінна {var} {truth} -> гіпотеза {target} ДОВЕДЕНА."
    )