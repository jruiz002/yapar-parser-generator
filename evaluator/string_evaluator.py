"""
Módulo 6 – Evaluador de cadenas (simulación SLR(1))

Implementa el algoritmo estándar de parseo con pila LR:

  stack = [0]
  loop:
    a = next token
    s = top(stack)
    acción = ACTION[s][a]
    si shift n  → push(a), push(n)
    si reduce p → pop 2*|rhs|, s' = top(stack), push(lhs), push(GOTO[s'][lhs])
    si accept   → ACEPTADO
    si error    → RECHAZO con mensaje

El evaluador acepta tokens como tuplas (tipo, lexema) o como strings simples.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from slr.slr_table import SLRTable
from parsing.yalp_parser import Grammar
from grammar.first_follow import EOF_MARKER


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class ParseStep:
    """Snapshot de un paso del algoritmo de parseo."""
    step: int
    stack: list          # copia de la pila en ese momento
    remaining: list[str] # tokens restantes
    action: str          # descripción de la acción


@dataclass
class ParseResult:
    """Resultado completo del parseo de una cadena."""
    accepted: bool
    message: str
    steps: list[ParseStep] = field(default_factory=list)
    error_token: str | None = None
    error_state: int | None = None

    def __str__(self) -> str:
        status = "ACCEPTED ✓" if self.accepted else f"SYNTAX ERROR ✗"
        return f"{status} — {self.message}"


# ---------------------------------------------------------------------------
# Evaluador
# ---------------------------------------------------------------------------

class StringEvaluator:
    """
    Evalúa una secuencia de tokens contra la tabla SLR(1).

    Args:
        table  : tabla SLR(1) construida por el Módulo 4
        grammar: gramática (para acceder a producciones por índice)
    """

    def __init__(self, table: SLRTable, grammar: Grammar):
        self.table = table
        self.grammar = grammar

    def evaluate(
        self,
        tokens: list,
        ignored: frozenset[str] | None = None,
        trace: bool = True,
    ) -> ParseResult:
        """
        Evalúa una secuencia de tokens.

        Args:
            tokens : lista de tokens. Cada elemento puede ser:
                       - str        (tipo del token, sin lexema)
                       - tuple[str, str]  (tipo, lexema)
            ignored: conjunto de tipos de token a ignorar (ej. WS)
            trace  : si True, registra cada paso en ParseResult.steps

        Retorna un ParseResult con el veredicto y el rastro de pasos.
        """
        ignored = ignored or frozenset()

        # Normalizar tokens: extraer el tipo
        token_types: list[str] = []
        for tok in tokens:
            if isinstance(tok, tuple):
                token_types.append(tok[0])
            else:
                token_types.append(str(tok))

        # Filtrar ignorados
        token_types = [t for t in token_types if t not in ignored]
        token_types.append(EOF_MARKER)

        stack: list[int] = [0]
        steps: list[ParseStep] = []
        pos = 0
        step_num = 0

        while True:
            state = stack[-1]
            lookahead = token_types[pos] if pos < len(token_types) else EOF_MARKER
            action = self.table.get_action(state, lookahead)

            # Registrar paso
            if trace:
                steps.append(ParseStep(
                    step=step_num,
                    stack=list(stack),
                    remaining=list(token_types[pos:]),
                    action=action or "error",
                ))
            step_num += 1

            if action is None:
                # Error sintáctico
                msg = (
                    f"Token inesperado '{lookahead}' en estado {state}. "
                    f"Tokens válidos: {sorted(self.table.action.get(state, {}).keys())}"
                )
                return ParseResult(
                    accepted=False,
                    message=msg,
                    steps=steps,
                    error_token=lookahead,
                    error_state=state,
                )

            if action == "accept":
                return ParseResult(
                    accepted=True,
                    message="Cadena aceptada exitosamente.",
                    steps=steps,
                )

            if action.startswith("shift"):
                next_state = int(action.split()[1])
                stack.append(next_state)
                pos += 1

            elif action.startswith("reduce"):
                prod_idx = int(action.split()[1])
                prod = self.grammar.productions[prod_idx]
                # Sacar 2*len(rhs) elementos de la pila
                # La pila sólo contiene enteros (estados), no símbolos
                # Protocolo estándar: la pila almacena estados
                for _ in prod.rhs:
                    stack.pop()
                top_state = stack[-1]
                lhs = prod.lhs
                goto_state = self.table.get_goto(top_state, lhs)
                if goto_state is None:
                    msg = (
                        f"Error en GOTO[{top_state}][{lhs}] durante reduce "
                        f"por {prod}."
                    )
                    return ParseResult(
                        accepted=False,
                        message=msg,
                        steps=steps,
                        error_state=top_state,
                    )
                stack.append(goto_state)

                if trace:
                    # Actualizar la acción del paso anterior con descripción rica
                    steps[-1] = ParseStep(
                        step=steps[-1].step,
                        stack=steps[-1].stack,
                        remaining=steps[-1].remaining,
                        action=f"reduce {prod}",
                    )
            else:
                return ParseResult(
                    accepted=False,
                    message=f"Acción desconocida: {action!r}",
                    steps=steps,
                )

            if step_num > 10_000:
                return ParseResult(
                    accepted=False,
                    message="Límite de pasos excedido (posible ciclo).",
                    steps=steps,
                )


# ---------------------------------------------------------------------------
# Utilidades de impresión
# ---------------------------------------------------------------------------

def print_parse_trace(result: ParseResult):
    """Imprime el rastro de parseo en formato tabular."""
    col_step = 6
    col_stack = 25
    col_remaining = 30
    col_action = 40

    header = (
        f"{'Paso':>{col_step}} | "
        f"{'Pila':<{col_stack}} | "
        f"{'Entrada restante':<{col_remaining}} | "
        f"{'Acción':<{col_action}}"
    )
    print(header)
    print("-" * len(header))

    for s in result.steps:
        stack_str = str(s.stack)[-col_stack:]
        remaining_str = " ".join(s.remaining)
        remaining_str = remaining_str[:col_remaining]
        action_str = str(s.action)[:col_action]
        print(
            f"{s.step:>{col_step}} | "
            f"{stack_str:<{col_stack}} | "
            f"{remaining_str:<{col_remaining}} | "
            f"{action_str:<{col_action}}"
        )

    print()
    print(f"  → {result}")
