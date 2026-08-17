# Task 1 TDD and Verification Evidence

**Date:** 2026-08-17

**Branch:** `feat/worldsim-v1`

**Environment:** Windows, Python 3.14.5, pytest 8.4.2

This report preserves the command evidence for the Task 1 review fixes: the one-way NPC naming
obligation, oversized JSON integer handling, and growth-level bounds-before-arithmetic behavior.

## Original scaffold cycle provenance

The original scaffold red run was executed before production package files existed with this
command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_package.py tests\test_rules.py tests\test_cli.py -v
```

Its verbatim stdout was not retained in a versioned artifact. The contemporaneous task record says
that 10 tests failed because `overlord_worldsim` and `content/core/ruleset.json` did not yet exist.
That sentence is a summary, not a reconstructed or verbatim transcript. No invented output is
presented as original evidence.

## Review fixes: fresh red

The regression tests were added before modifying production code or the rules document.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules.py::test_naming_threshold_is_a_one_way_obligation tests\test_rules.py::test_decoder_integer_above_safe_digit_limit_fails_clearly tests\test_rules.py::test_growth_target_level_is_bounded_before_arithmetic tests\test_cli.py::test_rules_command_handles_decoder_integer_limit tests\test_cli.py::test_rules_command_handles_oversized_growth_target -q --tb=short
```

Output, captured before the fixes:

```text
FFFFF                                                                    [100%]
================================== FAILURES ===================================
________________ test_naming_threshold_is_a_one_way_obligation ________________
tests\test_rules.py:169: in test_naming_threshold_is_a_one_way_obligation
    assert scarcity["all_npcs_at_or_above_level_must_be_named"] == 45
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'all_npcs_at_or_above_level_must_be_named'
__________ test_decoder_integer_above_safe_digit_limit_fails_clearly __________
tests\test_rules.py:293: in test_decoder_integer_above_safe_digit_limit_fails_clearly
    load_ruleset(path)
src\overlord_worldsim\rules.py:303: in load_ruleset
    json.loads(serialized, object_pairs_hook=_object_with_unique_keys),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\json\__init__.py:365: in loads
    return cls(**kw).decode(s)
           ^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\json\decoder.py:345: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\json\decoder.py:361: in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
E   ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit
____________ test_growth_target_level_is_bounded_before_arithmetic ____________
tests\test_rules.py:309: in test_growth_target_level_is_bounded_before_arithmetic
    load_ruleset(path)
src\overlord_worldsim\rules.py:322: in load_ruleset
    growth_costs = _validate_growth_costs(document)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\overlord_worldsim\rules.py:460: in _validate_growth_costs
    f"{entry_path}.cost must be {expected_cost} for target level "
                                ^^^^^^^^^^^^^^^
E   ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit
______________ test_rules_command_handles_decoder_integer_limit _______________
tests\test_cli.py:81: in test_rules_command_handles_decoder_integer_limit
    assert completed.returncode == 2
E   AssertionError: assert 1 == 2
E    +  where 1 = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...igits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit\n').returncode
_____________ test_rules_command_handles_oversized_growth_target ______________
tests\test_cli.py:99: in test_rules_command_handles_oversized_growth_target
    assert completed.returncode == 2
E   AssertionError: assert 1 == 2
E    +  where 1 = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...ceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit\n').returncode
=========================== short test summary info ===========================
FAILED tests/test_rules.py::test_naming_threshold_is_a_one_way_obligation - K...
FAILED tests/test_rules.py::test_decoder_integer_above_safe_digit_limit_fails_clearly
FAILED tests/test_rules.py::test_growth_target_level_is_bounded_before_arithmetic
FAILED tests/test_cli.py::test_rules_command_handles_decoder_integer_limit - ...
FAILED tests/test_cli.py::test_rules_command_handles_oversized_growth_target
5 failed in 0.50s
```

The failures confirmed three root causes:

- the frozen JSON and validator used a bidirectionally misleading `named_npc_minimum_level` key;
- `json.loads` can raise plain `ValueError` for Python's integer digit safety limit;
- growth target bounds were not checked before exponentiation and integer formatting.

## Review fixes: fresh green

The same command was rerun after the minimal fixes.

```text
.....                                                                    [100%]
5 passed in 0.34s
```

The library now raises `RulesetValidationError` without echoing unbounded integers, and both CLI
cases return exit status 2 without a traceback.

## Loader-owned integer limit: fresh red

Independent review then tested with CPython's mutable global guard disabled. Two new oversized-cost
tests were added at the same time; they already passed because the first fix had removed raw cost
interpolation. The loader-owned-limit tests failed, proving the remaining environment dependency.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules.py::test_decoder_integer_above_safe_digit_limit_fails_clearly tests\test_rules.py::test_growth_target_level_is_bounded_before_arithmetic tests\test_rules.py::test_oversized_growth_cost_is_not_echoed_in_diagnostic tests\test_cli.py::test_rules_command_handles_decoder_integer_limit tests\test_cli.py::test_rules_command_handles_oversized_growth_target tests\test_cli.py::test_rules_command_does_not_echo_oversized_growth_cost -q --tb=short
```

Output, captured with the tests setting `PYTHONINTMAXSTRDIGITS=0`:

```text
F..F..                                                                   [100%]
================================== FAILURES ===================================
__________ test_decoder_integer_above_safe_digit_limit_fails_clearly __________
tests\test_rules.py:297: in test_decoder_integer_above_safe_digit_limit_fails_clearly
    load_ruleset(path)
src\overlord_worldsim\rules.py:324: in load_ruleset
    _validate_no_unknown_fields(document)
src\overlord_worldsim\rules.py:388: in _validate_no_unknown_fields
    value: JsonValue = document if not parent_path else _at(document, parent_path)
                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^
src\overlord_worldsim\rules.py:372: in _at
    raise RulesetValidationError(f"missing required field {'.'.join(traversed)!r}")
E   overlord_worldsim.rules.RulesetValidationError: missing required field 'compatibility'

During handling of the above exception, another exception occurred:
tests\test_rules.py:296: in test_decoder_integer_above_safe_digit_limit_fails_clearly
    with pytest.raises(error_type, match="JSON integer exceeds the safe digit limit"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: Regex pattern did not match.
E    Regex: 'JSON integer exceeds the safe digit limit'
E    Input: "missing required field 'compatibility'"
______________ test_rules_command_handles_decoder_integer_limit _______________
tests\test_cli.py:84: in test_rules_command_handles_decoder_integer_limit
    assert "JSON integer exceeds the safe digit limit" in completed.stderr
E   assert 'JSON integer exceeds the safe digit limit' in "error: missing required field 'compatibility'\n"
E    +  where "error: missing required field 'compatibility'\n" = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...andles_dec0\\too-many-digits.json'], returncode=2, stdout='', stderr="error: missing required field 'compatibility'\n").stderr
=========================== short test summary info ===========================
FAILED tests/test_rules.py::test_decoder_integer_above_safe_digit_limit_fails_clearly
FAILED tests/test_cli.py::test_rules_command_handles_decoder_integer_limit - ...
2 failed, 4 passed in 0.51s
```

## Loader-owned integer limit: fresh green

The loader now supplies a bounded `parse_int` callback that counts lexical digits before building an
integer and does not depend on the interpreter's global string-conversion setting.

Output from the same command:

```text
......                                                                   [100%]
6 passed in 0.44s
```

## Final verification

### Pytest and coverage

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

Output:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\AAA_OVERLORD
configfile: pyproject.toml
testpaths: tests
plugins: hypothesis-6.165.10, cov-6.3.0
collected 42 items

tests\test_cli.py .....                                                  [ 11%]
tests\test_package.py .                                                  [ 14%]
tests\test_rules.py ....................................                 [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.5-final-0 _______________

Name                                Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------------
src\overlord_worldsim\__main__.py      29      1      4      1    94%   41
src\overlord_worldsim\rules.py        184      5     78      3    97%   327-328, 412, 431, 437
-------------------------------------------------------------------------------
TOTAL                                 216      6     82      4    97%

1 file skipped due to complete coverage.
Required test coverage of 95.0% reached. Total coverage: 96.64%
============================= 42 passed in 1.74s ==============================
```

### Ruff lint

Command and output:

```powershell
> .\.venv\Scripts\python.exe -m ruff check .
All checks passed!
```

### Ruff format

Command and output:

```powershell
> .\.venv\Scripts\python.exe -m ruff format --check .
12 files already formatted
```

### Mypy

Command and output:

```powershell
> .\.venv\Scripts\python.exe -m mypy src tests
Success: no issues found in 6 source files
```
