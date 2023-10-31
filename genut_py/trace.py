import sys
import dataclasses


@dataclasses.dataclass
class FuncTrace:
    filename: str
    line_start: int
    line_end: int
    coverage: int = 0

    def update(self, frame):
        if self.filename != frame.f_code.co_filename:
            return
        if self.line_start <= frame.f_lineno and frame.f_lineno < self.line_end:
            self.coverage |= 1 << frame.f_lasti


class Tracer:
    _index = 0
    func_traces: dict[int, FuncTrace] = {}

    @classmethod
    def register(cls, filename, line_start, line_end) -> int:
        if len(cls.func_traces) == 0:
            sys.settrace(cls.trace)

        cls._index += 1
        cls.func_traces[cls._index] = FuncTrace(filename, line_start, line_end)
        return cls._index

    @classmethod
    def get_coverage(cls, index):
        return cls.func_traces[index].coverage

    @classmethod
    def delete(cls, index):
        del cls.func_traces[index]

        if len(cls.func_traces) == 0:
            sys.settrace(None)

    @classmethod
    def trace(cls, frame, event, arg):
        frame.f_trace_lines = True
        frame.f_trace_opcodes = True
        if event == "opcode":
            for func_trace in cls.func_traces.values():
                func_trace.update(frame)
        return cls.trace
