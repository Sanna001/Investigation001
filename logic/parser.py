from logic.models import Formula, Atom, NotOp, AndOp, OrOp, ImpliesOp, EquivOp

class ParseError(Exception):
    pass

def parse_formula(expression: str) -> Formula:
    """Простий рекурсивний спуск для парсингу логічних виразів."""
    s = expression.replace(" ", "")
    if not s:
        raise ParseError("Порожній вираз.")

    def parse_equiv(tokens, pos):
        left, pos = parse_implication(tokens, pos)
        while pos < len(tokens) and tokens[pos] == '<->':
            pos += 1
            right, pos = parse_implication(tokens, pos)
            left = EquivOp(left, right)
        return left, pos

    def parse_implication(tokens, pos):
        left, pos = parse_or(tokens, pos)
        while pos < len(tokens) and tokens[pos] == '->':
            pos += 1
            right, pos = parse_or(tokens, pos)
            left = ImpliesOp(left, right)
        return left, pos

    def parse_or(tokens, pos):
        left, pos = parse_and(tokens, pos)
        while pos < len(tokens) and tokens[pos] in ('v', '|'):
            pos += 1
            right, pos = parse_and(tokens, pos)
            left = OrOp(left, right)
        return left, pos

    def parse_and(tokens, pos):
        left, pos = parse_unary(tokens, pos)
        while pos < len(tokens) and tokens[pos] == '&':
            pos += 1
            right, pos = parse_unary(tokens, pos)
            left = AndOp(left, right)
        return left, pos

    def parse_unary(tokens, pos):
        if pos < len(tokens) and tokens[pos] == '~':
            pos += 1
            operand, pos = parse_unary(tokens, pos)
            return NotOp(operand), pos
        return parse_primary(tokens, pos)

    def parse_primary(tokens, pos):
        if pos >= len(tokens):
            raise ParseError("Неочікуваний кінець виразу.")
        
        token = tokens[pos]
        if token == '(':
            pos += 1
            expr, pos = parse_equiv(tokens, pos)
            if pos >= len(tokens) or tokens[pos] != ')':
                raise ParseError("Пропущена дужка ')'")
            return expr, pos + 1
        elif token.isalnum() and token[0].isupper():
            return Atom(token), pos + 1
        else:
            raise ParseError(f"Невідомий символ або лексема: '{token}'")

    tokens = []
    i = 0
    while i < len(s):
        if s[i:i+3] == '<->':
            tokens.append('<->')
            i += 3
        elif s[i:i+2] == '->':
            tokens.append('->')
            i += 2
        elif s[i] in ('~', '&', 'v', '|', '(', ')'):
            tokens.append(s[i])
            i += 1
        elif s[i].isupper():
            start = i
            i += 1
            while i < len(s) and s[i].isdigit():
                i += 1
            tokens.append(s[start:i])
        else:
            raise ParseError(f"Недопустимий символ: '{s[i]}'")

    expr, pos = parse_equiv(tokens, 0)
    if pos != len(tokens):
            raise ParseError("Зайві символи наприкінці виразу.")
    return expr