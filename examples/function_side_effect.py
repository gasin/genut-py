from genut_py import GenUT


@GenUT
def append_list(l, x):
    if x < 0:
        return
    l.append(x)


l = [1, 2]
for i in range(-5, 5):
    append_list(l, i)
