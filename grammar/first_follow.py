"""
Módulo 3 – Conjuntos FIRST y FOLLOW

Implementa:
  compute_first(grammar)  → dict[str, set[str]]
  compute_follow(grammar, first) → dict[str, set[str]]

Convenciones:
  - EPSILON es representado internamente con la cadena vacía ""
  - "$" es el marcador de fin de entrada (EOF)
"""

from __future__ import annotations
from parsing.yalp_parser import Grammar

EPSILON = ""
EOF_MARKER = "$"


def compute_first(grammar: Grammar) -> dict[str, set[str]]:
    """
    Calcula FIRST(X) para todos los símbolos de la gramática.

    FIRST(a) = {a}              si a es terminal
    FIRST(ε) = {ε}
    FIRST(A) = unión de FIRST de cada alternativa, propagando ε correctamente.
    """
    first: dict[str, set[str]] = {}

    # Inicializar terminales
    for t in grammar.terminals:
        first[t] = {t}
    first[EOF_MARKER] = {EOF_MARKER}
    first[EPSILON] = {EPSILON}

    # Inicializar no-terminales con conjuntos vacíos
    for nt in grammar.non_terminals:
        first[nt] = set()

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            lhs = prod.lhs
            before = len(first[lhs])

            if not prod.rhs:
                # producción vacía A → ε
                first[lhs].add(EPSILON)
            else:
                # A → X1 X2 … Xk
                all_have_epsilon = True
                for sym in prod.rhs:
                    sym_first = first.get(sym, {sym})
                    # Añadir FIRST(sym) \ {ε}
                    first[lhs] |= sym_first - {EPSILON}
                    if EPSILON not in sym_first:
                        all_have_epsilon = False
                        break
                if all_have_epsilon:
                    first[lhs].add(EPSILON)

            if len(first[lhs]) != before:
                changed = True

    return first


def compute_follow(grammar: Grammar, first: dict[str, set[str]]) -> dict[str, set[str]]:
    """
    Calcula FOLLOW(A) para todos los no-terminales.

    Reglas:
      1. $ ∈ FOLLOW(S)  (S = símbolo inicial)
      2. Si B → α A β, entonces FIRST(β)\{ε} ⊆ FOLLOW(A)
      3. Si B → α A β  y ε ∈ FIRST(β), entonces FOLLOW(B) ⊆ FOLLOW(A)
      4. Si B → α A,   entonces FOLLOW(B) ⊆ FOLLOW(A)
    """
    follow: dict[str, set[str]] = {nt: set() for nt in grammar.non_terminals}
    follow[grammar.start_symbol].add(EOF_MARKER)

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            trailer: set[str] = set(follow[prod.lhs])
            # recorrer RHS de derecha a izquierda
            for sym in reversed(prod.rhs):
                if sym in grammar.non_terminals:
                    before = len(follow[sym])
                    follow[sym] |= trailer
                    if len(follow[sym]) != before:
                        changed = True
                    # actualizar trailer
                    sym_first = first.get(sym, set())
                    if EPSILON in sym_first:
                        trailer = (trailer | sym_first) - {EPSILON}
                    else:
                        trailer = sym_first - {EPSILON}
                else:
                    # terminal
                    trailer = first.get(sym, {sym}) - {EPSILON}

    return follow


def first_of_sequence(sequence: list[str], first: dict[str, set[str]]) -> set[str]:
    """
    Calcula FIRST(X1 X2 … Xk) para una secuencia de símbolos.
    Útil para el algoritmo de parseo LALR(1) (no requerido en SLR).
    """
    result: set[str] = set()
    for sym in sequence:
        sym_first = first.get(sym, {sym})
        result |= sym_first - {EPSILON}
        if EPSILON not in sym_first:
            return result
    result.add(EPSILON)
    return result
