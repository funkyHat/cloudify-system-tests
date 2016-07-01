# pytest Proof of Concept
This Proof of Concept demonstrates several of the features of pytest, as well as the `config` framework component which geokala developed, implemented as a pytest fixture.

To run the tests install the package:

```bash
pip install -e .
```

And then run the test suite:

```bash
py.test cloudify_tester external_example bdd_example
```

py.test will run everything it finds under . by default, so if you have set up a virtualenv within the repo running `py.test` by itself is probably not what you want.

The main test suites and framework are in the `cloudify_tester` dir.

Test framework components are pytest plugins, and can be loaded in the standard way by external test suites (see below)

Tests can be be tagged and then excluded or run based on those tags:

```bash
# Run all tests which aren't tagged `slow`
py.test bdd_example -k-slow

# Run only `slow` tests
py.test -m-slow
```

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

This allows test suites to easily make use of any components from the main framework simply and directly as long as it is installed (note `external_example/conftest.py` referencing the config helper from the main framework).

## BDD
The `bdd_example` dir demonstrates the `pytest-bdd` package in action (http://pytest-bdd.readthedocs.io/en/latest/)

In order to run these tests successfully you'll need to set up a suitable `test_config.yaml`, something like:

```yaml
real: yes
fake: no
cloudify_version: 3.4rc1
#platform: aws
platform_options:
  manager_blueprint: aws-ec2-manager-blueprint.yaml
  nodecellar_blueprint: aws-ec2-blueprint.yaml
  manager_blueprint_inputs:
    aws_access_key_id: <key>
    aws_secret_access_key: <secret>
    image_id: ami-91feb7fb
    manager_security_group_name: <yourname> test bdd manager sg
    agent_security_group_name: <yourname> test bdd agent sg
    manager_keypair_name: <yourname> test bdd manager key
    agent_keypair_name: <yourname> test bdd agent key
```

(also note that I would propose we adopt geokala's updated config parser which supports namespaces, rather than using my outdated clone as-is)

An option is added to py.test by this suite. If you run `py.test --bdd_reporting bdd_example -k-slow` it will print the steps as they are run (note that this is a very rough PoC of this feature and as such is not colour coded or quite as pretty as behave's output. It could easily be improved upon (see `bdd_example/conftest.py`).

While BDD allows a much more declarative style of test, which would suit a lot of cloudify's system tests, I think that some tests are clearer written as plain functions, and pytest-bdd would allow us to re-use the same plugins & fixtures across all of the tests.

---

Note that if you just run `py.test` in the root of the repo it will run all of the tests, including those in the "external" suites (and possibly anything in your virtualenv).

---

# Thoughts

We agree on a lot: the current test framework is overly complicated. Many layers of inheritance make it hard to see what's going on, and a lot of them aren't really necessary.
To improve on this we split out functionality which is not directly part of the tests into helpers which can be imported (or loaded as a plugin in pytest) and used explicitly rather than being implicitly available as a result of a deep inheritance structure.
