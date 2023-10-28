import atexit
import copy
import inspect
import logging
import os
import pickle
import trace

import genut_py

logger = logging.getLogger(__name__)


def snake_to_camel(snake_str: str) -> str:
    def word_to_camel(s: str):
        if s == "":
            return ""
        return s[0].upper() + s[1:]

    return "".join(map(word_to_camel, snake_str.split("_")))


def camel_to_snake(camel_str: str) -> str:
    snake_str = ""
    for i, c in enumerate(camel_str):
        if i > 0 and c.isupper():
            snake_str += "_"
        snake_str += c.lower()

    return snake_str


def spawn_tracer():
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
    global_log = {}
    _is_cache_imported = False
    _is_cache_exported = False

    CACHE_FILE = ".genut/cache.pkl"

    def __init__(self, f, use_cache=False):
        self.f = f

        atexit.register(self.output_unit_test)
        atexit.register(self.export_global_log)

        if use_cache and not _GenUT._is_cache_imported and os.path.isfile(_GenUT.CACHE_FILE):
            _GenUT._is_cache_imported = True
            try:
                with open(".genut/cache.pkl", "rb") as f:
                    _GenUT.global_log = pickle.load(f)
                logger.info("cache is loaded")
            except AttributeError:
                logger.warning("failed to load cache")

        codes, self.start_line = inspect.getsourcelines(self.f)
        self.end_line = self.start_line + len(codes)
        self.filename = inspect.getsourcefile(self.f)
        self.funcname = self.f.__name__
        self.clsname = None

    def export_global_log(self):
        if _GenUT._is_cache_exported:
            return
        _GenUT._is_cache_exported = True

        os.makedirs(".genut", exist_ok=True)
        with open(_GenUT.CACHE_FILE, "wb") as f:
            pickle.dump(_GenUT.global_log, f)

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
        for key, (arg_dict, return_value, modified_args) in _GenUT.global_log.items():
            if (self.filename, self.funcname) != (key[0], key[1]):
                continue
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

    def _update_global_log(self, tracer, callargs_pre, return_value, callargs_post):
        modified_args = {}
        for key in callargs_pre.keys():
            if todict(callargs_pre[key]) != todict(callargs_post[key]):
                modified_args[key] = copy.deepcopy(callargs_post[key])

        coverage = self._get_coverage(tracer)
        key = (self.filename, self.funcname, coverage)
        if key not in _GenUT.global_log:
            _GenUT.global_log[key] = (callargs_pre, return_value, modified_args)

    def __call__(self, *args, **keywords):
        tracer = spawn_tracer()
        callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, *args, *keywords))
        return_value = tracer.runfunc(self.f, *args, *keywords)
        callargs_post = inspect.getcallargs(self.f, *args, *keywords)

        self._update_global_log(tracer, callargs_pre, return_value, callargs_post)

        return return_value

    def __get__(self, instance, owner):
        self.clsname = owner.__name__

        def wrapper(*args, **keywords):
            tracer = spawn_tracer()
            callargs_pre = copy.deepcopy(inspect.getcallargs(self.f, instance, *args, *keywords))
            return_value = tracer.runfunc(self.f, instance, *args, *keywords)
            callargs_post = inspect.getcallargs(self.f, instance, *args, *keywords)

            self._update_global_log(tracer, callargs_pre, return_value, callargs_post)

            return return_value

        return wrapper


def GenUT(function=None, use_cache=False):
    if function:
        return _GenUT(function)

    def wrapper(function):
        return _GenUT(function, use_cache=use_cache)

    return wrapper
