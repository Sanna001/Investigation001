from dataclasses import dataclass
from typing import FrozenSet, Set, Union

@dataclass(frozen=True)
class Literal:
    name: str
    negated: bool = False

    def __invert__(self):
        return Literal(self.name, not self.negated)

    def __str__(self):
        return f"~{self.name}" if self.negated else self.name

@dataclass(frozen=True)
class Clause:
    literals: FrozenSet[Literal]

    def __str__(self):
        if not self.literals:
            return "-" 
        return " v ".join(str(lit) for lit in sorted(self.literals, key=lambda l: (l.name, l.negated)))

    @property
    def is_empty(self) -> bool:
        return len(self.literals) == 0

class Formula:
    pass

@dataclass(frozen=True)
class Atom(Formula):
    name: str
    def __str__(self): return self.name

@dataclass(frozen=True)
class NotOp(Formula):
    operand: Formula
    def __str__(self): return f"~({self.operand})"

@dataclass(frozen=True)
class AndOp(Formula):
    left: Formula
    right: Formula
    def __str__(self): return f"({self.left} & {self.right})"

@dataclass(frozen=True)
class OrOp(Formula):
    left: Formula
    right: Formula
    def __str__(self): return f"({self.left} v {self.right})"

@dataclass(frozen=True)
class ImpliesOp(Formula):
    left: Formula
    right: Formula
    def __str__(self): return f"({self.left} -> {self.right})"

@dataclass(frozen=True)
class EquivOp(Formula):
    left: Formula
    right: Formula
    def __str__(self): return f"({self.left} <-> {self.right})"