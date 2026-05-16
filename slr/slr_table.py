"""
Módulo 4 – Constructor de la Tabla SLR(1)

Produce:
  action_table : dict[int, dict[str, str]]
      "shift N"    → desplazar y pasar al estado N
      "reduce P"   → reducir por la producción P (índice en grammar.productions)
      "accept"     → aceptar

  goto_table   : dict[int, dict[str, int]]
      GOTO[estado][no-terminal] = estado_destino

Detecta y reporta conflictos shift/reduce y reduce/reduce.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from grammar.lr0_items import LR0Automaton, LR0Item
from grammar.lr0_builder import AUGMENTED_START
from grammar.first_follow import compute_first, compute_follow, EOF_MARKER
from parsing.yalp_parser import Grammar


# ---------------------------------------------------------------------------
# Estructuras de la tabla
# ---------------------------------------------------------------------------

@dataclass
class SLRTable:
    """Tabla SLR(1) completa."""
    action: dict[int, dict[str, str]] = field(default_factory=dict)
    goto: dict[int, dict[str, int]] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)

    def get_action(self, state: int, terminal: str) -> str | None:
        return self.action.get(state, {}).get(terminal)

    def get_goto(self, state: int, non_terminal: str) -> int | None:
        return self.goto.get(state, {}).get(non_terminal)

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def print_table(self, grammar: Grammar, ignored: frozenset | None = None):
        """Imprime la tabla ACTION/GOTO en forma tabular en consola."""
        ignored = ignored or frozenset()
        terminals = sorted((grammar.terminals | {EOF_MARKER}) - ignored)
        non_terminals = sorted(grammar.non_terminals - {AUGMENTED_START})
        states = sorted(self.action.keys() | self.goto.keys())

        col_w = 14
        header = f"{'Estado':>7} | " + " ".join(f"{t:>{col_w}}" for t in terminals)
        header += " | " + " ".join(f"{nt:>{col_w}}" for nt in non_terminals)
        print(header)
        print("-" * len(header))

        for s in states:
            row = f"{s:>7} | "
            for t in terminals:
                cell = self.action.get(s, {}).get(t, "")
                row += f"{cell:>{col_w}}"
            row += " | "
            for nt in non_terminals:
                cell = str(self.goto.get(s, {}).get(nt, ""))
                row += f"{cell:>{col_w}}"
            print(row)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

class SLRTableBuilder:
    """Construye la tabla SLR(1) a partir del autómata LR(0)."""

    def __init__(self, automaton: LR0Automaton):
        self.automaton = automaton
        self.grammar: Grammar = automaton._grammar  # type: ignore[attr-defined]

    def build(self) -> SLRTable:
        first = compute_first(self.grammar)
        follow = compute_follow(self.grammar, first)

        table = SLRTable()

        # índice de producciones de la gramática ORIGINAL (sin S')
        # Los reduce usan el índice en grammar.productions
        prod_index = {
            (p.lhs, tuple(p.rhs)): i
            for i, p in enumerate(self.grammar.productions)
        }

        for state in self.automaton.states:
            sid = state.id
            table.action[sid] = {}
            table.goto[sid] = {}

            for item in state.items:
                sym = item.next_symbol

                # ---- SHIFT / GOTO ----
                if sym is not None:
                    dest = self.automaton.transitions.get(sid, {}).get(sym)
                    if dest is None:
                        continue

                    if sym in self.grammar.terminals:
                        action_str = f"shift {dest}"
                        self._set_action(table, sid, sym, action_str)

                    elif sym in self.grammar.non_terminals:
                        table.goto[sid][sym] = dest

                # ---- REDUCE / ACCEPT ----
                else:
                    if item.lhs == AUGMENTED_START:
                        # A → S · → ACCEPT
                        self._set_action(table, sid, EOF_MARKER, "accept")
                    else:
                        key = (item.lhs, item.rhs)
                        prod_idx = prod_index.get(key)
                        if prod_idx is None:
                            continue
                        action_str = f"reduce {prod_idx}"
                        for terminal in follow.get(item.lhs, set()):
                            self._set_action(table, sid, terminal, action_str)

        return table

    def _set_action(self, table: SLRTable, state: int, symbol: str, action: str):
        """Asigna una entrada ACTION, detectando conflictos."""
        existing = table.action[state].get(symbol)
        if existing is None:
            table.action[state][symbol] = action
        elif existing != action:
            conflict_msg = (
                f"CONFLICTO en estado {state}, símbolo '{symbol}': "
                f"'{existing}' vs '{action}'"
            )
            table.conflicts.append(conflict_msg)
            # Política por defecto: preferir shift sobre reduce (heurística)
            if action.startswith("shift"):
                table.action[state][symbol] = action


def build_slr_table(automaton: LR0Automaton) -> SLRTable:
    """Función de conveniencia para construir la tabla SLR(1)."""
    builder = SLRTableBuilder(automaton)
    return builder.build()
