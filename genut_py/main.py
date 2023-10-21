import trace
import atexit
import inspect
import functools
import genut_py
import os

class MyLogger:

    def __init__(self, f):
        self.f = f
        self.cache = {}
        functools.update_wrapper(self, f)

        atexit.register(self.generate_unit_tests)

        codes, self.start_line = inspect.getsourcelines(self.f)
        self.end_line = self.start_line + len(codes)
        self.filename = inspect.getsourcefile(self.f)
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

    def generate_unit_tests(self):
        print(f"Class Test{self.snake_to_camel(self.f.__name__)}")
        for k, v in self.log.items():
            print(k)
            print(v)
    
    def __call__(self, *args, **keywords):

        tracer = trace.Trace(ignoredirs=[os.path.dirname(inspect.getfile(genut_py)),
                                         os.path.dirname(inspect.getfile(trace))])
        return_value = tracer.runfunc(self.f, *args, *keywords)
        result = tracer.results()
        target_lines = []
        for filename, line in result.counts.keys():
            if self.filename == filename and self.start_line <= line and line < self.end_line:
                target_lines.append(line)
        
        key = tuple(sorted(target_lines))
        if key not in self.log:
            self.log[key] = inspect.getcallargs(self.f, *args, *keywords)

        return return_value
    