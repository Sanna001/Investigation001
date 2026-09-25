from dataclasses import dataclass
from typing import Set, List, Tuple, Optional, Dict
from logic.models import Clause, Literal, Formula
from logic.parser import parse_formula
from logic.cnf import to_CNF, formula_to_clauses

@dataclass
class DeductionStep:
    result_clause: Clause
    parent1: Clause
    parent2: Clause
    resolved_literal: Literal

@dataclass
class DeductionTree:
    status: str  
    steps: List[DeductionStep]
    final_clause: Optional[Clause] = None

def resolve(c1: Clause, c2: Clause) -> Tuple[Set[Clause], Optional[Literal]]:
    """Шкалує резолюцію між двома клаузами."""
    resolvents = set()
    resolved_lit = None

    for lit1 in c1.literals:
        complement = Literal(lit1.name, not lit1.negated)
        if complement in c2.literals:
            resolved_lit = lit1
            new_lits = (c1.literals - {lit1}) | (c2.literals - {complement})
            resolvents.add(Clause(frozenset(new_lits)))
            break 
            
    return resolvents, resolved_lit

def prove(kb_clauses: Set[Clause], hypothesis_clause: Clause) -> DeductionTree:
    """
    Доводить гіпотезу методом refutation (спростування від супротивного).
    Конвертує всі аксіоми у клаузи КНФ та додає заперечення гіпотези.
    """
    working_set = set()
    
    for item in kb_clauses:
        if isinstance(item, str):
            parsed = parse_formula(item)
            working_set.update(formula_to_clauses(parsed))
        elif isinstance(item, Clause):
            working_set.add(item)
        elif isinstance(item, Formula):
            working_set.update(formula_to_clauses(item))

    for lit in hypothesis_clause.literals:
        inverted_lit = Literal(lit.name, not lit.negated)
        working_set.add(Clause(frozenset([inverted_lit])))

    parent_map: Dict[Clause, Tuple[Clause, Clause, Literal]] = {}
    all_clauses = set(working_set)

    changed = True
    while changed:
        changed = False
        new_clauses_this_round = []
        clause_list = list(all_clauses)
        
        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                c1, c2 = clause_list[i], clause_list[j]
                resolvents, lit = resolve(c1, c2)
                
                for res in resolvents:
                    has_tautology = any(Literal(l.name, not l.negated) in res.literals for l in res.literals)
                    if not has_tautology and res not in all_clauses:
                        if res not in parent_map:
                            parent_map[res] = (c1, c2, lit)
                        if res.is_empty:
                            all_clauses.add(res)
                            steps = reconstruct_steps(res, parent_map)
                            return DeductionTree("PROVED", steps, res)
                        
                        new_clauses_this_round.append(res)
        
        for res in new_clauses_this_round:
            if res not in all_clauses:
                all_clauses.add(res)
                changed = True

    return DeductionTree("UNDETERMINED", reconstruct_all_steps(parent_map))

def reconstruct_steps(target: Clause, parent_map: Dict[Clause, Tuple[Clause, Clause, Literal]]) -> List[DeductionStep]:
    steps = []
    visited = set()
    
    def dfs(c: Clause):
        if c in parent_map and c not in visited:
            visited.add(c)
            c1, c2, lit = parent_map[c]
            dfs(c1)
            dfs(c2)
            steps.append(DeductionStep(c, c1, c2, lit))
            
    dfs(target)
    return steps

def reconstruct_all_steps(parent_map: Dict[Clause, Tuple[Clause, Clause, Literal]]) -> List[DeductionStep]:
    return [DeductionStep(res, c1, c2, lit) for res, (c1, c2, lit) in parent_map.items()]

def is_minimal_inconsistent(kb_clauses: Set[Clause]) -> bool:
    """Перевіряє, чи є база суперечливою і чи є вона мінімальною."""
    def check_inconsistency(clauses: Set[Clause]) -> bool:
        curr = set()
        for item in clauses:
            if isinstance(item, str):
                curr.update(formula_to_clauses(parse_formula(item)))
            elif isinstance(item, Clause):
                curr.add(item)
            elif isinstance(item, Formula):
                curr.update(formula_to_clauses(item))
                
        changed = True
        while changed:
            changed = False
            lst = list(curr)
            for i in range(len(lst)):
                for j in range(i+1, len(lst)):
                    res, _ = resolve(lst[i], lst[j])
                    for r in res:
                        if r.is_empty:
                            return True
                        if r not in curr:
                            curr.add(r)
                            changed = True
        return False

    if not check_inconsistency(kb_clauses):
        return False

    kb_list = list(kb_clauses)
    for i in range(len(kb_list)):
        subset = set(kb_list[:i] + kb_list[i+1:])
        if check_inconsistency(subset):
            return False
            
    return True