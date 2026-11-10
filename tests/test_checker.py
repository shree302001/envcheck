import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from envcheck.checker import compare
from envcheck.cli import main
from envcheck.parser import parse


class CompareTests(unittest.TestCase):
    def test_report(self):
        example = parse("A=x\nB=y\nC=\n")
        env = parse("A=1\nA=2\nB=\nZ=9\n")
        r = compare(env, example)
        self.assertEqual(r.missing, ["C"])
        self.assertEqual(r.extra, ["Z"])
        self.assertEqual(r.empty, ["B"])
        self.assertEqual(r.duplicates, [("A", [1, 2])])

    def test_optional_stays_optional(self):
        r = compare(parse("C=\n"), parse("C=\n"))
        self.assertEqual(r.problems(), 0)

    def test_strict_counts_extra(self):
        r = compare(parse("A=1\nZ=1"), parse("A=x"))
        self.assertEqual(r.problems(), 0)
        self.assertEqual(r.problems(strict=True), 1)


class CliTests(unittest.TestCase):
    def run_cli(self, env, example, *extra):
        with tempfile.TemporaryDirectory() as d:
            ep, xp = os.path.join(d, ".env"), os.path.join(d, ".env.example")
            for p, t in ((ep, env), (xp, example)):
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(t)
            out = StringIO()
            with redirect_stdout(out):
                code = main([ep, "-e", xp, *extra])
            return code, out.getvalue()

    def test_ok(self):
        code, out = self.run_cli("A=1", "A=x")
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_missing_fails(self):
        code, out = self.run_cli("", "A=x")
        self.assertEqual(code, 1)
        self.assertIn("missing    A", out)

    def test_json(self):
        code, out = self.run_cli("", "A=x", "--format", "json")
        data = json.loads(out)
        self.assertEqual((code, data["ok"], data["missing"]), (1, False, ["A"]))

    def test_missing_file(self):
        self.assertEqual(main(["nope.env", "-e", "nope.example"]), 2)


class FixTests(unittest.TestCase):
    def _run(self, env_text, example_text, *flags):
        with tempfile.TemporaryDirectory() as d:
            env, ex = os.path.join(d, ".env"), os.path.join(d, ".env.example")
            with open(env, "w", encoding="utf-8", newline="") as fh:
                fh.write(env_text)
            with open(ex, "w", encoding="utf-8") as fh:
                fh.write(example_text)
            out = StringIO()
            with redirect_stdout(out):
                code = main([env, "-e", ex, *flags])
            with open(env, encoding="utf-8", newline="") as fh:
                return code, out.getvalue(), fh.read()

    def test_fix_appends_missing(self):
        code, out, text = self._run("A=1", 'A=x\nexport B="two words"\nC=\n', "--fix")
        self.assertEqual(text, 'A=1\nB="two words"\nC=\n')
        self.assertIn("added      B", out)
        self.assertEqual(code, 0)

    def test_fix_leaves_complete_file_alone(self):
        _, out, text = self._run("A=1\n", "A=x\n", "--fix")
        self.assertEqual(text, "A=1\n")
        self.assertNotIn("added", out)

    def test_without_fix_file_untouched(self):
        code, _, text = self._run("A=1\n", "A=x\nB=y\n")
        self.assertEqual(text, "A=1\n")
        self.assertEqual(code, 1)

    def test_fix_json_lists_added(self):
        _, out, _ = self._run("", "A=x\n", "--fix", "--format", "json")
        self.assertEqual(json.loads(out)["added"], ["A"])

    def test_ignore_hides_findings(self):
        code, out, _ = self._run("A=1\nZ=1\nZ=2\n", "A=x\nB=y\n",
                                 "--ignore", "B", "--ignore", "Z", "--strict")
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_ignore_not_added_by_fix(self):
        _, _, text = self._run("A=1\n", "A=x\nB=y\nC=z\n", "--fix", "--ignore", "B")
        self.assertEqual(text, "A=1\nC=z\n")


class MultiFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_cli(self, *args):
        buf = StringIO()
        with redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def test_text_headers_and_exit_code(self):
        ex = self.write("ex", "A=x\n")
        good = self.write("good.env", "A=1\n")
        bad = self.write("bad.env", "")
        code, out = self.run_cli(good, bad, "-e", ex)
        self.assertEqual(code, 1)
        self.assertIn(f"==> {good} <==", out)
        self.assertIn(f"==> {bad} <==", out)
        self.assertIn("missing    A", out)

    def test_json_lists_files(self):
        ex = self.write("ex", "A=x\n")
        good = self.write("good.env", "A=1\n")
        bad = self.write("bad.env", "")
        code, out = self.run_cli(good, bad, "-e", ex, "--format", "json")
        data = json.loads(out)
        self.assertFalse(data["ok"])
        self.assertEqual([f["file"] for f in data["files"]], [good, bad])
        self.assertEqual([f["ok"] for f in data["files"]], [True, False])

    def test_fix_applies_to_each_file(self):
        ex = self.write("ex", "A=x\n")
        a = self.write("a.env", "")
        b = self.write("b.env", "")
        self.run_cli(a, b, "-e", ex, "--fix")
        for path in (a, b):
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "A=x\n")


class TypeHintTests(unittest.TestCase):
    EXAMPLE = (
        "# type: int\nPORT=8080\n"
        "DEBUG=false  # type: bool\n"
        "RATE=1.5 # type: float\n"
        "URL=https://x.io # type: url\n"
        "NAME=app\n"
    )

    def report(self, env_text, **kw):
        return compare(parse(env_text), parse(self.EXAMPLE), **kw)

    def test_valid_values_pass(self):
        r = self.report("PORT=1\nDEBUG=Yes\nRATE=2\nURL=http://a.b\nNAME=z\n")
        self.assertEqual(r.invalid, [])

    def test_invalid_values_reported(self):
        r = self.report("PORT=abc\nDEBUG=maybe\nRATE=x\nURL=nope\nNAME=z\n")
        self.assertEqual([k for k, _, _ in r.invalid], ["PORT", "DEBUG", "RATE", "URL"])
        self.assertEqual(r.problems(), 4)

    def test_blank_is_empty_not_invalid(self):
        r = self.report("PORT=\nDEBUG=true\nRATE=1\nURL=http://a.b\nNAME=z\n")
        self.assertEqual(r.invalid, [])
        self.assertEqual(r.empty, ["PORT"])

    def test_hint_does_not_leak_across_blank_line(self):
        ex = parse("# type: int\n\nA=x\n")
        self.assertEqual(ex.first("A").type_hint, "")

    def test_ignore_skips_check(self):
        r = self.report("PORT=abc\nDEBUG=true\nRATE=1\nURL=http://a.b\nNAME=z\n", ignore=["PORT"])
        self.assertEqual(r.invalid, [])


if __name__ == "__main__":
    unittest.main()
