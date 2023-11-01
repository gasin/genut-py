from function import compare


class TestCompare:
    def test_compare_0(self):
        x = 0
        y = 0

        actual = compare(x,y)
        expected = 0

        assert actual == expected


    def test_compare_1(self):
        x = 0
        y = 1

        actual = compare(x,y)
        expected = 0

        assert actual == expected


    def test_compare_2(self):
        x = 1
        y = 0

        actual = compare(x,y)
        expected = 1

        assert actual == expected


