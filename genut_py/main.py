import atexit
import inspect
import os
import trace
import copy
import genut_py


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


def obj_to_dict(obj):
    if type(obj) is dict:
        res = {}
        for k, v in obj.items():
            res[k] = obj_to_dict(v)
        return res
    elif type(obj) is list:
        return [obj_to_dict(item) for item in obj]
    else:
        return obj


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for k, v in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict(
            [
                (key, todict(value, classkey))
                for key, value in obj.__dict__.items()
                if not callable(value) and not key.startswith("_")
            ]
        )
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


class GenUT:
    global_log = {}

    def __init__(self, f):
        self.f = f

        atexit.register(self.output_unit_test)

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
        for key, (arg_dict, return_value, modified_args) in self.global_log.items():
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
                output += f"        actual = {camel_to_snake(self.clsname)}.{self.funcname}({arg_names_str})\n"
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
        if key not in self.global_log:
            self.global_log[key] = (callargs_pre, return_value, modified_args)

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
