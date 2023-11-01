import atexit
import copy
import inspect
import logging

from genut_py.format import camel_to_snake, snake_to_camel
from genut_py.state import State
from genut_py.trace import Tracer

logger = logging.getLogger(__name__)


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
        data = {
            key: todict(value)
            for key, value in obj.__dict__.items()
            if not callable(value) and not key.startswith("_")
        }
        return data
    elif hasattr(obj, "__slots__"):
        data = {
            slot: todict(getattr(obj, slot))
            for slot in obj.__slots__
            if not slot.startswith("_") and not callable(getattr(obj, slot))
        }
        return data
    else:
        return obj


class _GenUT:
    state: State = State()
    tracer: Tracer = Tracer()

    def __init__(self, f, use_cache=False, max_samples=None, line_trace=True):
        self.f = f
        self.max_samples = max_samples

        atexit.register(self.output_unit_test)
        atexit.register(self.state.save)

        _GenUT.state.load(use_cache)

        codes, self.start_line = inspect.getsourcelines(self.f)
        self.end_line = self.start_line + len(codes)
        self.filename = inspect.getsourcefile(self.f)
        self.funcname = self.f.__name__
        self.clsname = None
        self.is_line = line_trace

    def output_unit_test(self):
        clsfncname = self.funcname
        if self.clsname is not None:
            clsfncname = camel_to_snake(self.clsname) + "_" + self.funcname

        filename = self.filename.split("/")[-1].removesuffix(".py")
        test_path = "/".join(self.filename.split("/")[:-1]) + f"/test_{filename}_{clsfncname}.py"
        output = ""
        if self.clsname is None:
            output += f"from {filename} import {self.funcname}\n"
        else:
            output += f"from {filename} import {self.clsname}\n"
        output += "\n\n"

        output += f"class Test{snake_to_camel(clsfncname)}:\n"
        index = 0
        for arg_dict, return_value, modified_args in _GenUT.state.get_items(
            self.filename, self.funcname
        ):
            output += f"    def test_{clsfncname}_{index}(self):\n"
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

        with open(test_path, "w") as output_file:
            output_file.write(output)

    def _update_state(self, trace_id, callargs_pre, return_value, callargs_post):
        modified_args = {}
        for key in callargs_pre.keys():
            if todict(callargs_pre[key]) != todict(callargs_post[key]):
                modified_args[key] = copy.deepcopy(callargs_post[key])

        coverage = _GenUT.tracer.get_coverage(trace_id)

        _GenUT.state.update(
            self.filename, self.funcname, coverage, callargs_pre, return_value, modified_args
        )

    def __call__(self, *args, **keywords):
        if self.max_samples is not None:
            if self.max_samples == 0:
                return self.f(*args, *keywords)
            self.max_samples -= 1

        trace_id = _GenUT.tracer.register(
            self.filename, self.start_line, self.end_line, self.is_line
        )
        callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, *args, *keywords))
        return_value = self.f(*args, *keywords)
        callargs_post = inspect.getcallargs(self.f, *args, *keywords)

        self._update_state(trace_id, callargs_pre, return_value, callargs_post)

        _GenUT.tracer.delete(trace_id)

        return return_value

    def __get__(self, instance, owner):
        self.clsname = owner.__name__

        def wrapper(*args, **keywords):
            if self.max_samples is not None:
                if self.max_samples == 0:
                    return self.f(instance, *args, *keywords)
                self.max_samples -= 1
            trace_id = _GenUT.tracer.register(
                self.filename, self.start_line, self.end_line, self.is_line
            )
            callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, instance, *args, *keywords))
            return_value = self.f(instance, *args, *keywords)
            callargs_post = inspect.getcallargs(self.f, instance, *args, *keywords)

            self._update_state(trace_id, callargs_pre, return_value, callargs_post)

            _GenUT.tracer.delete(trace_id)

            return return_value

        return wrapper


def GenUT(function=None, use_cache=False, max_samples=None, line_trace=True):
    """Decorator to generate unit tests from execution

    Args:
        use_cache: if True, restart from previous execution
        max_samples: if number of samples reaches max_samples, stop tracing
        line_trace: use line trace instead of bytecode trace

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
        return _GenUT(
            function, use_cache=use_cache, max_samples=max_samples, line_trace=line_trace
        )

    return wrapper
