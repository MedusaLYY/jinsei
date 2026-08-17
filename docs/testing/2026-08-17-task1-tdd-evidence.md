# Task 1 TDD and Verification Evidence

**Date:** 2026-08-17

**Branch:** `feat/worldsim-v1`

**Commit order:** `7b02b2b` → `f61e5a3` → `f8f161d` → `8895906`

**Environment:** Windows, Python 3.14.5, pytest 8.4.2

This report preserves the command evidence for the Task 1 review fixes: the one-way NPC naming
obligation, oversized JSON integer handling, and growth-level bounds-before-arithmetic behavior.

## Original scaffold cycle provenance (7b02b2b)

The original scaffold red run was executed before production package files existed with this
command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_package.py tests\test_rules.py tests\test_cli.py -v
```

Its verbatim stdout was not retained in a versioned artifact. The contemporaneous task record says
that 10 tests failed because `overlord_worldsim` and `content/core/ruleset.json` did not yet exist.
That sentence is a summary, not a reconstructed or verbatim transcript. No invented output is
presented as original evidence.

## Review fixes (f61e5a3): fresh red

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

## Review fixes (f61e5a3): fresh green

The same command was rerun after the minimal fixes.

```text
.....                                                                    [100%]
5 passed in 0.34s
```

The library now raises `RulesetValidationError` without echoing unbounded integers, and both CLI
cases return exit status 2 without a traceback.

## Loader-owned integer limit (f61e5a3): fresh red

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

## Loader-owned integer limit (f61e5a3): fresh green

The loader now supplies a bounded `parse_int` callback that counts lexical digits before building an
integer and does not depend on the interpreter's global string-conversion setting.

Output from the same command:

```text
......                                                                   [100%]
6 passed in 0.44s
```

## Final verification for f61e5a3

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

## Bounded diagnostics and total byte limit (f8f161d): fresh red

The next quality review found that frozen-field mismatch diagnostics still rendered arbitrary JSON
values with `repr`, and that the loader read an entire file before applying any validation. Focused
library and subprocess tests were added first. The subprocess helper used
`PYTHONINTMAXSTRDIGITS=640`; the known frozen integer was 1,000 digits, below the loader's 4,300
digit lexical ceiling. A read probe also rejected any read other than exactly the 4 MiB limit plus
one byte.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules.py::test_large_frozen_integer_mismatch_has_bounded_typed_diagnostic tests\test_rules.py::test_large_string_mismatch_has_bounded_deterministic_diagnostic tests\test_rules.py::test_large_container_mismatch_has_bounded_deterministic_diagnostic tests\test_rules.py::test_ruleset_larger_than_loader_limit_is_rejected tests\test_rules.py::test_ruleset_loader_caps_its_file_read tests\test_cli.py::test_rules_command_handles_large_frozen_integer_diagnostic tests\test_cli.py::test_rules_command_rejects_ruleset_larger_than_loader_limit -q --tb=short
```

Output, captured before modifying production code:

```text
FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
_______ test_large_frozen_integer_mismatch_has_bounded_typed_diagnostic _______
tests\test_rules.py:365: in test_large_frozen_integer_mismatch_has_bounded_typed_diagnostic
    load_ruleset(path)
src\overlord_worldsim\rules.py:340: in load_ruleset
    _expect(document, field_path, expected)
src\overlord_worldsim\rules.py:423: in _expect
    raise RulesetValidationError(f"{dotted_path} must be {expected!r}; got {actual!r}")
                                                                           ^^^^^^^^^^
E   ValueError: Exceeds the limit (640 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit
_______ test_large_string_mismatch_has_bounded_deterministic_diagnostic _______
tests\test_rules.py:392: in test_large_string_mismatch_has_bounded_deterministic_diagnostic
    assert "string" in first_message
E   assert 'string' in "ruleset_id must be 'urn:overlord-worldsim:ruleset:core'; got 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'"
_____ test_large_container_mismatch_has_bounded_deterministic_diagnostic ______
tests\test_rules.py:414: in test_large_container_mismatch_has_bounded_deterministic_diagnostic
    assert "array" in first_message
E   assert 'array' in "start_modes must be [{'id': 'ordinary', 'level': 1}, {'id': 'heroic', 'level': 35}, {'id': 'legendary', 'level': 60},...one, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]"
______________ test_ruleset_larger_than_loader_limit_is_rejected ______________
src\overlord_worldsim\rules.py:310: in load_ruleset
    json.loads(
D:\Python3.14.5\Lib\json\__init__.py:365: in loads
    return cls(**kw).decode(s)
           ^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\json\decoder.py:345: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\json\decoder.py:363: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 4194306 (char 4194305)

The above exception was the direct cause of the following exception:
tests\test_rules.py:425: in test_ruleset_larger_than_loader_limit_is_rejected
    load_ruleset(path)
src\overlord_worldsim\rules.py:317: in load_ruleset
    raise RulesetValidationError(
E   overlord_worldsim.rules.RulesetValidationError: C:\Users\Medusa\AppData\Local\Temp\pytest-of-Medusa\pytest-355\test_ruleset_larger_than_loade0\oversized-ruleset.json: malformed JSON at line 1, column 4194306: Expecting value

During handling of the above exception, another exception occurred:
tests\test_rules.py:424: in test_ruleset_larger_than_loader_limit_is_rejected
    with pytest.raises(error_type, match=r"exceeds maximum size of 4194304 bytes"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: Regex pattern did not match.
E    Regex: 'exceeds maximum size of 4194304 bytes'
E    Input: 'C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-355\\test_ruleset_larger_than_loade0\\oversized-ruleset.json: malformed JSON at line 1, column 4194306: Expecting value'
___________________ test_ruleset_loader_caps_its_file_read ____________________
tests\test_rules.py:470: in test_ruleset_loader_caps_its_file_read
    load_ruleset(tmp_path / "read-probe.json")
src\overlord_worldsim\rules.py:299: in load_ruleset
    serialized = rules_path.read_text(encoding="utf-8")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python3.14.5\Lib\pathlib\__init__.py:787: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_rules.py:464: in open_probe
    assert mode == "rb"
E   AssertionError: assert 'r' == 'rb'
E
E     - rb
E     + r
_________ test_rules_command_handles_large_frozen_integer_diagnostic __________
tests\test_cli.py:139: in test_rules_command_handles_large_frozen_integer_diagnostic
    assert completed.returncode == 2
E   AssertionError: assert 1 == 2
E    +  where 1 = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...xceeds the limit (640 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit\n').returncode
_________ test_rules_command_rejects_ruleset_larger_than_loader_limit _________
tests\test_cli.py:156: in test_rules_command_rejects_ruleset_larger_than_loader_limit
    assert "exceeds maximum size of 4194304 bytes" in completed.stderr
E   AssertionError: assert 'exceeds maximum size of 4194304 bytes' in 'error: C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-355\\test_rules_command_rejects_rul0\\oversized-ruleset.json: malformed JSON at line 1, column 4194306: Expecting value\n'
E    +  where 'error: C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-355\\test_rules_command_rejects_rul0\\oversized-ruleset.json: malformed JSON at line 1, column 4194306: Expecting value\n' = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...\\test_rules_command_rejects_rul0\\oversized-ruleset.json: malformed JSON at line 1, column 4194306: Expecting value\n').stderr
=========================== short test summary info ===========================
FAILED tests/test_rules.py::test_large_frozen_integer_mismatch_has_bounded_typed_diagnostic
FAILED tests/test_rules.py::test_large_string_mismatch_has_bounded_deterministic_diagnostic
FAILED tests/test_rules.py::test_large_container_mismatch_has_bounded_deterministic_diagnostic
FAILED tests/test_rules.py::test_ruleset_larger_than_loader_limit_is_rejected
FAILED tests/test_rules.py::test_ruleset_loader_caps_its_file_read - Assertio...
FAILED tests/test_cli.py::test_rules_command_handles_large_frozen_integer_diagnostic
FAILED tests/test_cli.py::test_rules_command_rejects_ruleset_larger_than_loader_limit
7 failed in 0.63s
```

The failures isolate the two remaining causes: `_expect` directly formatted arbitrary parsed values,
and `Path.read_text` performed an uncapped read before UTF-8 and JSON validation.

## Bounded diagnostics and total byte limit (f8f161d): fresh green

The loader now reads at most 4 MiB plus one byte in binary mode, rejects excess input before UTF-8
decoding, and preserves strict UTF-8 errors for allowed-size files. Frozen-field errors use a typed
summary: safe small scalar values are shown, while large integers, strings, arrays, and objects are
represented by bounded metadata.

The exact red command was rerun after the implementation.

Output:

```text
.......                                                                  [100%]
7 passed in 0.37s
```

## Final verification after bounded-loader fixes (f8f161d)

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
collected 49 items

tests\test_cli.py .......                                                [ 14%]
tests\test_package.py .                                                  [ 16%]
tests\test_rules.py .........................................            [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.5-final-0 _______________

Name                                Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------------
src\overlord_worldsim\__main__.py      29      1      4      1    94%   41
src\overlord_worldsim\rules.py        209      6     94      4    97%   340-341, 425, 445, 447, 467
-------------------------------------------------------------------------------
TOTAL                                 241      7     98      5    96%

1 file skipped due to complete coverage.
Required test coverage of 95.0% reached. Total coverage: 96.46%
============================= 49 passed in 2.20s ==============================
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

## Unified bounded diagnostics (8895906): fresh red

Spec re-review found raw formatting outside `_expect`: public lookup arguments, duplicate JSON keys,
unknown keys, floating-point field paths, and duplicate damage phases. Behavioral tests were added
for all families plus CLI projections for a large string, container, and key. The public integer
tests set the interpreter digit guard to 640 around a 1,000-digit integer.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers tests\test_rules.py::test_public_lookup_large_integer_is_safe_under_python_digit_guard tests\test_rules.py::test_large_duplicate_damage_phase_has_bounded_diagnostic tests\test_rules.py::test_large_duplicate_json_key_has_bounded_diagnostic tests\test_rules.py::test_large_unknown_field_has_bounded_diagnostic tests\test_rules.py::test_large_floating_point_field_path_has_bounded_diagnostic tests\test_cli.py::test_rules_command_bounds_large_duplicate_phase_diagnostic tests\test_cli.py::test_rules_command_bounds_large_container_diagnostic tests\test_cli.py::test_rules_command_bounds_large_duplicate_key_diagnostic -q --tb=short
```

Output, captured before modifying production code:

```text
FFFFFFFFFFFFF.F                                                          [100%]
================================== FAILURES ===================================
_ test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-string] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   assert 10058 < 500
E    +  where 10058 = len("target level must be an integer from 1 through 100; got 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
_ test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-array] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   AssertionError: assert 60056 < 500
E    +  where 60056 = len('target level must be an integer from 1 through 100; got [None, None, None, None, None, None, None, None, None, None, ...one, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]')
_ test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-object] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   AssertionError: assert 118946 < 500
E    +  where 118946 = len('target level must be an integer from 1 through 100; got {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: Non...990: None, 9991: None, 9992: None, 9993: None, 9994: None, 9995: None, 9996: None, 9997: None, 9998: None, 9999: None}')
_ test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-string] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   AssertionError: assert 10020 < 500
E    +  where 10020 = len('unknown magic tier: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
_ test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-array] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   AssertionError: assert 60020 < 500
E    +  where 60020 = len('unknown magic tier: [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, ...one, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]')
_ test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-object] _
tests\test_rules.py:224: in test_public_lookup_diagnostics_bound_strings_and_containers
    assert len(message) < 500
E   AssertionError: assert 118910 < 500
E    +  where 118910 = len('unknown magic tier: {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: No...990: None, 9991: None, 9992: None, 9993: None, 9994: None, 9995: None, 9996: None, 9997: None, 9998: None, 9999: None}')
_ test_public_lookup_large_integer_is_safe_under_python_digit_guard[growth-cost] _
tests\test_rules.py:265: in test_public_lookup_large_integer_is_safe_under_python_digit_guard
    assert expected_context in message
E   AssertionError: assert 'target level must be from 1 through 100' in 'Exceeds the limit (640 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit'
_ test_public_lookup_large_integer_is_safe_under_python_digit_guard[magic-tier] _
tests\test_rules.py:265: in test_public_lookup_large_integer_is_safe_under_python_digit_guard
    assert expected_context in message
E   AssertionError: assert 'unknown magic tier' in 'Exceeds the limit (640 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit'
__________ test_large_duplicate_damage_phase_has_bounded_diagnostic ___________
tests\test_rules.py:317: in test_large_duplicate_damage_phase_has_bounded_diagnostic
    assert len(message) < 500
E   assert 10031 < 500
E    +  where 10031 = len("duplicate damage phase 'phase-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
____________ test_large_duplicate_json_key_has_bounded_diagnostic _____________
tests\test_rules.py:385: in test_large_duplicate_json_key_has_bounded_diagnostic
    assert len(message) < 500
E   assert 10160 < 500
E    +  where 10160 = len("C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-362\\test_large_duplicate_json_key_0\\large-duplica...kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk'")
_______________ test_large_unknown_field_has_bounded_diagnostic _______________
tests\test_rules.py:621: in test_large_unknown_field_has_bounded_diagnostic
    assert len(message) < 500
E   assert 10016 < 500
E    +  where 10016 = len("unknown field 'zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz...zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz'")
_________ test_large_floating_point_field_path_has_bounded_diagnostic _________
tests\test_rules.py:639: in test_large_floating_point_field_path_has_bounded_diagnostic
    assert len(message) < 500
E   AssertionError: assert 10081 < 500
E    +  where 10081 = len('effects.zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz...zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz contains a floating-point number; authoritative numbers must be integers')
_________ test_rules_command_bounds_large_duplicate_phase_diagnostic __________
tests\test_cli.py:175: in test_rules_command_bounds_large_duplicate_phase_diagnostic
    assert len(completed.stderr) < 500
E   assert 10039 < 500
E    +  where 10039 = len("error: duplicate damage phase 'phase-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n")
E    +    where "error: duplicate damage phase 'phase-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n" = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n").stderr
__________ test_rules_command_bounds_large_duplicate_key_diagnostic ___________
tests\test_cli.py:211: in test_rules_command_bounds_large_duplicate_key_diagnostic
    assert len(completed.stderr) < 500
E   assert 10168 < 500
E    +  where 10168 = len("error: C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-362\\test_rules_command_bounds_larg2\\large-...kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk'\n")
E    +    where "error: C:\\Users\\Medusa\\AppData\\Local\\Temp\\pytest-of-Medusa\\pytest-362\\test_rules_command_bounds_larg2\\large-...kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk'\n" = CompletedProcess(args=['C:\\AAA_OVERLORD\\.venv\\Scripts\\python.exe', '-m', 'overlord_worldsim', 'rules', '--path', '...kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk'\n").stderr
=========================== short test summary info ===========================
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-string]
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-array]
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[growth-cost-object]
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-string]
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-array]
FAILED tests/test_rules.py::test_public_lookup_diagnostics_bound_strings_and_containers[magic-tier-object]
FAILED tests/test_rules.py::test_public_lookup_large_integer_is_safe_under_python_digit_guard[growth-cost]
FAILED tests/test_rules.py::test_public_lookup_large_integer_is_safe_under_python_digit_guard[magic-tier]
FAILED tests/test_rules.py::test_large_duplicate_damage_phase_has_bounded_diagnostic
FAILED tests/test_rules.py::test_large_duplicate_json_key_has_bounded_diagnostic
FAILED tests/test_rules.py::test_large_unknown_field_has_bounded_diagnostic
FAILED tests/test_rules.py::test_large_floating_point_field_path_has_bounded_diagnostic
FAILED tests/test_cli.py::test_rules_command_bounds_large_duplicate_phase_diagnostic
FAILED tests/test_cli.py::test_rules_command_bounds_large_duplicate_key_diagnostic
14 failed, 1 passed in 1.05s
```

The CLI container test passed in the red run because the preceding `_expect` fix already bounded
that route. It remains as explicit subprocess coverage. All other new cases failed for the intended
raw-format or integer-conversion reason.

The same command after routing those diagnostics through the shared renderer produced:

```text
...............                                                          [100%]
15 passed in 0.81s
```

## Filesystem-path diagnostic (8895906): fresh red and green

A follow-up raw-format audit found that unreadable-file errors still echoed the supplied filesystem
path twice: directly and through `OSError`. A focused regression was added before changing that
boundary.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules.py::test_unreadable_large_ruleset_path_has_bounded_diagnostic -q --tb=short
```

Red output:

```text
F                                                                        [100%]
================================== FAILURES ===================================
__________ test_unreadable_large_ruleset_path_has_bounded_diagnostic __________
tests\test_rules.py:362: in test_unreadable_large_ruleset_path_has_bounded_diagnostic
    assert len(message) < 500
E   assert 20064 < 500
E    +  where 20064 = len("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.json'")
=========================== short test summary info ===========================
FAILED tests/test_rules.py::test_unreadable_large_ruleset_path_has_bounded_diagnostic
1 failed in 0.41s
```

The loader now reports a bounded filename-and-length descriptor and omits raw `OSError` text. The
path regression plus the full diagnostic group then produced:

```text
................                                                         [100%]
16 passed in 0.71s
```

## Final verification after unified diagnostic fixes (8895906)

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
collected 68 items

tests\test_cli.py ..........                                             [ 14%]
tests\test_package.py .                                                  [ 16%]
tests\test_rules.py .................................................... [ 92%]
.....                                                                    [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.5-final-0 _______________

Name                                Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------------
src\overlord_worldsim\__main__.py      29      1      4      1    94%   41
src\overlord_worldsim\rules.py        268      6    120      4    97%   407-408, 503, 613, 625, 642
-------------------------------------------------------------------------------
TOTAL                                 300      7    124      5    97%

1 file skipped due to complete coverage.
Required test coverage of 95.0% reached. Total coverage: 97.17%
============================= 68 passed in 5.98s ==============================
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

### Diff check

Command:

```powershell
git diff --check
```

Output: empty; exit status 0.
