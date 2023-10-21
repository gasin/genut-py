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
