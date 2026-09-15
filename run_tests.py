"""Test runner. pytest is not installable in this container, so a minimal
compatible shim is installed only when the real package is absent.

The runner exists to make execution provable. It prints the number of tests
collected, executed, passed, failed and skipped, and exits non-zero if ZERO
tests ran. A suite that silently collects nothing is the failure mode this
guards against: it looks exactly like a suite that passed.
"""
from __future__ import annotations
import importlib, inspect, sys, tempfile, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _install_shim():
    """Install the shim ALWAYS, even when real pytest is present.

    This runner resolves fixtures by looking for markers the shim sets. Real
    pytest's @fixture leaves no such marker, so deferring to it makes every
    fixture-taking test fail with KeyError. The first version of this runner
    installed the shim only when pytest was missing, which worked in the
    container where pytest cannot be installed and broke on every machine that
    had it. Found by running the suite on a machine with pytest, 2026-09-14.

    If you want a real pytest run, invoke pytest directly:  pytest -v
    The test files are ordinary pytest files and work fine that way; you just
    lose this runner's three-way exit codes.
    """
    import types
    m = types.ModuleType("pytest")

    class Skipped(Exception):
        pass

    def fixture(func=None, **kw):
        def wrap(f):
            f.__is_fixture__ = True
            f.__fixture_scope__ = kw.get("scope", "function")
            return f
        return wrap(func) if func else wrap

    class _Mark:
        def skipif(self, cond, reason=""):
            def deco(f):
                f.__skip_if__ = (bool(cond), reason)
                return f
            deco.__skip_if__ = (bool(cond), reason)
            return deco

    def skip(reason=""):
        raise Skipped(reason)

    class _Raises:
        def __init__(self, exc): self.exc = exc
        def __enter__(self): return self
        def __exit__(self, t, v, tb):
            if t is None:
                raise AssertionError(f"expected {self.exc.__name__}, nothing raised")
            return issubclass(t, self.exc)

    m.fixture = fixture
    m.mark = _Mark()
    m.skip = skip
    m.raises = lambda exc: _Raises(exc)
    m.Skipped = Skipped
    sys.modules["pytest"] = m
    return "shim (installed unconditionally)"


def main(modnames=("test_adherence", "test_minibson")):
    kind = _install_shim()
    import pytest
    Skipped = getattr(pytest, "Skipped", None) or type("S", (Exception,), {})
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE / "sema"))

    collected = executed = passed = skipped = 0
    failures = []

    for modname in modnames:
        try:
            mod = importlib.import_module(modname)
        except Exception:
            failures.append((modname, "<import>", traceback.format_exc()))
            continue

        fixtures = {n: f for n, f in vars(mod).items()
                    if callable(f) and getattr(f, "__is_fixture__", False)}
        cache: dict = {}
        mark = getattr(mod, "pytestmark", None)
        mod_skip = getattr(mark, "__skip_if__", (False, ""))

        def resolve(name, tmp):
            if name == "tmp_path":
                return tmp
            if name not in fixtures:
                raise KeyError(f"no fixture named {name!r}")
            if getattr(fixtures[name], "__fixture_scope__", "function") == "session":
                if name not in cache:
                    cache[name] = fixtures[name]()
                return cache[name]
            return fixtures[name]()

        tests = [(n, f) for n, f in sorted(vars(mod).items())
                 if n.startswith("test_") and callable(f) and not getattr(f, "__is_fixture__", False)]
        collected += len(tests)

        for name, fn in tests:
            if mod_skip[0] or getattr(fn, "__skip_if__", (False, ""))[0]:
                skipped += 1
                continue
            executed += 1
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                try:
                    kwargs = {p: resolve(p, tmp) for p in inspect.signature(fn).parameters}
                    fn(**kwargs)
                    passed += 1
                except Skipped:
                    # the test called pytest.skip(); `passed` was never incremented
                    executed -= 1; skipped += 1
                except Exception:
                    failures.append((modname, name, traceback.format_exc()))

    for mod, name, tb in failures:
        print(f"\nFAIL {mod}::{name}\n{tb}")
    print(f"\nrunner={kind}  collected={collected}  executed={executed}  "
          f"passed={passed}  failed={len(failures)}  skipped={skipped}")

    if collected == 0 or executed == 0:
        print("ERROR: zero tests executed. An empty suite is not a passing suite.")
        return 2
    if failures:
        return 1
    if skipped:
        print(f"INCOMPLETE: {skipped} of {collected} tests were skipped and did not run.\n"
              f"            The {passed} that ran passed and verify their own components, but\n"
              f"            the pipeline is unverified. Stage the raw data (see VERIFY.md) and\n"
              f"            rerun: the gate is exit 0, meaning failed=0 AND skipped=0.")
        return 3
    return 0


def _self_check_empty(d: Path) -> int:
    """Prove the runner distinguishes 'all passed' from 'nothing ran'.

    Point it at a directory holding a module with no test functions; it must
    report zero executed and exit 2.
    """
    sys.path.insert(0, str(d))
    mods = [f.stem for f in sorted(Path(d).glob("test_*.py"))]
    return main(tuple(mods))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--self-check-empty":
        sys.exit(_self_check_empty(Path(sys.argv[2])))
    sys.exit(main())
