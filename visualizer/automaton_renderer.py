"""
Módulo 5 – Visualizador del Autómata LR(0)

Genera representaciones visuales del autómata usando Graphviz (pydot).

Funciones principales:
  render_automaton_png(automaton, output_path)  → genera archivo PNG
"""

from __future__ import annotations
import os
import textwrap
from grammar.lr0_items import LR0Automaton, LR0State, LR0Item


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_item(item: LR0Item) -> str:
    """Formatea un ítem LR(0) como cadena legible para el nodo."""
    symbols = list(item.rhs)
    symbols.insert(item.dot, "·")
    rhs_str = " ".join(symbols) if symbols else "·"
    return f"{item.lhs} → {rhs_str}"


def _node_label(state: LR0State) -> str:
    """Etiqueta multi-línea para el nodo de un estado."""
    lines = [f"Estado {state.id}"]
    for item in sorted(state.items, key=lambda i: (i.lhs, str(i))):
        lines.append(_format_item(item))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Renderizado PNG (Graphviz / pydot)
# ---------------------------------------------------------------------------

def render_automaton_png(automaton: LR0Automaton, output_path: str) -> str:
    """
    Genera una imagen PNG del autómata LR(0) usando graphviz (pydot).

    Retorna la ruta al archivo generado.
    Requiere: pip install pydot  y  graphviz en el PATH del sistema.
    """
    try:
        import pydot  # type: ignore
    except ImportError:
        print("  [Visualizador] pydot no instalado — omitiendo PNG.")
        return ""

    graph = pydot.Dot(
        graph_type="digraph",
        rankdir="LR",
        fontname="Helvetica",
        bgcolor="#1e1e2e",
    )
    graph.set_node_defaults(
        shape="box",
        style="filled,rounded",
        fillcolor="#313244",
        fontcolor="#cdd6f4",
        fontname="Courier New",
        fontsize="10",
    )
    graph.set_edge_defaults(
        color="#89b4fa",
        fontcolor="#a6e3a1",
        fontname="Helvetica",
        fontsize="9",
    )

    # Nodo inicial (flecha de entrada)
    graph.add_node(pydot.Node("__start__", shape="point", width="0.1"))
    graph.add_edge(pydot.Edge("__start__", f"s{automaton.initial_state.id}"))

    for state in automaton.states:
        label = _node_label(state)
        # Resaltar estado inicial
        fillcolor = "#45475a" if state.id == automaton.initial_state.id else "#313244"
        node = pydot.Node(
            f"s{state.id}",
            label=label,
            fillcolor=fillcolor,
        )
        graph.add_node(node)

    for from_id, transitions in automaton.transitions.items():
        for symbol, to_id in transitions.items():
            edge = pydot.Edge(
                f"s{from_id}",
                f"s{to_id}",
                label=f" {symbol} ",
            )
            graph.add_edge(edge)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    graph.write_png(output_path)
    return output_path



