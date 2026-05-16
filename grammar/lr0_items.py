"""
Módulo 3 – Estructuras de datos del autómata LR(0)

LR0Item  : ítem de la forma  A → α · β
LR0State : estado = conjunto de ítems LR(0)
LR0Automaton : grafo de estados + transiciones
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Ítem LR(0)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LR0Item:
    """
    Representa un ítem LR(0): A → α · β

    Atributos:
        lhs   : lado izquierdo de la producción (no-terminal)
        rhs   : tuple completo de símbolos del RHS
        dot   : índice del punto (0..len(rhs))
    """
    lhs: str
    rhs: tuple[str, ...]
    dot: int = 0

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def next_symbol(self) -> Optional[str]:
        """Símbolo inmediatamente después del punto, o None si está al final."""
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None

    @property
    def is_complete(self) -> bool:
        """True cuando el punto está al final: A → α ·"""
        return self.dot == len(self.rhs)

    def advance(self) -> "LR0Item":
        """Retorna el ítem con el punto avanzado un símbolo."""
        if self.is_complete:
            raise ValueError("No se puede avanzar el punto: ítem completo.")
        return LR0Item(self.lhs, self.rhs, self.dot + 1)

    # ------------------------------------------------------------------
    # Representación
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        symbols = list(self.rhs)
        symbols.insert(self.dot, "·")
        rhs_str = " ".join(symbols) if symbols else "·"
        return f"{self.lhs} → {rhs_str}"

    def __repr__(self) -> str:
        return f"LR0Item({self!s})"


# ---------------------------------------------------------------------------
# Estado LR(0)
# ---------------------------------------------------------------------------

@dataclass
class LR0State:
    """
    Estado del autómata LR(0).

    Atributos:
        id    : identificador numérico único
        items : conjunto de ítems LR(0) (kernel + clausura)
    """
    id: int
    items: frozenset[LR0Item]

    def __hash__(self):
        return hash(self.items)

    def __eq__(self, other) -> bool:
        if not isinstance(other, LR0State):
            return False
        return self.items == other.items

    def __str__(self) -> str:
        items_str = "\n  ".join(str(i) for i in sorted(self.items, key=str))
        return f"Estado {self.id}:\n  {items_str}"

    def __repr__(self) -> str:
        return f"LR0State(id={self.id}, items={len(self.items)})"


# ---------------------------------------------------------------------------
# Autómata LR(0)
# ---------------------------------------------------------------------------

@dataclass
class LR0Automaton:
    """
    Autómata LR(0) completo.

    Atributos:
        states      : lista ordenada de estados
        transitions : dict[int, dict[str, int]]
                      transitions[estado_id][símbolo] = estado_destino_id
        initial_state: estado inicial (I0)
    """
    states: list[LR0State] = field(default_factory=list)
    transitions: dict[int, dict[str, int]] = field(default_factory=dict)
    initial_state: Optional[LR0State] = None

    def get_state(self, state_id: int) -> LR0State:
        return self.states[state_id]

    def add_transition(self, from_id: int, symbol: str, to_id: int):
        self.transitions.setdefault(from_id, {})[symbol] = to_id

    def __repr__(self) -> str:
        return (
            f"LR0Automaton("
            f"{len(self.states)} estados, "
            f"{sum(len(v) for v in self.transitions.values())} transiciones)"
        )
