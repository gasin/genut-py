from method import User


class TestUserIsAdult:
    def test_user_is_adult_0(self):
        user = User(name='John', age=19)

        actual = user.is_adult()
        expected = 'John is child'

        assert actual == expected


    def test_user_is_adult_1(self):
        user = User(name='Tom', age=25)

        actual = user.is_adult()
        expected = 'Tom is adult'

        assert actual == expected


