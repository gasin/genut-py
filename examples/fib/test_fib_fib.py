from fib import fib


class TestFib:
    def test_fib_0(self):
        n = 2

        actual = fib(n)
        expected = 1

        assert actual == expected


    def test_fib_1(self):
        n = 1

        actual = fib(n)
        expected = 1

        assert actual == expected


    def test_fib_2(self):
        n = 3

        actual = fib(n)
        expected = 2

        assert actual == expected


