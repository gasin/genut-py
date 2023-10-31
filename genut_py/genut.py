import atexit
import copy
import inspect
import logging
import os
import trace

import genut_py
from genut_py.format import camel_to_snake, snake_to_camel
from genut_py.state import State

logger = logging.getLogger(__name__)


def spawn_tracer():
    """spawn_tracer"""
    return trace.Trace(
        trace=0,
        ignoredirs=[
            os.path.dirname(inspect.getfile(genut_py)),
            os.path.dirname(inspect.getfile(trace)),
        ],
    )


def todict(obj):
    if isinstance(obj, dict):
        data = {}
        for k, v in obj.items():
            data[k] = todict(v)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict(
            [
                (key, todict(value))
                for key, value in obj.__dict__.items()
                if not callable(value) and not key.startswith("_")
            ]
        )
        return data
    else:
        return obj


class _GenUT:
    state: State = State()
    max_samples = None

    def __init__(self, f, use_cache=False, max_samples=None):
        self.f = f
        _GenUT.max_samples = max_samples

        atexit.register(self.output_unit_test)
        atexit.register(self.state.save)

        _GenUT.state.load(use_cache)

        codes, self.start_line = inspect.getsourcelines(self.f)
        self.end_line = self.start_line + len(codes)
        self.filename = inspect.getsourcefile(self.f)
        self.funcname = self.f.__name__
        self.clsname = None

    def output_unit_test(self):
        clsfncname = self.funcname
        if self.clsname is not None:
            clsfncname = camel_to_snake(self.clsname) + "_" + self.funcname

        import_str = "." + os.path.relpath(self.filename, os.getcwd() + "/.genut").replace(
            "../", "."
        ).removesuffix(".py").replace("/", ".")
        output = ""
        if self.clsname is None:
            output += f"from {import_str} import {self.funcname}\n"
        else:
            output += f"from {import_str} import {self.clsname}\n"
        output += "\n\n"

        output += f"class Test{snake_to_camel(clsfncname)}:\n"
        index = 0
        for arg_dict, return_value, modified_args in _GenUT.state.get_items(
            self.filename, self.funcname
        ):
            output += f"    def test_{clsfncname}_{index}():\n"
            for arg_name, arg_value in arg_dict.items():
                if self.clsname is not None and arg_name == "self":
                    output += f"        {camel_to_snake(self.clsname)} = {arg_value.__repr__()}\n"
                    continue
                output += f"        {arg_name} = {arg_value.__repr__()}\n"
            arg_names_str = ",".join(
                k for k in arg_dict.keys() if self.clsname is None or k != "self"
            )
            output += "\n"
            if self.clsname is None:
                output += f"        actual = {self.funcname}({arg_names_str})\n"
            else:
                method_call_str = (
                    f"{camel_to_snake(self.clsname)}.{self.funcname}({arg_names_str})\n"
                )
                output += f"        actual = {method_call_str}"
            output += f"        expected = {return_value.__repr__()}\n"
            output += "\n"
            output += "        assert actual == expected\n"
            for arg_name, value in modified_args.items():
                if self.clsname is not None and arg_name == "self":
                    arg_name = camel_to_snake(self.clsname)
                output += f"        assert {arg_name} == {value}\n"
            output += "\n\n"

            index += 1

        os.makedirs(".genut", exist_ok=True)
        with open(f".genut/{clsfncname}_test_class.py", "w") as output_file:
            output_file.write(output)

    def _get_coverage(self, tracer):
        result = tracer.results()
        target_lines = []
        for filename, line in result.counts.keys():
            if self.filename == filename and self.start_line <= line and line < self.end_line:
                target_lines.append(line)

        return tuple(sorted(target_lines))

    def _update_state(self, tracer, callargs_pre, return_value, callargs_post):
        modified_args = {}
        for key in callargs_pre.keys():
            if todict(callargs_pre[key]) != todict(callargs_post[key]):
                modified_args[key] = copy.deepcopy(callargs_post[key])

        coverage = self._get_coverage(tracer)
        _GenUT.state.update(
            self.filename, self.funcname, coverage, callargs_pre, return_value, modified_args
        )

    def __call__(self, *args, **keywords):
        if _GenUT.max_samples is not None:
            if _GenUT.max_samples == 0:
                return self.f(*args, *keywords)
            _GenUT.max_samples -= 1

        tracer = spawn_tracer()
        callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, *args, *keywords))
        return_value = tracer.runfunc(self.f, *args, *keywords)
        callargs_post = inspect.getcallargs(self.f, *args, *keywords)

        self._update_state(tracer, callargs_pre, return_value, callargs_post)

        return return_value

    def __get__(self, instance, owner):
        self.clsname = owner.__name__

        def wrapper(*args, **keywords):
            if _GenUT.max_samples is not None:
                if _GenUT.max_samples == 0:
                    return self.f(instance, *args, *keywords)
                _GenUT.max_samples -= 1
            tracer = spawn_tracer()
            callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, instance, *args, *keywords))
            return_value = tracer.runfunc(self.f, instance, *args, *keywords)
            callargs_post = inspect.getcallargs(self.f, instance, *args, *keywords)

            self._update_state(tracer, callargs_pre, return_value, callargs_post)

            return return_value

        return wrapper


def GenUT(function=None, use_cache=False, max_samples=None):
    """Decorator to generate unit tests from execution

    Args:
        use_cache: if True, restart from previous execution
        max_samples: if number of samples reaches max_samples, stop tracing

    Examples:
        decorator of function

        >>> @GenUT
        >>> def add(a, b):
        >>>     return a + b

        decorator of method

        >>> class User:
        >>>     name: str
        >>>
        >>>     @GenUT(use_cache=True, max_samples=True)
        >>>     def call_name(self):
        >>>         print(self.name)
    """

    if function:
        return _GenUT(function)

    def wrapper(function):
        return _GenUT(function, use_cache=use_cache, max_samples=max_samples)

    return wrapper
