"""
Tests unitarios básicos para YAPar.
Ejecutar con: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parsing.yalp_lexer import YalpLexer
from parsing.yalp_parser import parse_yalp, Grammar, Production
from grammar.first_follow import compute_first, compute_follow, EOF_MARKER
from grammar.lr0_builder import build_lr0_automaton, augment_grammar
from grammar.lr0_items import LR0Item
from slr.slr_table import build_slr_table
from evaluator.string_evaluator import StringEvaluator


# ---------------------------------------------------------------------------
# Fixtures: gramática aritmética simple
# ---------------------------------------------------------------------------

ARITHMETIC_YALP = os.path.join(
    os.path.dirname(__file__), "..", "examples", "arithmetic.yalp"
)


def get_grammar() -> Grammar:
    return parse_yalp(ARITHMETIC_YALP)


# ---------------------------------------------------------------------------
# Tests del lexer .yalp
# ---------------------------------------------------------------------------

def test_yalp_lexer_tokens():
    text = "%token ID PLUS\nIGNORE WS\n%%\nexpr:\n    ID\n    ;"
    lexer = YalpLexer(text)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert "PERCENT_TOKEN" in types
    assert "UPPER_ID" in types
    assert "IGNORE" in types
    assert "SEPARATOR" in types
    assert "LOWER_ID" in types
    assert "COLON" in types
    assert "SEMICOLON" in types
    assert "EOF" in types
    print("  ✓ test_yalp_lexer_tokens")


def test_yalp_lexer_comments():
    text = "/* esto es un comentario */ %token ID\n%%\nexpr:\n    ID\n    ;"
    lexer = YalpLexer(text)
    tokens = lexer.tokenize()
    # Los comentarios no deben generar tokens
    types = [t.type for t in tokens if t.type != "EOF"]
    assert "PERCENT_TOKEN" in types
    assert len([t for t in types if t == "UPPER_ID"]) == 2  # ID in %token and ID in prod
    print("  ✓ test_yalp_lexer_comments")


# ---------------------------------------------------------------------------
# Tests del parser .yalp
# ---------------------------------------------------------------------------

def test_parse_grammar_structure():
    grammar = get_grammar()
    assert grammar.start_symbol == "expr"
    assert "ID" in grammar.terminals
    assert "PLUS" in grammar.terminals
    assert "TIMES" in grammar.terminals
    assert "expr" in grammar.non_terminals
    assert "term" in grammar.non_terminals
    assert "factor" in grammar.non_terminals
    assert "WS" in grammar.ignored
    print("  ✓ test_parse_grammar_structure")


def test_parse_productions_count():
    grammar = get_grammar()
    # expr → expr PLUS term | term        (2)
    # term → term TIMES factor | factor   (2)
    # factor → LPAREN expr RPAREN | ID    (2)
    assert len(grammar.productions) == 6
    print("  ✓ test_parse_productions_count")


# ---------------------------------------------------------------------------
# Tests de FIRST y FOLLOW
# ---------------------------------------------------------------------------

def test_first_terminals():
    grammar = get_grammar()
    aug = augment_grammar(grammar)
    first = compute_first(aug)
    # FIRST de un terminal es él mismo
    assert first["ID"] == {"ID"}
    assert first["PLUS"] == {"PLUS"}
    print("  ✓ test_first_terminals")


def test_first_nonterminals():
    grammar = get_grammar()
    aug = augment_grammar(grammar)
    first = compute_first(aug)
    # FIRST(expr) = FIRST(term) = FIRST(factor) = {ID, LPAREN}
    assert "ID" in first["expr"]
    assert "LPAREN" in first["expr"]
    assert "ID" in first["factor"]
    assert "LPAREN" in first["factor"]
    print("  ✓ test_first_nonterminals")


def test_follow_start_symbol():
    grammar = get_grammar()
    aug = augment_grammar(grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    # FOLLOW(expr) debe contener $
    assert EOF_MARKER in follow["expr"]
    assert "PLUS" in follow["term"] or "TIMES" in follow["term"]
    print("  ✓ test_follow_start_symbol")


# ---------------------------------------------------------------------------
# Tests del autómata LR(0)
# ---------------------------------------------------------------------------

def test_lr0_automaton_states():
    grammar = get_grammar()
    automaton = build_lr0_automaton(grammar)
    # La gramática aritmética tiene 12 estados en LR(0)
    assert len(automaton.states) > 0
    assert automaton.initial_state is not None
    assert automaton.initial_state.id == 0
    print(f"  ✓ test_lr0_automaton_states ({len(automaton.states)} estados)")


def test_lr0_initial_item():
    grammar = get_grammar()
    automaton = build_lr0_automaton(grammar)
    initial = automaton.initial_state
    # El estado inicial debe contener S' → · expr
    items_str = [str(i) for i in initial.items]
    assert any("S'" in s for s in items_str), f"No S' item found: {items_str}"
    print("  ✓ test_lr0_initial_item")


# ---------------------------------------------------------------------------
# Tests de la tabla SLR(1)
# ---------------------------------------------------------------------------

def test_slr_table_no_conflicts():
    grammar = get_grammar()
    automaton = build_lr0_automaton(grammar)
    table = build_slr_table(automaton)
    if table.has_conflicts():
        print(f"  ⚠ Conflictos: {table.conflicts}")
    assert not table.has_conflicts(), f"Conflictos inesperados: {table.conflicts}"
    print("  ✓ test_slr_table_no_conflicts")


def test_slr_table_has_accept():
    grammar = get_grammar()
    automaton = build_lr0_automaton(grammar)
    table = build_slr_table(automaton)
    # Debe haber exactamente un estado con 'accept' en $
    accept_states = [
        s for s, actions in table.action.items()
        if actions.get("$") == "accept"
    ]
    assert len(accept_states) == 1, f"Accept states: {accept_states}"
    print(f"  ✓ test_slr_table_has_accept (estado {accept_states[0]})")


# ---------------------------------------------------------------------------
# Tests del evaluador
# ---------------------------------------------------------------------------

def _get_evaluator():
    grammar = get_grammar()
    automaton = build_lr0_automaton(grammar)
    table = build_slr_table(automaton)
    aug = automaton._grammar
    return StringEvaluator(table, aug), grammar.ignored


def test_evaluator_accepts_valid():
    evaluator, ignored = _get_evaluator()
    result = evaluator.evaluate(["ID", "PLUS", "ID"], ignored=ignored, trace=False)
    assert result.accepted, f"Debería aceptar: {result.message}"
    print("  ✓ test_evaluator_accepts_valid (ID PLUS ID)")


def test_evaluator_accepts_complex():
    evaluator, ignored = _get_evaluator()
    tokens = ["LPAREN", "ID", "PLUS", "ID", "RPAREN", "TIMES", "ID"]
    result = evaluator.evaluate(tokens, ignored=ignored, trace=False)
    assert result.accepted, f"Debería aceptar: {result.message}"
    print("  ✓ test_evaluator_accepts_complex ((ID PLUS ID) TIMES ID)")


def test_evaluator_rejects_invalid():
    evaluator, ignored = _get_evaluator()
    result = evaluator.evaluate(["PLUS", "ID"], ignored=ignored, trace=False)
    assert not result.accepted, "Debería rechazar PLUS ID"
    print("  ✓ test_evaluator_rejects_invalid (PLUS ID)")


def test_evaluator_rejects_incomplete():
    evaluator, ignored = _get_evaluator()
    result = evaluator.evaluate(["ID", "PLUS"], ignored=ignored, trace=False)
    assert not result.accepted, "Debería rechazar ID PLUS (incompleto)"
    print("  ✓ test_evaluator_rejects_incomplete (ID PLUS)")


# ---------------------------------------------------------------------------
# Runner manual (sin pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*50)
    print("YAPar – Tests Unitarios")
    print("="*50)
    tests = [
        test_yalp_lexer_tokens,
        test_yalp_lexer_comments,
        test_parse_grammar_structure,
        test_parse_productions_count,
        test_first_terminals,
        test_first_nonterminals,
        test_follow_start_symbol,
        test_lr0_automaton_states,
        test_lr0_initial_item,
        test_slr_table_no_conflicts,
        test_slr_table_has_accept,
        test_evaluator_accepts_valid,
        test_evaluator_accepts_complex,
        test_evaluator_rejects_invalid,
        test_evaluator_rejects_incomplete,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
    print(f"\n  Resultado: {passed} passed, {failed} failed")
