![GitHub](https://img.shields.io/github/license/gasin/genut-py)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/genut-py)

# genut-py

genut-py is a semi-automatic unit test generator for Python

## Description

Unit tests are crucial in software development.

However, writing unit tests is a laborious task and it often requires more efforts than implementing a new feature.

Before writing unit tests, we often know that our implementation certainly works correctly by executing a program with some actual inputs and observing its outputs.

Our program utilizes the execution to generate unit tests.

By adding decorators to target functions or methods, some inputs are selected from the execution based on its coverage, and then, unit tests in pytest format are generated automatically.

The generated tests is relatively easy to interpret as the inputs are "actual" data.

| | manual | semi-automatic | automatic |
| ---- | ---- | ---- | ---- |
| methods | hand-craft | retrieve from execution | fuzz, smt-solver |
| tools | | genut-py | UnitTestBot, Pynguin |
| interpretability | high | medium | low |
| developper's burden | high | low | low |
| coverage | low | medium | high |

## Example

### Generate Unit Tests of Functions
```python
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
```
In default settings, the script below will be generated as `compare_test_class.py` under `.genut` directory by running the script above.
```python
from ..examples.function import compare


class TestCompare:
    def test_compare_0():
        x = 0
        y = 0

        actual = compare(x,y)
        expected = 0

        assert actual == expected

    def test_compare_1():
        x = 0
        y = 1

        actual = compare(x,y)
        expected = -1

        assert actual == expected

    def test_compare_2():
        x = 1
        y = 0

        actual = compare(x,y)
        expected = 1

        assert actual == expected
```

### Generate Unit Tests of Methods
```python
from genut_py import GenUT


class User:
    def __repr__(self):
        return f"User(name={self.name.__repr__()}, age={self.age.__repr__()})"

    def __init__(self, name, age):
        self.name = name
        self.age = age

    @GenUT
    def is_adult(self):
        if self.age >= 20:
            return f"{self.name} is adult"
        return f"{self.name} is child"


user = User(name="John", age=19)
user.is_adult()
user2 = User(name="Tom", age=25)
user2.is_adult()
```
In default settings, the script below will be generated as `user_is_adult_test_class.py` under `.genut` directory by running the script above.
```python
from ..examples.method import User


class TestUserIsAdult:
    def test_user_is_adult_0():
        user = User(name="John", age=19)

        actual = user.is_adult()
        expected = "John is child"

        assert actual == expected

    def test_user_is_adult_1():
        user = User(name="Tom", age=25)

        actual = user.is_adult()
        expected = "Tom is adult"

        assert actual == expected
```

## Getting Started

### Installation
```bash
pip install genut-py
```
