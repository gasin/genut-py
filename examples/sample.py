from genut_py import MyLogger


@MyLogger
def f(a: int, b: int):
    c = a + b
    return c


@MyLogger
def g(a: int, b: int):
    if a == 0:
        return 0
    return a - b


@MyLogger
def ho_ho(x):
    if x == 0:
        return g(0, 1)
    else:
        return g(1, 1)


class User:
    def __repr__(self):
        return f"User(name={self.name.__repr__()}, age={self.age.__repr__()})"

    name: str = "John"
    age: int = 19

    @MyLogger
    def check_age2(self):
        if self.age >= 20:
            return "method_ok"
        else:
            return "method_no"


@MyLogger
def check_age(user: User) -> str:
    if user.age >= 20:
        return "ok"
    else:
        return "no"


def main():
    f(1, 2)
    g(2, 2)
    g(0, 2)
    f(2, 2)
    ho_ho(0)
    ho_ho(1)
    user = User()
    check_age(user)
    user.age = 50
    check_age(user)
    user.check_age2()
    user2 = User()
    user2.check_age2()


if __name__ == "__main__":
    main()
