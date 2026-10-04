def evaluate_step_by_step(axioms_strs, legend):
    """
    Алгоритм покрокового розв'язання бази знань.
    Визначає значення змінних (1 або 0) та генерує покроковий лог.
    """
    vars_set = set(legend.keys())
    values = {}
    steps = []
    remaining_axioms = list(axioms_strs)

    changed = True
    while changed:
        changed = False
        
        #  Пошук одиничних літералів 
        for ax in list(remaining_axioms):
            ax_clean = ax.replace(" ", "").replace("(", "").replace(")", "")
            
            if ax_clean.startswith("~") and ax_clean[1:] in vars_set:
                var = ax_clean[1:]
                if var not in values:
                    values[var] = 0
                    steps.append(f" ~{var}=1 -> {var}=0")
                    remaining_axioms.remove(ax)
                    changed = True
            elif ax_clean in vars_set:
                var = ax_clean
                if var not in values:
                    values[var] = 1
                    steps.append(f" {var}=1")
                    remaining_axioms.remove(ax)
                    changed = True

        # 2. Обробка диз'юнкцій (A v B) та імплікацій (A -> B)
        for ax in list(remaining_axioms):
            if "v" in ax:
                parts = [p.strip(" ()") for p in ax.split("v")]
                for i, p in enumerate(parts):
                    other_p = parts[1 - i]
                    
                    p_is_false = False
                    if p.startswith("~") and values.get(p[1:]) == 1:
                        p_is_false = True
                    elif not p.startswith("~") and values.get(p) == 0:
                        p_is_false = True

                    if p_is_false:
                        target_var = other_p.lstrip("~")
                        is_neg = other_p.startswith("~")
                        val = 0 if is_neg else 1
                        
                        if target_var not in values:
                            values[target_var] = val
                            steps.append(f"({ax})=1 -> if {p}=0 then {other_p} has to be 1 -> {other_p}=1")
                            remaining_axioms.remove(ax)
                            changed = True
                            break

            elif "->" in ax:
                left, right = [p.strip(" ()") for p in ax.split("->")]
                left_var = left.lstrip("~")
                left_is_neg = left.startswith("~")
                left_is_true = (values.get(left_var) == 0 if left_is_neg else values.get(left_var) == 1)

                if left_is_true:
                    right_var = right.lstrip("~")
                    right_is_neg = right.startswith("~")
                    val = 0 if right_is_neg else 1

                    if right_var not in values:
                        values[right_var] = val
                        steps.append(f"({ax})=1 if {left}=1 then {right} cannot be 0, -> {right}=1")
                        if right_is_neg:
                            steps.append(f" {right}=1 -> {right_var}=0")
                        remaining_axioms.remove(ax)
                        changed = True

    return steps, values


def generate_step_by_step_solution(case_data: dict) -> str:
    """Генерує фінальний текст розв'язку справи у потрібному форматі."""
    legend_str = "\n".join([f"   {k} : {v}" for k, v in case_data['legend'].items()])
    axioms_str = "\n".join([f"  [Аксіома {i}]: ({ax})" for i, ax in enumerate(case_data['axioms'], 1)])

    steps, values = evaluate_step_by_step(case_data['axioms'], case_data['legend'])
    
    target = case_data.get("target_hypothesis", "V")
    target_var = target.lstrip("~")
    target_val = values.get(target_var, 0)
    
    steps_formatted = "\n".join(steps)
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