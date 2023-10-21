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


def main():
    f(1, 2)
    g(2, 2)
    g(0, 2)
    f(2, 2)
    ho_ho(0)
    ho_ho(1)


if __name__ == "__main__":
    main()
