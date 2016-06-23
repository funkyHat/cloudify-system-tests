def test_the_teardown_stuff_first(fake_manager):
    pass


# NOTE! I am relying on the order of execution of these tests, and deliberately
# sharing state between them, because I'm demonstrating test teardown. For real
# tests this should never be done!

def test_the_teardown_stuff_second(fake_manager):
    assert fake_manager.fin_called is True
