# pytest Proof of Concept
This Proof of Concept demonstrates several of the features of pytest, as well as the `config` framework component which geokala developed, implemented as a pytest fixture.

To run the tests install the package:

```bash
pip install -e .
```

And then run the test suite:

```bash
py.test
```

The main test suites and framework are in the `cloudify_tester` dir.

Test framework components are pytest plugins, and can be loaded in the standard way by external test suites (see below)

Failing tests can be found in `cloudify_tester/suites/test_tests/failing_tests.py`. To run those:

```bash
py.test cloudify_tester/suites/test_tests/failing_tests.py
```

## Debugging
pytest has several features to aid in debugging failing tests. My favourite is the `--pdb` option:

```bash
$ py.test --pdb cloudify_tester/suites/test_tests/failing_tests.py
=========================================== test session starts ============================================
platform darwin -- Python 2.7.11, pytest-2.9.2, py-1.4.31, pluggy-0.3.1
rootdir: /Users/matt/Projects/cloudify/cloudify-tests-poc/cloudify_tester, inifile: pytest.ini
collected 1 items

cloudify_tester/suites/test_tests/failing_tests.py F
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> traceback >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def test_fail():
        """Demonstrating pytest's advanced assert reporting.
        Note that it shows the evaluated value in the report"""
        value = False
>       assert value is True
E       assert False is True

cloudify_tester/suites/test_tests/failing_tests.py:12: AssertionError
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> entering PDB >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> /Users/matt/Projects/cloudify/cloudify-tests-poc/cloudify_tester/suites/test_tests/failing_tests.py(12)test_fail()
-> assert value is True
(Pdb) ?

Documented commands (type help <topic>):
========================================
EOF    bt         cont      enable  jump  pp       run      unt
a      c          continue  exit    l     q        s        until
alias  cl         d         h       list  quit     step     up
args   clear      debug     help    n     r        tbreak   w
b      commands   disable   ignore  next  restart  u        whatis
break  condition  down      j       p     return   unalias  where

Miscellaneous help topics:
==========================
exec  pdb

Undocumented commands:
======================
retval  rv

(Pdb) p value
False
(Pdb) c


========================================= 1 failed in 8.82 seconds =========================================
```

## External Suites
The `external_example` dir demonstrates that the `cloudify_tester` package can be referenced externally (e.g. from test suites which live in their respective components' repos in git).

## BDD
The `bdd_example` dir demonstrates the `pytest-bdd` package in action (http://pytest-bdd.readthedocs.io/en/latest/)

While BDD allows a much more declarative style of test, which would suit a lot of cloudify's system tests, I think that some tests are clearer written as plain functions, and pytest-bdd would allow us to re-use the same plugins & fixtures across all of the tests.

---

Note that if you just run `py.test` in the root of the repo it will run all of the tests, including those in the "external" suites.
