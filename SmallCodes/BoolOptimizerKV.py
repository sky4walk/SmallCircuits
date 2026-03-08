#!/usr/bin/env python3
"""
Boolean Expression Minimizer
=============================
Parses arbitrary boolean expressions, minimizes them via Quine-McCluskey,
and optionally renders a Karnaugh map (≤4 variables) in the terminal.

Usage:
    python bool_minimize.py "A AND (B OR NOT C)"
    python bool_minimize.py "A AND B OR C AND D" --no-kv
    python bool_minimize.py --minterms 0 1 3 5 7 --vars A B C
    python bool_minimize.py --minterms 0 1 3 5 7 --dontcares 2 6 --vars A B C
"""

import sys


# ─────────────────────────────────────────────────────────────────────────────
# 1. PARSER  –  converts infix string to a callable truth function
# ─────────────────────────────────────────────────────────────────────────────

PRECEDENCE = {'OR': 1, 'AND': 2, 'NOT': 3}

ALIAS = {'!': 'NOT', '~': 'NOT', '&': 'AND', '|': 'OR'}

SKIP_CHARS = set()   # commas are handled by rewrite_functional, not stripped here


def tokenize(expr: str) -> list[str]:
    """Lex the expression into normalised uppercase tokens (no regex)."""
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]

        # Skip whitespace
        if c == ' ' or c == '\t':
            i += 1
            continue

        # Comma – keep as token for rewrite_functional
        if c == ',':
            tokens.append(',')
            i += 1
            continue

        # Parentheses
        if c in '()':
            tokens.append(c)
            i += 1
            continue

        # Single-char aliases  (! ~ & |)
        if c in ALIAS:
            tokens.append(ALIAS[c])
            i += 1
            continue

        # Literals 0 / 1
        if c in '01':
            tokens.append(c)
            i += 1
            continue

        # Word token: operator keyword or variable name
        if c.isalpha() or c == '_':
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            word = expr[i:j].upper()
            # Normalise known operators; keep variable names as-is (original case)
            if word in ('AND', 'OR', 'NOT'):
                tokens.append(word)
            else:
                tokens.append(expr[i:j])   # preserve original casing for variables
            i = j
            continue

        # Unknown character – skip with warning
        print(f"  Warnung: unbekanntes Zeichen '{c}' wird ignoriert", file=sys.stderr)
        i += 1

    return tokens


def rewrite_functional(tokens: list[str]) -> list[str]:
    """
    Convert prefix functional notation to infix.
    AND(X, Y)  →  (X AND Y)
    OR(X, Y)   →  (X OR Y)
    NOT(X)     →  (NOT X)

    Uses a depth stack so nested plain parens don't confuse the operator tracking.
    """
    result = []
    # Stack entries: (operator, open_paren_depth_when_this_call_started)
    call_stack: list[tuple[str, int]] = []
    depth = 0   # current paren nesting depth

    i = 0
    while i < len(tokens):
        t = tokens[i]

        # Detect OPERATOR '('  →  start of functional call
        if t in ('AND', 'OR', 'NOT') and i + 1 < len(tokens) and tokens[i + 1] == '(':
            call_stack.append((t, depth))
            result.append('(')
            if t == 'NOT':
                result.append('NOT')
            depth += 1
            i += 2   # consume OPERATOR and '('
            continue

        if t == '(':
            result.append('(')
            depth += 1
            i += 1
            continue

        if t == ')':
            result.append(')')
            depth -= 1
            # If we're closing the paren that a functional call opened, pop it
            if call_stack and call_stack[-1][1] == depth:
                call_stack.pop()
            i += 1
            continue

        # Comma inside a binary functional call at the right depth
        if t == ',':
            if call_stack and call_stack[-1][0] in ('AND', 'OR') and call_stack[-1][1] == depth - 1:
                result.append(call_stack[-1][0])
            # else: comma in nested call – skip silently
            i += 1
            continue

        result.append(t)
        i += 1

    return result


def parse(tokens: list[str]):
    """
    Shunting-yard parser.
    Returns a list of tokens in Reverse Polish Notation (RPN).
    """
    output = []
    ops = []

    def pop_op():
        op = ops.pop()
        output.append(op)

    i = 0

    while i < len(tokens):
        t = tokens[i]

        if t in ('0', '1') or (len(t) > 1 or t.isalpha()) and t not in PRECEDENCE and t not in ('(', ')'):
            # Operand (variable or literal)
            output.append(t)

        elif t == 'NOT':
            ops.append(t)

        elif t in PRECEDENCE:
            while (ops and ops[-1] != '(' and ops[-1] in PRECEDENCE and
                   PRECEDENCE[ops[-1]] >= PRECEDENCE[t]):
                pop_op()
            ops.append(t)

        elif t == '(':
            ops.append(t)

        elif t == ')':
            while ops and ops[-1] != '(':
                pop_op()
            if ops:
                ops.pop()  # discard '('

        i += 1

    while ops:
        pop_op()

    return output


def rpn_to_lambda(rpn: list[str], variables: list[str]):
    """Compile RPN token list to a Python lambda over a variable→bool dict."""
    def evaluate(assignment: dict[str, bool]) -> bool:
        stack = []
        for t in rpn:
            if t == 'NOT':
                stack.append(not stack.pop())
            elif t == 'AND':
                b, a = stack.pop(), stack.pop()
                stack.append(a and b)
            elif t == 'OR':
                b, a = stack.pop(), stack.pop()
                stack.append(a or b)
            elif t == '1':
                stack.append(True)
            elif t == '0':
                stack.append(False)
            else:
                stack.append(assignment[t])
        return stack[0]
    return evaluate


def extract_variables(rpn: list[str]) -> list[str]:
    """Return sorted list of variable names from RPN token list."""
    ops = set(PRECEDENCE) | {'(', ')', '0', '1'}
    seen = {}
    for t in rpn:
        if t not in ops and t not in seen:
            seen[t] = None
    return list(seen.keys())


def build_truth_table(expr_str: str) -> tuple[list[str], list[int], list[int]]:
    """
    Parse expression, evaluate all input combinations.
    Returns (variables, minterms, maxterms).
    """
    tokens = tokenize(expr_str)
    # Functional notation: AND/OR immediately followed by '(' AND preceded by
    # nothing, '(' or ',' (i.e. not an operand/closing paren as in infix A AND (...))
    def is_functional_call(tokens, i):
        if tokens[i] not in ('AND', 'OR'):
            return False
        if i + 1 >= len(tokens) or tokens[i + 1] != '(':
            return False
        # Check what comes before
        if i == 0:
            return True
        prev = tokens[i - 1]
        return prev in ('(', ',')

    is_functional = any(is_functional_call(tokens, i) for i in range(len(tokens)))
    if is_functional:
        tokens = rewrite_functional(tokens)
    rpn = parse(tokens)
    variables = extract_variables(rpn)
    fn = rpn_to_lambda(rpn, variables)

    n = len(variables)
    minterms, maxterms = [], []

    for idx in range(2 ** n):
        bits = [(idx >> (n - 1 - j)) & 1 for j in range(n)]
        assignment = {v: bool(b) for v, b in zip(variables, bits)}
        result = fn(assignment)
        (minterms if result else maxterms).append(idx)

    return variables, minterms, maxterms


# ─────────────────────────────────────────────────────────────────────────────
# 2. QUINE-McCLUSKEY  –  finds minimal sum-of-products
# ─────────────────────────────────────────────────────────────────────────────

def ones(n: int) -> int:
    return bin(n).count('1')


def combine(a: str, b: str) -> str | None:
    """Try to combine two implicant strings (-, 0, 1). Returns merged or None."""
    diffs = [i for i in range(len(a)) if a[i] != b[i] and '-' not in (a[i], b[i])]
    if len(diffs) == 1 and sum(1 for i in range(len(a)) if a[i] != b[i]) == 1:
        return a[:diffs[0]] + '-' + a[diffs[0] + 1:]
    return None


def quine_mccluskey(minterms: list[int], dontcares: list[int], n_vars: int) -> list[str]:
    """
    Full Quine-McCluskey minimization.
    Returns list of prime implicant strings (e.g. '1-01').
    """
    all_terms = sorted(set(minterms + dontcares))
    if not all_terms:
        return ['0']
    if len(all_terms) == 2 ** n_vars:
        return ['1']

    # Initial implicants as binary strings
    implicants: dict[str, set[int]] = {}
    for m in all_terms:
        key = format(m, f'0{n_vars}b')
        implicants[key] = {m}

    prime_implicants: set[str] = set()

    while implicants:
        groups: dict[int, list[str]] = {}
        for imp in implicants:
            key = imp.count('1')
            if key not in groups:
                groups[key] = []
            groups[key].append(imp)

        new_implicants: dict[str, set[int]] = {}
        used: set[str] = set()

        sorted_keys = sorted(groups)
        for i in range(len(sorted_keys) - 1):
            g1 = groups[sorted_keys[i]]
            g2 = groups[sorted_keys[i + 1]]
            for a in g1:
                for b in g2:
                    merged = combine(a, b)
                    if merged is not None:
                        combined_minterms = implicants[a] | implicants[b]
                        if merged not in new_implicants:
                            new_implicants[merged] = combined_minterms
                        else:
                            new_implicants[merged] |= combined_minterms
                        used.add(a)
                        used.add(b)

        for imp in implicants:
            if imp not in used:
                prime_implicants.add(imp)

        implicants = new_implicants

    return sorted(prime_implicants)


def petrick(prime_implicants: list[str], minterms: list[int], n_vars: int) -> list[str]:
    """
    Petrick's method: find minimal cover of minterms by prime implicants.
    Returns selected prime implicant strings.
    """
    # Map each prime implicant to the minterms it covers
    coverage: dict[str, set[int]] = {}
    for pi in prime_implicants:
        covered = set()
        for m in minterms:
            bits = format(m, f'0{n_vars}b')
            if all(pi[i] == '-' or pi[i] == bits[i] for i in range(n_vars)):
                covered.add(m)
        coverage[pi] = covered

    # Essential prime implicants
    essential: list[str] = []
    remaining_minterms = set(minterms)

    changed = True
    while changed:
        changed = False
        for m in list(remaining_minterms):
            covering = [pi for pi in prime_implicants if m in coverage.get(pi, set())]
            if len(covering) == 1:
                pi = covering[0]
                if pi not in essential:
                    essential.append(pi)
                    remaining_minterms -= coverage[pi]
                    changed = True
                    break

    if not remaining_minterms:
        return essential

    # Petrick's product-of-sums for remaining minterms
    pos: list[list[str]] = []
    for m in remaining_minterms:
        covering = [pi for pi in prime_implicants if m in coverage.get(pi, set())]
        if covering:
            pos.append(covering)

    # Expand product of sums to sum of products (brute force for small problems)
    solutions = [set()]
    for clause in pos:
        new_solutions = []
        for sol in solutions:
            for pi in clause:
                new_sol = sol | {pi}
                new_solutions.append(new_sol)
        # Keep only minimal solutions
        solutions = new_solutions

    if solutions:
        best = min(solutions, key=lambda s: (len(s), sum(pi.count('1') for pi in s)))
        essential.extend(best)

    return essential


def implicant_to_term(imp: str, variables: list[str]) -> str:
    """Convert implicant string like '1-0' to algebraic term like 'A·C\\'."""
    parts = []
    for i, (bit, var) in enumerate(zip(imp, variables)):
        if bit == '1':
            parts.append(var)
        elif bit == '0':
            parts.append(f"{var}'")
    return '·'.join(parts) if parts else '1'


def minimize(minterms: list[int], dontcares: list[int], variables: list[str]) -> str:
    """Full pipeline: QMC + Petrick → minimal SOP expression string."""
    n = len(variables)

    if not minterms:
        return '0'
    if len(minterms) + len(dontcares) == 2 ** n:
        return '1'

    primes = quine_mccluskey(minterms, dontcares, n)
    selected = petrick(primes, minterms, n)

    terms = [implicant_to_term(pi, variables) for pi in selected]
    return ' + '.join(sorted(set(terms), key=lambda t: (len(t), t)))


# ─────────────────────────────────────────────────────────────────────────────
# 3. KARNAUGH MAP  –  terminal rendering for ≤4 variables
# ─────────────────────────────────────────────────────────────────────────────

GRAY2 = [0, 1, 3, 2]          # 00 01 11 10
GRAY2_LABELS = ['00', '01', '11', '10']


def kv_map(minterms: list[int], dontcares: list[int], variables: list[str]) -> str:
    n = len(variables)
    if n > 4:
        return "(KV-Diagramm nur für ≤4 Variablen verfügbar)"
    if n < 2:
        return "(KV-Diagramm benötigt mindestens 2 Variablen)"

    minterm_set = set(minterms)
    dontcare_set = set(dontcares)

    lines = []

    if n == 2:
        # Rows: A (1 var), Cols: B (1 var)
        col_var = variables[1]
        row_var = variables[0]
        lines.append(f"\n  KV-Diagramm  ({row_var} \\ {col_var})")
        lines.append(f"        {col_var}=0   {col_var}=1")
        lines.append("       ┌─────┬─────┐")
        for r in range(2):
            cells = []
            for c in range(2):
                idx = r * 2 + c
                if idx in minterm_set:
                    cells.append("  1  ")
                elif idx in dontcare_set:
                    cells.append("  X  ")
                else:
                    cells.append("  0  ")
            lines.append(f"  {row_var}={r} │{'│'.join(cells)}│")
            if r < 1:
                lines.append("       ├─────┼─────┤")
        lines.append("       └─────┴─────┘")

    elif n == 3:
        # Rows: A, Cols: BC (Gray code)
        row_var = variables[0]
        col_vars = variables[1] + variables[2]
        header_labels = ['00', '01', '11', '10']
        lines.append(f"\n  KV-Diagramm  ({row_var} \\ {col_vars})")
        lines.append(f"        {'    '.join(header_labels)}")
        lines.append("       ┌────┬────┬────┬────┐")
        for r in range(2):
            cells = []
            for g in GRAY2:
                idx = r * 4 + g
                if idx in minterm_set:
                    cells.append(" 1  ")
                elif idx in dontcare_set:
                    cells.append(" X  ")
                else:
                    cells.append(" 0  ")
            lines.append(f"  {row_var}={r} │{'│'.join(cells)}│")
            if r < 1:
                lines.append("       ├────┼────┼────┼────┤")
        lines.append("       └────┴────┴────┴────┘")
        lines.append(f"        {col_vars}:")
        lines.append(f"        {' → '.join(header_labels)}")

    elif n == 4:
        # Rows: AB, Cols: CD
        row_vars = variables[0] + variables[1]
        col_vars = variables[2] + variables[3]
        lines.append(f"\n  KV-Diagramm  ({row_vars} \\ {col_vars})")
        lines.append("           00    01    11    10")
        lines.append("        ┌──────┬──────┬──────┬──────┐")
        for ri, rg in enumerate(GRAY2):
            cells = []
            for ci, cg in enumerate(GRAY2):
                idx = rg * 4 + cg
                if idx in minterm_set:
                    cells.append("  1   ")
                elif idx in dontcare_set:
                    cells.append("  X   ")
                else:
                    cells.append("  0   ")
            row_label = GRAY2_LABELS[ri]
            lines.append(f"  {row_label}  │{'│'.join(cells)}│")
            if ri < 3:
                lines.append("        ├──────┼──────┼──────┼──────┤")
        lines.append("        └──────┴──────┴──────┴──────┘")
        lines.append(f"  {row_vars} ↓   {col_vars} →")

    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRUTH TABLE  –  terminal rendering
# ─────────────────────────────────────────────────────────────────────────────

def print_truth_table(variables: list[str], minterms: list[int],
                      dontcares: list[int]) -> str:
    n = len(variables)
    header = ' | '.join(f' {v} ' for v in variables) + ' ║  F '
    sep = '─' * len(header)
    lines = ['\n  Wahrheitstabelle', '  ' + sep, '  ' + header, '  ' + sep]
    for idx in range(2 ** n):
        bits = [(idx >> (n - 1 - j)) & 1 for j in range(n)]
        row = ' | '.join(f' {b} ' for b in bits)
        if idx in dontcares:
            f_val = ' X '
        elif idx in minterms:
            f_val = ' 1 '
        else:
            f_val = ' 0 '
        lines.append('  ' + row + ' ║ ' + f_val)
    lines.append('  ' + sep)
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI
# ─────────────────────────────────────────────────────────────────────────────

def print_header():
    print("\n╔══════════════════════════════════════════════╗")
    print("║     Boolean Expression Minimizer             ║")
    print("║     Quine-McCluskey + Karnaugh Map           ║")
    print("╚══════════════════════════════════════════════╝")


def run(args: dict):
    print_header()

    # ── Determine minterms + variables ──────────────────────────────────────
    if args['expression']:
        expr = args['expression']
        print(f"\n  Ausdruck : {expr}")
        try:
            variables, minterms, maxterms = build_truth_table(expr)
        except Exception as e:
            print(f"\n  ✗ Fehler beim Parsen: {e}")
            sys.exit(1)
        dontcares = []
    else:
        variables = args['vars']
        minterms  = list(args['minterms'])
        dontcares = list(args['dontcares'])
        n = len(variables)
        max_idx = 2 ** n - 1
        for m in minterms + dontcares:
            if m > max_idx:
                print(f"  ✗ Minterm {m} > {max_idx} (zu viele Bits für {n} Variablen)")
                sys.exit(1)

    n = len(variables)
    print(f"  Variablen: {', '.join(variables)}  (n={n})")
    print(f"  Minterme : {sorted(minterms)}")
    if dontcares:
        print(f"  Don't care: {sorted(dontcares)}")

    # ── Truth table ──────────────────────────────────────────────────────────
    print(print_truth_table(variables, minterms, dontcares))

    # ── KV map ───────────────────────────────────────────────────────────────
    if not args['no_kv']:
        print(kv_map(minterms, dontcares, variables))

    # ── Minimization ─────────────────────────────────────────────────────────
    print("\n  ── Quine-McCluskey Minimierung ──────────────")
    result = minimize(minterms, dontcares, variables)

    print(f"\n  Minimierter Ausdruck:\n")
    print(f"      F = {result}\n")
    print(f"  Legende: A' = NOT A,  ·  = AND,  +  = OR")
    print()


def print_usage():
    print("""
Verwendung:
  python bool_minimize.py "A AND (B OR NOT C)"
  python bool_minimize.py "(A OR B) AND (NOT A OR C)"
  python bool_minimize.py --minterms 0 1 3 5 7 --vars A B C
  python bool_minimize.py --minterms 1 3 7 --dontcares 0 5 --vars A B C
  python bool_minimize.py "A AND B OR C AND D" --no-kv

Optionen:
  --minterms N ...    Minterme als Dezimalzahlen
  --dontcares N ...   Don't-care-Terme
  --vars VAR ...      Variablennamen (bei --minterms erforderlich)
  --no-kv             KV-Diagramm nicht anzeigen
  --help              Diese Hilfe anzeigen

Operatoren:  AND  OR  NOT   (Kurzformen: & | ! ~)
Klammern:    ( )  werden vollständig unterstützt
""")


def parse_args(argv: list[str]) -> dict:
    """Minimal sys.argv parser – replaces argparse."""
    args = {
        'expression': None,
        'minterms': None,
        'dontcares': [],
        'vars': [],
        'no_kv': False,
    }

    if not argv or '--help' in argv or '-h' in argv:
        print_usage()
        sys.exit(0)

    i = 0
    while i < len(argv):
        tok = argv[i]

        if tok == '--no-kv':
            args['no_kv'] = True

        elif tok == '--minterms':
            args['minterms'] = []
            i += 1
            while i < len(argv) and not argv[i].startswith('--'):
                try:
                    args['minterms'].append(int(argv[i]))
                except ValueError:
                    print(f"  ✗ Kein gültiger Minterm: '{argv[i]}'")
                    sys.exit(1)
                i += 1
            continue

        elif tok == '--dontcares':
            i += 1
            while i < len(argv) and not argv[i].startswith('--'):
                try:
                    args['dontcares'].append(int(argv[i]))
                except ValueError:
                    print(f"  ✗ Kein gültiger Don't-care-Term: '{argv[i]}'")
                    sys.exit(1)
                i += 1
            continue

        elif tok == '--vars':
            i += 1
            while i < len(argv) and not argv[i].startswith('--'):
                args['vars'].append(argv[i])
                i += 1
            continue

        elif not tok.startswith('--'):
            if args['expression'] is None:
                args['expression'] = tok
            else:
                print(f"  ✗ Unerwartetes Argument: '{tok}'")
                sys.exit(1)

        else:
            print(f"  ✗ Unbekannte Option: '{tok}'")
            print_usage()
            sys.exit(1)

        i += 1

    # Validation
    if args['expression'] is None and args['minterms'] is None:
        print("  ✗ Entweder Ausdruck oder --minterms angeben.")
        print_usage()
        sys.exit(1)

    if args['minterms'] is not None and not args['vars']:
        print("  ✗ --minterms benötigt --vars")
        sys.exit(1)

    return args


def main():
    args = parse_args(sys.argv[1:])
    run(args)


if __name__ == '__main__':
    main()
