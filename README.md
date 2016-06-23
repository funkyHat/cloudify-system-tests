This Proof of Concept demonstrates several of the features of pytest, as well as the `config` framework component which geokala developed, implemented as a pytest fixture.

To run the tests install the package:

```bash
pip install -e .
```

And then run the test suite:

```bash
py.test
```


Failing tests can be found in `cloudify_tester/suites/test_tests/failing_tests.py`. To run those:

```bash
py.test cloudify_tester/suites/test_tests/failing_tests.py
```

pytest has several features to aid in debugging failing tests. My favourite is the `--pdb` option:

```bash
$ py.test cloudify_tester/suites/test_tests/failing_tests.py
=========================================== test session starts ============================================
platform darwin -- Python 2.7.11, pytest-2.9.2, py-1.4.31, pluggy-0.3.1
rootdir: /Users/matt/Projects/cloudify/cloudify-tests-poc/cloudify_tester, inifile: pytest.ini
collected 1 items

cloudify_tester/suites/test_tests/failing_tests.py F

================================================= FAILURES =================================================
________________________________________________ test_fail _________________________________________________

    def test_fail():
        """Demonstrating pytest's advanced assert reporting.
        Note that it shows the evaluated value in the report"""
        value = False
>       assert value is True
E       assert False is True

cloudify_tester/suites/test_tests/failing_tests.py:12: AssertionError
========================================= 1 failed in 0.01 seconds =========================================
(cfy-testspoc)E1% py.test --pdb cloudify_tester/suites/test_tests/failing_tests.py
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
(Pdb) p value
False
(Pdb) c


========================================= 1 failed in 8.82 seconds =========================================
```

## External Suites
The `external_example` dir demonstrates that the `cloudify_tester` package can be referenced externally (e.g. from test suites which live in their respective components' repos in git).
