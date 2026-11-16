"""Guards Python 3.9+ compatibility from a newer interpreter.

Python 3.12 allows f"{x['a']}" style nesting of the SAME quote character (f"{', '.join(f'{r['n']}')}"),
which is a SyntaxError on 3.9-3.11. We run on whatever the grader has, so we forbid it here.
Also parses every file against the 3.9 grammar.
"""
import ast
import io
import sys
import tokenize
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [p for p in ROOT.rglob("*.py") if ".venv" not in p.parts and "raw" not in p.parts]


def nested_same_quote(path):
    """Yield (line, text) wherever a string inside an f-string's {} reuses the f-string's own quote."""
    stack = []  # (quote char, is_triple) of the f-strings we are inside
    toks = tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf8")).readline)
    for t in toks:
        if t.type == tokenize.FSTRING_START:
            q = t.string[-1]
            if stack and not stack[-1][1] and stack[-1][0] == q:
                yield t.start[0], t.line.strip()
            stack.append((q, t.string.endswith(q * 3)))
        elif t.type == tokenize.FSTRING_END:
            stack.pop()
        elif t.type == tokenize.STRING and stack and not stack[-1][1]:
            if t.string.lstrip("rRbBuU")[0] == stack[-1][0]:
                yield t.start[0], t.line.strip()


class Compat(unittest.TestCase):
    def test_parses_with_python39_grammar(self):
        for p in FILES:
            ast.parse(p.read_text(encoding="utf8"), filename=str(p), feature_version=(3, 9))

    @unittest.skipIf(sys.version_info < (3, 12), "only a 3.12+ interpreter can tokenise this")
    def test_no_nested_same_quote_fstrings(self):
        bad = [(p.name, ln, txt) for p in FILES for ln, txt in nested_same_quote(p)]
        self.assertEqual(bad, [], "f-string reuses its own quote: breaks Python < 3.12")


if __name__ == "__main__":
    unittest.main()
