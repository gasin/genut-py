from function_side_effect import append_list


class TestAppendList:
    def test_append_list_0(self):
        lst = [1, 2]
        x = -5

        actual = append_list(lst,x)
        expected = None

        assert actual == expected


    def test_append_list_1(self):
        lst = [1, 2]
        x = 0

        actual = append_list(lst,x)
        expected = None

        assert actual == expected
        assert lst == [1, 2, 0]


