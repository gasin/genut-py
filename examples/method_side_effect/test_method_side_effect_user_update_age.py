from method_side_effect import User


class TestUserUpdateAge:
    def test_user_update_age_0(self):
        user = User(name='John', age=19)
        age = 20

        actual = user.update_age(age)
        expected = 20

        assert actual == expected
        assert user == User(name='John', age=20)


    def test_user_update_age_1(self):
        user = User(name='John', age=20)
        age = 20

        actual = user.update_age(age)
        expected = 20

        assert actual == expected


