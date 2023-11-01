import sys
import dataclasses


@dataclasses.dataclass
class FuncTrace:
    filename: str
    line_start: int
    line_end: int
    is_line: bool
    coverage: int = 0

    def update(self, frame):
        if self.filename != frame.f_code.co_filename:
            return
        if self.line_start <= frame.f_lineno and frame.f_lineno < self.line_end:
            if self.is_line:
                self.coverage |= 1 << frame.f_lineno
            else:
                self.coverage |= 1 << frame.f_lasti


class Tracer:
    _index = 0
    func_traces: dict[int, FuncTrace] = {}
    is_opcode_trace = False
    is_line_trace = False

    @classmethod
    def register(cls, filename, line_start, line_end, is_line) -> int:
        if len(cls.func_traces) == 0:
            sys.settrace(cls.trace)

        cls._index += 1
        cls.func_traces[cls._index] = FuncTrace(filename, line_start, line_end, is_line)
        if is_line:
            cls.is_line_trace = True
        else:
            cls.is_opcode_trace = True
        return cls._index

    @classmethod
    def get_coverage(cls, index):
        return cls.func_traces[index].coverage

    @classmethod
    def delete(cls, index):
        del cls.func_traces[index]

        if len(cls.func_traces) == 0:
            sys.settrace(None)

        cls.is_line_trace = any(ft.is_line for ft in cls.func_traces.values())
        cls.is_opcode_trace = any(not ft.is_line for ft in cls.func_traces.values())

    @classmethod
    def trace(cls, frame, event, arg):
        frame.f_trace_lines = cls.is_line_trace
        frame.f_trace_opcodes = cls.is_opcode_trace
        if event == "line":
            for func_trace in cls.func_traces.values():
                if func_trace.is_line:
                    func_trace.update(frame)
        if event == "opcode":
            for func_trace in cls.func_traces.values():
                if not func_trace.is_line:
                    func_trace.update(frame)
        return cls.trace
