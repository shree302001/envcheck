import unittest

from envcheck.parser import parse


class ParserTests(unittest.TestCase):
    def values(self, text):
        return {e.key: e.value for e in parse(text).entries}

    def test_basic_and_comments(self):
        self.assertEqual(self.values("# hi\nA=1\n\nB = two\n"), {"A": "1", "B": "two"})

    def test_export_prefix(self):
        self.assertEqual(self.values("export A=1"), {"A": "1"})

    def test_quotes_and_inline_comments(self):
        got = self.values('A="x # y"\nB=\'q\'\nC=plain # note\nD="a\\"b"')
        self.assertEqual(got, {"A": "x # y", "B": "q", "C": "plain", "D": 'a"b'})

    def test_hash_without_space_is_kept(self):
        self.assertEqual(self.values("URL=http://x/#frag"), {"URL": "http://x/#frag"})

    def test_empty_value(self):
        self.assertEqual(self.values("A="), {"A": ""})

    def test_errors(self):
        r = parse('nonsense\n1BAD=x\nQ="open\nOK=1')
        self.assertEqual([n for n, _ in r.errors], [1, 2, 3])
        self.assertEqual(r.keys(), {"OK"})


if __name__ == "__main__":
    unittest.main()
