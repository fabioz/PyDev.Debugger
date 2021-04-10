"""
Bytecode analysing utils. Originally added for using in smart step into.

Note: not importable from Python 2.
"""

import sys
from _pydev_bundle import pydev_log
if sys.version_info[0] < 3:
    raise ImportError('This module is only compatible with Python 3.')

from types import CodeType
from _pydevd_frame_eval.vendored import bytecode
from _pydevd_frame_eval.vendored.bytecode import cfg as bytecode_cfg
import dis
from collections import namedtuple
import opcode as _opcode

from _pydevd_bundle.pydevd_constants import IS_PY3K, KeyifyList, DebugInfoHolder
from bisect import bisect
from collections import deque

# When True, throws errors on unknown bytecodes, when False, ignore those as if they didn't change the stack.
STRICT_MODE = False

DEBUG = False

_BINARY_OPS = set([opname for opname in dis.opname if opname.startswith('BINARY_')])

_BINARY_OP_MAP = {
    'BINARY_POWER': '__pow__',
    'BINARY_MULTIPLY': '__mul__',
    'BINARY_MATRIX_MULTIPLY': '__matmul__',
    'BINARY_FLOOR_DIVIDE': '__floordiv__',
    'BINARY_TRUE_DIVIDE': '__div__',
    'BINARY_MODULO': '__mod__',
    'BINARY_ADD': '__add__',
    'BINARY_SUBTRACT': '__sub__',
    'BINARY_LSHIFT': '__lshift__',
    'BINARY_RSHIFT': '__rshift__',
    'BINARY_AND': '__and__',
    'BINARY_OR': '__or__',
    'BINARY_XOR': '__xor__',
    'BINARY_SUBSCR': '__getitem__',
}

if not IS_PY3K:
    _BINARY_OP_MAP['BINARY_DIVIDE'] = '__div__'

_UNARY_OPS = set([opname for opname in dis.opname if opname.startswith('UNARY_') and opname != 'UNARY_NOT'])

_UNARY_OP_MAP = {
    'UNARY_POSITIVE': '__pos__',
    'UNARY_NEGATIVE': '__neg__',
    'UNARY_INVERT': '__invert__',
}

_COMP_OP_MAP = {
    '<': '__lt__',
    '<=': '__le__',
    '==': '__eq__',
    '!=': '__ne__',
    '>': '__gt__',
    '>=': '__ge__',
    'in': '__contains__',
    'not in': '__contains__',
}

Target = namedtuple('Target', ['arg', 'lineno', 'offset'])


class _TargetIdHashable(object):

    def __init__(self, target):
        self.target = target

    def __eq__(self, other):
        if not hasattr(other, 'target'):
            return
        return other.target is self.target

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return id(self.target)


class _StackInterpreter(object):
    '''
    Good reference: https://github.com/python/cpython/blob/fcb55c0037baab6f98f91ee38ce84b6f874f034a/Python/ceval.c
    '''

    def __init__(self, bytecode):
        self.bytecode = bytecode
        self._stack = deque()
        self.function_calls = []
        self.load_attrs = {}
        self.analyze_code_objects = set()

    def __str__(self):
        return 'Stack:\nFunction calls:\n%s\nLoad attrs:\n%s\n' % (self.function_calls, list(self.load_attrs.values()))

    def _getname(self, instr):
        if instr.opcode in _opcode.hascompare:
            cmp_op = dis.cmp_op[instr.arg]
            if cmp_op not in ('exception match', 'BAD'):
                return _COMP_OP_MAP.get(cmp_op, cmp_op)
        return instr.arg

    def _getcallname(self, instr):
        if instr.name == 'BINARY_SUBSCR':
            return '__getitem__().__call__'
        if instr.name == 'CALL_FUNCTION':
            return '__call__().__call__'
        if instr.name == 'MAKE_FUNCTION':
            return '__func__().__call__'
        name = self._getname(instr)
        if not isinstance(name, str):
            return None
        if name.endswith('>'):  # xxx.<listcomp>, xxx.<lambda>, ...
            return name.split('.')[-1]
        return name

    def on_LOAD_GLOBAL(self, instr):
        self._stack.append(instr)

    def on_LOAD_ATTR(self, instr):
        self._stack.pop()  # replaces the current top
        self._stack.append(instr)
        self.load_attrs[_TargetIdHashable(instr)] = Target(self._getname(instr), instr.lineno, instr.offset)

    on_LOOKUP_METHOD = on_LOAD_ATTR  # Improvement in PyPy

    def on_LOAD_CONST(self, instr):
        self._stack.append(instr)

    def on_STORE_FAST(self, instr):
        try:
            self._stack.pop()
        except IndexError:
            pass  # Ok, we may have a block just with the store
        self._stack.append(instr)

    def _handle_call_from_instr(self, func_name_instr, func_call_instr):
        self.load_attrs.pop(_TargetIdHashable(func_name_instr), None)
        call_name = self._getcallname(func_name_instr)
        if call_name not in(None, '<listcomp>', '<genexpr>'):
            self.function_calls.append(Target(call_name, func_name_instr.lineno, func_call_instr.offset))
        self._stack.append(func_call_instr)  # Keep the func call as the result

    def on_COMPARE_OP(self, instr):
        try:
            _right = self._stack.pop()
        except IndexError:
            return
        try:
            _left = self._stack.pop()
        except IndexError:
            return

        cmp_op = dis.cmp_op[instr.arg]
        if cmp_op not in ('exception match', 'BAD'):
            self.function_calls.append(Target(self._getname(instr), instr.lineno, instr.offset))

        self._stack.append(instr)

    def on_IS_OP(self, instr):
        try:
            self._stack.pop()
        except IndexError:
            return
        try:
            self._stack.pop()
        except IndexError:
            return

    def on_BINARY_SUBSCR(self, instr):
        try:
            _sub = self._stack.pop()
        except IndexError:
            return
        try:
            _container = self._stack.pop()
        except IndexError:
            return
        self.function_calls.append(Target(_BINARY_OP_MAP[instr.name], instr.lineno, instr.offset))
        self._stack.append(instr)

    on_BINARY_MATRIX_MULTIPLY = on_BINARY_SUBSCR
    on_BINARY_POWER = on_BINARY_SUBSCR
    on_BINARY_MULTIPLY = on_BINARY_SUBSCR
    on_BINARY_FLOOR_DIVIDE = on_BINARY_SUBSCR
    on_BINARY_TRUE_DIVIDE = on_BINARY_SUBSCR
    on_BINARY_MODULO = on_BINARY_SUBSCR
    on_BINARY_ADD = on_BINARY_SUBSCR
    on_BINARY_SUBTRACT = on_BINARY_SUBSCR
    on_BINARY_LSHIFT = on_BINARY_SUBSCR
    on_BINARY_RSHIFT = on_BINARY_SUBSCR
    on_BINARY_AND = on_BINARY_SUBSCR
    on_BINARY_OR = on_BINARY_SUBSCR
    on_BINARY_XOR = on_BINARY_SUBSCR

    def on_LOAD_METHOD(self, instr):
        # ceval sets the top and pushes an additional... the
        # final result is simply one additional instruction.
        self._stack.append(instr)

    def on_MAKE_FUNCTION(self, instr):
        qualname = self._stack.pop()
        code_obj = self._stack.pop()
        arg = instr.arg
        if arg & 0x08:
            _func_closure = self._stack.pop()
        if arg & 0x04:
            _func_annotations = self._stack.pop()
        if arg & 0x02:
            _func_kwdefaults = self._stack.pop()
        if arg & 0x01:
            _func_defaults = self._stack.pop()

        call_name = self._getcallname(qualname)
        if call_name in ('<genexpr>', '<listcomp>'):
            if isinstance(code_obj.arg, CodeType):
                self.analyze_code_objects.add(code_obj.arg)
        self._stack.append(qualname)

    def on_LOAD_FAST(self, instr):
        self._stack.append(instr)

    on_LOAD_BUILD_CLASS = on_LOAD_FAST

    def on_CALL_METHOD(self, instr):
        # pop the actual args
        for _ in range(instr.arg):
            self._stack.pop()

        func_name_instr = self._stack.pop()
        self._handle_call_from_instr(func_name_instr, instr)

    def on_CALL_FUNCTION(self, instr):
        arg = instr.arg

        argc = arg & 0xff  # positional args
        argc += ((arg >> 8) * 2)  # keyword args

        # pop the actual args
        for _ in range(argc):
            try:
                self._stack.pop()
            except IndexError:
                return

        try:
            func_name_instr = self._stack.pop()
        except IndexError:
            return
        self._handle_call_from_instr(func_name_instr, instr)

    def on_CALL_FUNCTION_KW(self, instr):
        # names of kw args
        _names_of_kw_args = self._stack.pop()

        # pop the actual args
        for _ in range(instr.arg):
            self._stack.pop()

        func_name_instr = self._stack.pop()
        self._handle_call_from_instr(func_name_instr, instr)

    def on_CALL_FUNCTION_VAR_KW(self, instr):
        # names of kw args
        _names_of_kw_args = self._stack.pop()

        arg = instr.arg

        argc = arg & 0xff  # positional args
        argc += ((arg >> 8) * 2)  # keyword args

        # also pop **kwargs
        self._stack.pop()

        # pop the actual args
        for _ in range(argc):
            self._stack.pop()

        func_name_instr = self._stack.pop()
        self._handle_call_from_instr(func_name_instr, instr)

    def on_CALL_FUNCTION_EX(self, instr):
        if instr.arg & 0x01:
            _kwargs = self._stack.pop()
        _callargs = self._stack.pop()
        func_name_instr = self._stack.pop()
        self._handle_call_from_instr(func_name_instr, instr)

    def on_YIELD_VALUE(self, instr):
        pass  # ok: doesn't change the stack

    def on_SETUP_LOOP(self, instr):
        pass  # ok: doesn't change the stack

    def on_FOR_ITER(self, instr):
        pass  # ok: doesn't change the stack

    def on_BREAK_LOOP(self, instr):
        pass  # ok: doesn't change the stack

    def on_JUMP_IF_FALSE_OR_POP(self, instr):
        try:
            self._stack.pop()
        except IndexError:
            return

    on_JUMP_IF_TRUE_OR_POP = on_JUMP_IF_FALSE_OR_POP

    def on_JUMP_IF_NOT_EXC_MATCH(self, instr):
        try:
            self._stack.pop()
        except IndexError:
            return
        try:
            self._stack.pop()
        except IndexError:
            return

    def on_JUMP_ABSOLUTE(self, instr):
        pass  # ok: doesn't change the stack

    def on_RERAISE(self, instr):
        pass  # ok: doesn't change the stack

    def on_LIST_TO_TUPLE(self, instr):
        pass  # ok: doesn't change the stack

    def on_ROT_TWO(self, instr):
        try:
            p0 = self._stack.pop()
        except IndexError:
            return

        try:
            p1 = self._stack.pop()
        except:
            self._stack.append(p0)
            return

        self._stack.append(p0)
        self._stack.append(p1)

    def on_ROT_THREE(self, instr):
        try:
            p0 = self._stack.pop()
        except IndexError:
            return

        try:
            p1 = self._stack.pop()
        except:
            self._stack.append(p0)
            return

        try:
            p2 = self._stack.pop()
        except:
            self._stack.append(p0)
            self._stack.append(p1)
            return

        self._stack.append(p0)
        self._stack.append(p1)
        self._stack.append(p2)

    def on_ROT_FOUR(self, instr):
        try:
            p0 = self._stack.pop()
        except IndexError:
            return

        try:
            p1 = self._stack.pop()
        except:
            self._stack.append(p0)
            return

        try:
            p2 = self._stack.pop()
        except:
            self._stack.append(p0)
            self._stack.append(p1)
            return

        try:
            p3 = self._stack.pop()
        except:
            self._stack.append(p0)
            self._stack.append(p1)
            self._stack.append(p2)
            return

        self._stack.append(p0)
        self._stack.append(p1)
        self._stack.append(p2)
        self._stack.append(p3)

    def on_POP_TOP(self, instr):
        try:
            self._stack.pop()
        except IndexError:
            pass  # Ok (in the end of blocks)

    def on_BUILD_MAP(self, instr):
        for _i in range(instr.arg):
            self._stack.pop()
            self._stack.pop()
        self._stack.append(instr)

    def on_BUILD_CONST_KEY_MAP(self, instr):
        self._stack.pop()  # keys
        for _i in range(instr.arg):
            self._stack.pop()  # value
        self._stack.append(instr)

    def on_RETURN_VALUE(self, instr):
        self.on_POP_TOP(instr)

    def on_POP_JUMP_IF_FALSE(self, instr):
        self.on_POP_TOP(instr)

    def on_POP_JUMP_IF_TRUE(self, instr):
        self.on_POP_TOP(instr)

    def on_DICT_MERGE(self, instr):
        self.on_POP_TOP(instr)

    def on_GET_ITER(self, instr):
        pass  # ok: doesn't change the stack (converts top to getiter(top))

    def on_LIST_APPEND(self, instr):
        self.on_POP_TOP(instr)

    def on_LIST_EXTEND(self, instr):
        self.on_POP_TOP(instr)

    def on_UNPACK_SEQUENCE(self, instr):
        self._stack.pop()
        for _i in range(instr.arg):
            self._stack.append(instr)

    def on_BUILD_LIST(self, instr):
        for _i in range(instr.arg):
            self._stack.pop()
        self._stack.append(instr)

    on_BUILD_TUPLE = on_BUILD_LIST
    on_BUILD_TUPLE_UNPACK_WITH_CALL = on_BUILD_LIST
    on_BUILD_TUPLE_UNPACK = on_BUILD_LIST
    on_BUILD_LIST_UNPACK = on_BUILD_LIST
    on_BUILD_MAP_UNPACK_WITH_CALL = on_BUILD_LIST
    on_BUILD_SET = on_BUILD_LIST

    def on_SETUP_FINALLY(self, instr):
        pass

    def on_RAISE_VARARGS(self, instr):
        pass

    def on_POP_BLOCK(self, instr):
        pass

    def on_JUMP_FORWARD(self, instr):
        pass

    def on_POP_EXCEPT(self, instr):
        pass

    def on_SETUP_EXCEPT(self, instr):
        pass

    on_WITH_EXCEPT_START = on_SETUP_EXCEPT

    def on_END_FINALLY(self, instr):
        pass

    def on_BEGIN_FINALLY(self, instr):
        pass

    def on_SETUP_WITH(self, instr):
        pass

    def on_WITH_CLEANUP_START(self, instr):
        pass

    def on_WITH_CLEANUP_FINISH(self, instr):
        pass

    def on_DUP_TOP(self, instr):
        try:
            i = self._stack[-1]
        except IndexError:
            # ok (in the start of block)
            self._stack.append(instr)
        else:
            self._stack.append(i)


def _get_smart_step_into_targets(code):
    analyzed_code_objects = set()
    analyzed_code_objects.add(code)

    b = bytecode.Bytecode.from_code(code)
    cfg = bytecode_cfg.ControlFlowGraph.from_bytecode(b)

    ret = []

    for block in cfg:
        if DEBUG:
            print('\nStart block----')
        stack = _StackInterpreter(block)
        for instr in block:
            try:
                func_name = 'on_%s' % (instr.name,)
                func = getattr(stack, func_name, None)
                if func is None:
                    if STRICT_MODE:
                        raise AssertionError('%s not found.' % (func_name,))
                    else:
                        continue
                if DEBUG:
                    print('\nWill handle: ', instr, '>>', stack._getname(instr), '<<')
                func(instr)
                if DEBUG:
                    for entry in stack._stack:
                        print('    arg:', stack._getname(entry), '(', entry, ')')
            except:
                if STRICT_MODE:
                    raise  # Error in strict mode.
                else:
                    # In non-strict mode, log it (if in verbose mode) and keep on going.
                    if DebugInfoHolder.DEBUG_TRACE_LEVEL >= 2:
                        pydev_log.exception('Exception computing step into targets (handled).')

        for code_obj in stack.analyze_code_objects:
            if code_obj not in analyzed_code_objects:
                analyzed_code_objects.add(code_obj)
                ret.extend(_get_smart_step_into_targets(code_obj))

        ret.extend(stack.function_calls)
        ret.extend(stack.load_attrs.values())
    return ret


# Note that the offset is unique within the frame (so, we can use it as the target id).
# Also, as the offset is the instruction offset within the frame, it's possible to
# to inspect the parent frame for frame.f_lasti to know where we actually are (as the
# caller name may not always match the new frame name).
Variant = namedtuple('Variant', ['name', 'is_visited', 'line', 'offset', 'call_order'])


def calculate_smart_step_into_variants(frame, start_line, end_line, base=0):
    """
    Calculate smart step into variants for the given line range.
    :param frame:
    :type frame: :py:class:`types.FrameType`
    :param start_line:
    :param end_line:
    :return: A list of call names from the first to the last.
    :note: it's guaranteed that the offsets appear in order.
    :raise: :py:class:`RuntimeError` if failed to parse the bytecode or if dis cannot be used.
    """
    variants = []
    is_context_reached = False
    code = frame.f_code
    lasti = frame.f_lasti

    call_order_cache = {}
    if DEBUG:
        dis.dis(code)

    for target in _get_smart_step_into_targets(code):
        name = target.arg
        if not isinstance(name, str):
            continue

        if target.lineno and target.lineno > end_line:
            break
        if not is_context_reached and target.lineno is not None and target.lineno >= start_line:
            is_context_reached = True
        if not is_context_reached:
            continue

        call_order = call_order_cache.get(name, 0) + 1
        call_order_cache[name] = call_order
        variants.append(
            Variant(
                name, target.offset <= lasti, target.lineno - base, target.offset, call_order))
    return variants


def get_smart_step_into_variant_from_frame_offset(frame_f_lasti, variants):
    """
    Given the frame.f_lasti, return the related `Variant`.

    :note: if the offset is found before any variant available or no variants are
           available, None is returned.

    :rtype: Variant|NoneType
    """
    if not variants:
        return None

    i = bisect(KeyifyList(variants, lambda entry:entry.offset), frame_f_lasti)

    if i == 0:
        return None

    else:
        return variants[i - 1]
