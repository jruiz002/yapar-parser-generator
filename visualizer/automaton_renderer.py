"""
Módulo 5 – Visualizador del Autómata LR(0)

Genera representaciones visuales del autómata usando Graphviz (pydot).

Funciones principales:
  render_automaton_png(automaton, output_path)  → genera archivo PNG
  render_automaton_html(automaton, output_path) → genera archivo HTML interactivo
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


# ---------------------------------------------------------------------------
# Renderizado HTML (interactivo con vis.js)
# ---------------------------------------------------------------------------

def render_automaton_html(automaton: LR0Automaton, output_path: str) -> str:
    """
    Genera un archivo HTML con el autómata renderizado de forma interactiva
    usando la biblioteca vis.js (embebida vía CDN, sin dependencias locales).

    Retorna la ruta al archivo generado.
    """
    # Construir datos JSON para vis.js
    nodes_js_parts: list[str] = []
    edges_js_parts: list[str] = []

    for state in automaton.states:
        label_lines = [f"I{state.id}"]
        for item in sorted(state.items, key=lambda i: (i.lhs, str(i))):
            label_lines.append(_format_item(item))
        label = "\\n".join(label_lines)
        color = "#45475a" if state.id == automaton.initial_state.id else "#313244"
        nodes_js_parts.append(
            f'  {{id: {state.id}, label: "{label}", '
            f'color: {{background: "{color}", border: "#89b4fa"}}}}'
        )

    edge_id = 0
    for from_id, transitions in automaton.transitions.items():
        for symbol, to_id in transitions.items():
            edges_js_parts.append(
                f'  {{id: {edge_id}, from: {from_id}, to: {to_id}, label: "{symbol}"}}'
            )
            edge_id += 1

    nodes_js = "[\n" + ",\n".join(nodes_js_parts) + "\n]"
    edges_js = "[\n" + ",\n".join(edges_js_parts) + "\n]"

    html = textwrap.dedent(f"""\
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Autómata LR(0) – YAPar</title>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" />
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
          background: #1e1e2e;
          color: #cdd6f4;
          font-family: 'Courier New', monospace;
          display: flex;
          flex-direction: column;
          height: 100vh;
        }}
        header {{
          padding: 12px 24px;
          background: #181825;
          border-bottom: 1px solid #313244;
          display: flex;
          align-items: center;
          gap: 16px;
        }}
        header h1 {{ font-size: 1.2rem; color: #cba6f7; }}
        header span {{ font-size: 0.85rem; color: #6c7086; }}
        #network {{
          flex: 1;
          background: #1e1e2e;
        }}
        #legend {{
          padding: 8px 24px;
          background: #181825;
          border-top: 1px solid #313244;
          font-size: 0.78rem;
          color: #6c7086;
        }}
      </style>
    </head>
    <body>
      <header>
        <h1>🔮 Autómata LR(0)</h1>
        <span>YAPar – Generador de Analizadores Sintácticos</span>
      </header>
      <div id="network"></div>
      <div id="legend">
        Estado inicial resaltado en gris oscuro · Aristas: transiciones por símbolo · Arrastra para reposicionar
      </div>
      <script>
        const nodes = new vis.DataSet({nodes_js});
        const edges = new vis.DataSet({edges_js});
        const container = document.getElementById('network');
        const data = {{ nodes, edges }};
        const options = {{
          nodes: {{
            shape: 'box',
            font: {{ face: 'Courier New', color: '#cdd6f4', size: 12 }},
            borderWidth: 1.5,
          }},
          edges: {{
            arrows: 'to',
            color: {{ color: '#89b4fa', highlight: '#cba6f7' }},
            font: {{ color: '#a6e3a1', size: 11, face: 'Helvetica' }},
            smooth: {{ type: 'curvedCW', roundness: 0.15 }},
          }},
          physics: {{
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{ gravitationalConstant: -50, springLength: 200 }},
            stabilization: {{ iterations: 200 }},
          }},
          interaction: {{ navigationButtons: true, keyboard: true }},
        }};
        new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return output_path
