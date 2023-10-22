from genut_py import GenUT


@GenUT
def compare(x, y):
    if x < y:
        return -1
    if x == y:
        return 0
    if x > y:
        return 1
    assert False


for i in range(10):
    for j in range(10):
        compare(i, j)
