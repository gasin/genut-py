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


@GenUT(line_trace=False)
def compare(x, y):
    if x < y or x == y:
        return 0
    if x > y:
        return 1
    assert False


for i in range(10):
    for j in range(10):
        compare(i, j)
```
```python
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
```

## Getting Started

### Installation
```bash
pip install genut-py
```

## Development

### Format & Lint
```bash
# under /
make check
```

### Generate Docs
```bash
# under /docs
poetry run make html
```
