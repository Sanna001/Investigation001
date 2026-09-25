from typing import Dict, Any, Set
from logic.parser import parse_formula
from logic.cnf import formula_to_clauses
from logic.models import Clause
from logic.resolution import prove, DeductionTree

class GameSession:
    def __init__(self, profile, case_data: Dict[str, Any]):
        self.profile = profile
        self.case_data = case_data
        self.attempts_left = 3
        self.kb_clauses: Set[Clause] = self._prepare_kb()

    def _prepare_kb(self) -> Set[Clause]:
        clauses = set()
        for formula_str in self.case_data["axioms"]:
            parsed = parse_formula(formula_str)
            cls = formula_to_clauses(parsed)
            clauses.update(cls)
        return clauses

    def verify_hypothesis(self, hyp_str: str) -> DeductionTree:
        parsed_hyp = parse_formula(hyp_str)
        hyp_clauses = formula_to_clauses(parsed_hyp)
        
        all_lits = set()
        for c in hyp_clauses:
            all_lits.update(c.literals)
        target_clause = Clause(frozenset(all_lits))
        
        return prove(self.kb_clauses, target_clause)