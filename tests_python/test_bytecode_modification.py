import sys
from io import StringIO

from _pydevd_frame_eval.pydevd_modify_bytecode import insert_code

TRACE_MESSAGE = "Trace called"

def tracing():
    print(TRACE_MESSAGE)


def bar(a, b):
    return a + b


if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


@unittest.skip("The test requires Python 3.6")
class TestInsertCode:
    lines_separator = "---Line tested---"

    def check_insert_every_line(self, func_to_modify, func_to_insert, number_of_lines):
        first_line = func_to_modify.__code__.co_firstlineno + 1
        last_line = first_line + number_of_lines
        for i in range(first_line, last_line):
            self.check_insert_to_line(func_to_modify, func_to_insert, i)
            print(self.lines_separator)

    def check_insert_to_line(self, func_to_modify, func_to_insert, line_number):
        code_orig = func_to_modify.__code__
        code_to_insert = func_to_insert.__code__
        success, result = insert_code(code_orig, code_to_insert, line_number)
        exec(result)
        output = sys.stdout.getvalue().strip().split(self.lines_separator)[-1]
        self.assertTrue(TRACE_MESSAGE in output)

    def test_assignment(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                a = 1
                b = 2
                c = 3

            self.check_insert_every_line(original, tracing, 3)

        finally:
            sys.stdout = self.original_stdout

    def test_for_loop(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                n = 3
                sum = 0
                for i in range(n):
                    sum += i
                return sum

            self.check_insert_every_line(original, tracing, 5)

        finally:
            sys.stdout = self.original_stdout

    def test_if(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                if True:
                    a = 1
                else:
                    a = 0
                print(a)

            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 2)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 5)

        finally:
            sys.stdout = self.original_stdout

    def test_else(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                if False:
                    a = 1
                else:
                    a = 0
                print(a)

            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 4)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 5)

        finally:
            sys.stdout = self.original_stdout

    def test_for_else(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                sum = 0
                for i in range(3):
                    sum += i
                else:
                    print(sum)

            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 1)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 3)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 5)

        finally:
            sys.stdout = self.original_stdout

    def test_elif(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                a = 5
                b = 0
                if a < 0:
                    print("a < 0")
                elif a < 3:
                    print("a < 3")
                else:
                    print("a >= 3")
                    b = a
                return b

            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 1)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 2)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 8)
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 9)

        finally:
            sys.stdout = self.original_stdout

    def test_call_other_function(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def original():
                a = 1
                b = 3
                c = bar(a, b)
                return c

            self.check_insert_every_line(original, tracing, 4)

        finally:
            sys.stdout = self.original_stdout

    def test_class_method(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            class A(object):
                @staticmethod
                def foo():
                    print("i'm in foo")

            original = A.foo
            self.check_insert_to_line(original, tracing, original.__code__.co_firstlineno + 2)

        finally:
            sys.stdout = self.original_stdout

    def test_offset_overflow(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def foo():
                a = 1  # breakpoint
                b = 2
                c = 3
                a1 = 1 if a > 1 else 2
                a2 = 1 if a > 1 else 2
                a3 = 1 if a > 1 else 2
                a4 = 1 if a > 1 else 2
                a5 = 1 if a > 1 else 2
                a6 = 1 if a > 1 else 2
                a7 = 1 if a > 1 else 2
                a8 = 1 if a > 1 else 2
                a9 = 1 if a > 1 else 2
                a10 = 1 if a > 1 else 2
                a11 = 1 if a > 1 else 2
                a12 = 1 if a > 1 else 2
                a13 = 1 if a > 1 else 2

                for i in range(1):
                    if a > 0:
                        print("111")
                        # a = 1
                    else:
                        print("222")
                return b

            self.check_insert_to_line(foo, tracing, foo.__code__.co_firstlineno + 2)

        finally:
            sys.stdout = self.original_stdout

    def test_long_lines(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            def foo():
                a = 1
                b = 1 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23
                c = 1 if b > 1 else 2 if b > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23
                d = 1 if c > 1 else 2 if c > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23 if a > 1 else 2 if a > 0 else 3 if a > 4 else 23
                e = d + 1
                return e

            self.check_insert_to_line(foo, tracing, foo.__code__.co_firstlineno + 2)


        finally:
            sys.stdout = self.original_stdout

    def test_many_names(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            from tests_python._many_names_example import foo
            self.check_insert_to_line(foo, tracing, foo.__code__.co_firstlineno + 2)

        finally:
            sys.stdout = self.original_stdout