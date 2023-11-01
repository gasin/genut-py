from genut_py import GenUT


@GenUT
def append_list(lst, x):
    if x < 0:
        return
    lst.append(x)


lst = [1, 2]
for i in range(-5, 5):
    append_list(lst, i)
