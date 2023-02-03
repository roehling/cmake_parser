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
from attrs import define, evolve
from typing import Dict, List, Tuple, Union
from .lexer import Token
from .error import CMakeResolveError


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
            raise CMakeResolveError(
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
