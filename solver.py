# solver.py
from logic.parser import parse_formula
from logic.cnf import formula_to_clauses
from logic.models import Clause, Literal

def eval_literal(lit: Literal, model: dict):
    """Повертає значення літералу (1, 0 або None, якщо невідомо)."""
    if lit.name not in model:
        return None
    val = model[lit.name]
    return (1 - val) if lit.negated else val

def evaluate_case(axioms_strs, legend):
    """
    Універсальний алгоритм покрокового розв'язання (Unit Propagation).
    Працює з будь-якими формами аксіом за допомогою КНФ!
    """
    # 1. Парсимо всі аксіоми у клаузи (диз'юнкції)
    clauses = []
    for ax_str in axioms_strs:
        parsed = parse_formula(ax_str)
        cls_set = formula_to_clauses(parsed)
        for c in cls_set:
            clauses.append((c, ax_str))

    model = {}  # Зберігає знайдені значення змінних: 'A': 1, 'B': 0 тощо.
    steps = []  # Зберігає текстові кроки виведення

    changed = True
    while changed:
        changed = False

        for clause, orig_ax in clauses:
            # Оцінюємо стан літералів у цій клаузі
            lits = list(clause.literals)
            unknown_lits = []
            clause_is_satisfied = False

            for lit in lits:
                val = eval_literal(lit, model)
                if val == 1:
                    clause_is_satisfied = True
                    break
                elif val is None:
                    unknown_lits.append(lit)

            # Якщо клауза вже істинна, пропускаємо її
            if clause_is_satisfied:
                continue

            # Якщо залишився РІВНО ОДИН невідомий літерал (решта хибні)
            if len(unknown_lits) == 1:
                target_lit = unknown_lits[0]
                # Щоб вся клауза була істинною, цей літерал МАЄ бути 1
                var_name = target_lit.name
                required_var_val = 0 if target_lit.negated else 1

                model[var_name] = required_var_val
                changed = True

                # Формуємо красивий текстовий крок
                false_lits_info = []
                for lit in lits:
                    if lit != target_lit:
                        false_lits_info.append(f"{lit}=0")

                if false_lits_info:
                    cond_str = ", ".join(false_lits_info)
                    step_text = f"Оскільки {cond_str}, з аксіоми ({orig_ax}) слідує: {target_lit}=1 -> {var_name}={required_var_val}"
                else:
                    step_text = f"З аксіоми ({orig_ax}) випливає: {target_lit}=1 -> {var_name}={required_var_val}"

                steps.append(step_text)

    return steps, model


def generate_step_by_step_solution(case_data: dict) -> str:
    """Генерує підсумковий звіт у вашому форматі."""
    legend_str = "\n".join([f"   {k} : {v}" for k, v in case_data['legend'].items()])
    axioms_str = "\n".join([f"  [Аксіома {i}]: {ax}" for i, ax in enumerate(case_data['axioms'], 1)])

    steps, model = evaluate_case(case_data['axioms'], case_data['legend'])

    target = case_data.get("target_hypothesis", "B")
    target_var = target.lstrip("~")
    target_val = model.get(target_var, 0)

    steps_formatted = "\n".join(f" {s}" for s in steps)
    ans_bool = "true" if target_val == 1 else "false"
    answer_str = f"Answer: {target_var}={target_val} means {target_var} is {ans_bool} -> {target}"

    return (
        f"[Опис розслідування]:\n {case_data['description']}\n\n"
        f" Легенда змінних:\n{legend_str}\n"
        f"==================================================>\n"
        f"--- БАЗА ЗНАНЬ (АКСІОМИ) ---\n"
        f"{axioms_str}\n\n"
        f"Розв'язання справи:\n"
        f"{target}-?\n"
        f"{steps_formatted}\n"
        f"{answer_str}"
    )