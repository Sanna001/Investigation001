from typing import Set
from logic.models import (
    Formula, Atom, NotOp, AndOp, OrOp, ImpliesOp, EquivOp, Literal, Clause
)

def eliminate_connectives(formula: Formula) -> Formula:
    """Усунення -> та <->."""
    if isinstance(formula, Atom):
        return formula
    elif isinstance(formula, NotOp):
        return NotOp(eliminate_connectives(formula.operand))
    elif isinstance(formula, AndOp):
        return AndOp(eliminate_connectives(formula.left), eliminate_connectives(formula.right))
    elif isinstance(formula, OrOp):
        return OrOp(eliminate_connectives(formula.left), eliminate_connectives(formula.right))
    elif isinstance(formula, ImpliesOp):
        # A -> B  <=>  ~A v B
        return OrOp(NotOp(eliminate_connectives(formula.left)), eliminate_connectives(formula.right))
    elif isinstance(formula, EquivOp):
        # A <-> B  <=>  (~A v B) & (~B v A)
        l = eliminate_connectives(formula.left)
        r = eliminate_connectives(formula.right)
        return AndOp(OrOp(NotOp(l), r), OrOp(NotOp(r), l))
    raise TypeError(f"Невідомий тип формули: {type(formula)}")

def move_not_inward(formula: Formula) -> Formula:
    """Закони де Моргана та подвійне заперечення."""
    if isinstance(formula, Atom):
        return formula
    elif isinstance(formula, NotOp):
        op = formula.operand
        if isinstance(op, NotOp):
            return move_not_inward(op.operand)  # ~~A -> A
        elif isinstance(op, AndOp):
            # ~(A & B) -> ~A v ~B
            return OrOp(move_not_inward(NotOp(op.left)), move_not_inward(NotOp(op.right)))
        elif isinstance(op, OrOp):
            # ~(A v B) -> ~A & ~B
            return AndOp(move_not_inward(NotOp(op.left)), move_not_inward(NotOp(op.right)))
        else:
            return NotOp(move_not_inward(op))
    elif isinstance(formula, AndOp):
        return AndOp(move_not_inward(formula.left), move_not_inward(formula.right))
    elif isinstance(formula, OrOp):
        return OrOp(move_not_inward(formula.left), move_not_inward(formula.right))
    return formula

def distribute_or_over_and(formula: Formula) -> Formula:
    """Дистрибутивність v над &."""
    if isinstance(formula, Atom) or isinstance(formula, NotOp):
        return formula
    elif isinstance(formula, AndOp):
        return AndOp(distribute_or_over_and(formula.left), distribute_or_over_and(formula.right))
    elif isinstance(formula, OrOp):
        left = distribute_or_over_and(formula.left)
        right = distribute_or_over_and(formula.right)
        
        # (A & B) v C  <=>  (A v C) & (B v C)
        if isinstance(left, AndOp):
            return AndOp(distribute_or_over_and(OrOp(left.left, right)),
                         distribute_or_over_and(OrOp(left.right, right)))
        # C v (A & B)  <=>  (C v A) & (C v B)
        if isinstance(right, AndOp):
            return AndOp(distribute_or_over_and(OrOp(left, right.left)),
                         distribute_or_over_and(OrOp(left, right.right)))
        return OrOp(left, right)
    return formula

def to_CNF(formula: Formula) -> Formula:
    f = eliminate_connectives(formula)
    f = move_not_inward(f)
    prev = None
    while prev != f:
        prev = f
        f = distribute_or_over_and(f)
    return f

def formula_to_clauses(formula: Formula) -> Set[Clause]:
    cnf = to_CNF(formula)
    clauses = set()

    def extract_conjuncts(f: Formula):
        if isinstance(f, AndOp):
            extract_conjuncts(f.left)
            extract_conjuncts(f.right)
        else:
            clauses.add(extract_disjuncts(f))

    def extract_disjuncts(f: Formula) -> Clause:
        lits = set()
        def collect(sub):
            if isinstance(sub, Atom):
                lits.add(Literal(sub.name, False))
            elif isinstance(sub, NotOp) and isinstance(sub.operand, Atom):
                lits.add(Literal(sub.operand.name, True))
            elif isinstance(sub, OrOp):
                collect(sub.left)
                collect(sub.right)
            else:
                if isinstance(sub, NotOp):
                    lits.add(Literal(sub.operand.name, True))
                else:
                    lits.add(Literal(str(sub), False))
        collect(f)
        return Clause(frozenset(lits))

    extract_conjuncts(cnf)
    return clauses