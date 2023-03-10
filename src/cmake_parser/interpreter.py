# CMake Parser
# Copyright 2023 Timo Röhling <timo@gaussglocke.de>
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import os
from attrs import define, evolve
from typing import Dict, List, Tuple, Union
from .ast import *
from .lexer import Token, TokenGenerator
from .error import CMakeExprError


try:
    from typing import Self
except ImportError:
    from typing import TypeVar

    Self = TypeVar("Self", bound="Context")


@define
class Context:
    parent: Self = None
    var: Dict[str, str] = {}
    env: Dict[str, str] = {}
    cache: Dict[str, str] = {}
    functions: Dict[str, Function] = {}
    macros: Dict[str, Macro] = {}

    def exists(self, f):
        return os.path.exists(f)


_token_spec = [
    ("ESCAPE", r"\\."),
    ("SEMICOLON", r";"),
    ("VAR_BEGIN", r"\$(?P<VAR_TYPE>[A-Za-z]*)\{"),
    ("VAR_END", r"\}"),
    ("LITERAL", r"[^\\\$\{\}]+"),
]

_next_token = re.compile(
    "|".join(f"(?P<{name}>{expr})" for name, expr in _token_spec)
).match


_esc_sequences = {
    "r": "\r",
    "n": "\n",
    "t": "\t",
    ";": "\\;",  # Semicolons get special treatment in _split()
}


def _resolve_vars(ctx: Context, token: Token) -> str:
    def scan(s: str, pos: int) -> Tuple[str, int]:
        result = ""
        mo = _next_token(s, pos)
        while mo:
            kind = mo.lastgroup
            val = mo.group(kind)
            if kind == "VAR_BEGIN":
                var_type = mo.group("VAR_TYPE")
                identifier, end_pos = scan(s, mo.end(kind))
                if var_type == "":
                    result += ctx.var.get(identifier, "")
                elif var_type == "ENV":
                    result += ctx.env.get(identifier, "")
                elif var_type == "CACHE":
                    result += ctx.cache.get(identifier, "")
                mo = _next_token(s, end_pos)
                continue
            if kind == "VAR_END" and pos > 0:
                return result, mo.end(kind)
            if kind == "ESCAPE":
                result += _esc_sequences.get(val[1], val[1])
            else:
                result += val
            mo = _next_token(s, mo.end(kind))
        if pos > 0:
            raise CMakeExprError(
                f"variable reference without terminating '}}' at line {token.line}, column {token.column}: {s[pos:]!r}"
            )
        return result, len(s)

    return scan(token.value, 0)[0]


def _split(s: str) -> List[str]:
    result = []
    for item in re.finditer(r"(?:\\.|[^;\\])+", s):
        result.append(item.group(0).replace("\\;", ";"))
    return result


def resolve_args(ctx: Context, args: List[Token]) -> List[Token]:
    result = []
    for token in args:
        if token.kind == "RAW":
            value = _resolve_vars(ctx, token)
            result.extend(evolve(token, value=item) for item in _split(value))
        else:
            if token.kind == "QUOTED":
                value = _resolve_vars(ctx, token)
            else:
                value = token.value
            result.append(evolve(token, value=value))
    return result


class LookAheadIterator:
    def __init__(self, iterable):
        self._iterable = iter(iterable)
        self._exhausted = False
        self._lookahead = None
        try:
            self._lookahead = next(self._iterable)
        except StopIteration:
            self._exhausted = True

    def peek(self):
        return self._lookahead

    def __iter__(self):
        return self

    def __next__(self):
        if self._exhausted:
            raise StopIteration
        value = self._lookahead
        try:
            self._lookahead = next(self._iterable)
        except StopIteration:
            self._exhausted = True
        return value


def _is_true_constant(s: str) -> bool:
    try:
        number = float(s)
        return number != 0
    except ValueError:
        pass
    return s.upper() in ["ON", "YES", "TRUE", "Y"]


def _is_false_constant(s: str) -> bool:
    try:
        number = float(s)
        return number == 0
    except ValueError:
        pass
    su = s.upper()
    return su in ["", "OFF", "NO", "FALSE", "N", "IGNORE", "NOTFOUND"] or su.endswith(
        "-NOTFOUND"
    )


def _eval_value(ctx: Context, value: Union[bool, Token, str]) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, Token):
        if value.kind == "QUOTED":
            return _is_true_constant(value.value)
        value = value.value
    if _is_true_constant(value):
        return True
    if _is_false_constant(value):
        return False
    value = ctx.var.get(value, "")
    return not _is_false_constant(value)


def _get_argument(op: str, G: TokenGenerator) -> Token:
    token = next(G, None)
    if token is None or token.kind not in ["RAW", "QUOTED"]:
        raise CMakeExprError(f"missing argument for {op} operator")
    return token


def _eval_defined(ctx: Context, arg: Token) -> bool:
    return arg.value in ctx.var


def _eval_exists(ctx: Context, arg: Token) -> bool:
    return ctx.exists(arg.value)


def _eval_command(ctx: Context, arg: Token) -> bool:
    return arg.value in ctx.functions or arg.value in ctx.macros


_PRECEDENCES = {
    "AND": 1,
    "OR": 1,
    "NOT": 2,
}

_UNARY_OPS = {
    "DEFINED": _eval_defined,
    "EXISTS": _eval_exists,
    "COMMAND": _eval_command,
}

_BINARY_OPS = {}


def _eval_expr(ctx: Context, G: LookAheadIterator, precedence: int) -> bool:
    token = next(G, None)
    if token is None or token.kind == "RPAREN":
        return False
    stack = []
    while token is not None:
        if token.kind == "LPAREN":
            stack.append(_eval_expr(ctx, G, precedence=1))
        elif token.kind == "RPAREN":
            if len(stack) != 1:
                raise CMakeExprError("Malformed expression")
            return _eval_value(ctx, stack.pop())
        elif token.kind == "RAW":
            if token.value == "NOT":
                stack.append(not _eval_expr(ctx, G, precedence=2))
            elif token.value == "AND":
                first_arg = _eval_value(ctx, stack.pop())
                second_arg = _eval_expr(ctx, G, precedence=2)
                stack.append(first_arg and second_arg)
            elif token.value == "OR":
                first_arg = _eval_value(ctx, stack.pop())
                second_arg = _eval_expr(ctx, G, precedence=2)
                stack.append(first_arg or second_arg)
            else:
                unary_op = _UNARY_OPS.get(token.value, None)
                if unary_op:
                    arg = _get_argument(token.value, G)
                    stack.append(unary_op(ctx, arg))
                else:
                    binary_op = _BINARY_OPS.get(token.value, None)
                    if binary_op:
                        if not stack:
                            raise CMakeExprError(f"missing argument for {token.value} operator")
                        first_arg = stack.pop()
                        second_arg = _get_argument(token.value, G)
                        stack.append(binary_op(ctx, first_arg, second_arg))
                    else:
                        stack.append(token)
        else:
            stack.append(token)
        lookahead = G.peek()
        if lookahead is None:
            break
        if lookahead.kind == "RAW":
            lookahead_precendence = _PRECEDENCES.get(lookahead.value, precedence)
            if lookahead_precendence < precedence:
                break
        token = next(G, None)
    if len(stack) != 1:
        raise CMakeExprError("Malformed expression")
    return _eval_value(ctx, stack.pop())


def eval_expr(ctx: Context, args: List[Token]) -> bool:
    G = LookAheadIterator(args)
    return _eval_expr(ctx, G, precedence=1)
