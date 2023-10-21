import atexit
import inspect
import os
import trace

import genut_py


class MyLogger:
    def __init__(self, f):
        self.f = f

        atexit.register(self.output_unit_test)

        codes, self.start_line = inspect.getsourcelines(self.f)
        self.end_line = self.start_line + len(codes)
        self.filename = inspect.getsourcefile(self.f)
        self.funcname = self.f.__name__
        self.log = {}

    def snake_to_camel(self, snake_str: str) -> str:
        is_head = True
        camel_str = ""
        for i in range(len(snake_str)):
            if is_head and snake_str[i].islower():
                camel_str += snake_str[i].upper()
                is_head = False
                continue
            if snake_str[i] == "_":
                is_head = True
                continue
            camel_str += snake_str[i]

        return camel_str

    def output_unit_test(self):
        output = f"class Test{self.snake_to_camel(self.funcname)}:\n"
        for i, (arg_dict, return_value) in enumerate(self.log.values()):
            output += f"    def test_{self.funcname}_{i}():\n"
            for arg_name, arg_value in arg_dict.items():
                output += f"        {arg_name} = {arg_value.__repr__()}\n"
            arg_names_str = ",".join(arg_dict.keys())
            output += "\n"
            output += f"        actual = {self.funcname}({arg_names_str})\n"
            output += f"        expected = {return_value.__repr__()}\n"
            output += "\n"
            output += "        assert actual == expected"
            output += "\n\n"

        os.makedirs(".genut", exist_ok=True)
        with open(f".genut/{self.funcname}_test_class.py", "w") as output_file:
            output_file.write(output)

    def __call__(self, *args, **keywords):
        tracer = trace.Trace(
            trace=0,
            ignoredirs=[
                os.path.dirname(inspect.getfile(genut_py)),
                os.path.dirname(inspect.getfile(trace)),
            ],
        )
        return_value = tracer.runfunc(self.f, *args, *keywords)
        result = tracer.results()
        target_lines = []
        for filename, line in result.counts.keys():
            if self.filename == filename and self.start_line <= line and line < self.end_line:
                target_lines.append(line)

        key = tuple(sorted(target_lines))
        if key not in self.log:
            self.log[key] = (inspect.getcallargs(self.f, *args, *keywords), return_value)

        return return_value
