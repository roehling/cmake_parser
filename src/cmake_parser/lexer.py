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
from attrs import define
from typing import Generator, List, Tuple

_token_spec = [
    ("SP", r"\s+"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("SEMICOLON", r";"),
    ("QUOTED", r'"(?:\\.|[^\\"])*"'),
    ("BRACKET_COMMENT", r"#\[(?P<COMMENT_FILL>=*)\[.*?\](?P=COMMENT_FILL)\]"),
    ("BRACKETED", r"\[(?P<BRACKET_FILL>=*)\[.*?\](?P=BRACKET_FILL)\]"),
    ("LINE_COMMENT", r"#(?!\[).*?$"),
    ("RAW", r'(?:\\.|[^\\\(\)"# \t\r\n;])+'),
]

_next_token = re.compile(
    "|".join(f"(?P<{name}>{expr})" for name, expr in _token_spec),
    re.MULTILINE | re.DOTALL,
).match


@define
class Token:
    kind: str
    value: str
    span: slice
    line: int
    column: int


TokenGenerator = Generator[Token, None, None]


def line_ranges(data: str) -> Generator[Tuple[int, int], None, None]:
    start = 0
    for mo in re.finditer(r"\r?\n", data):
        yield (start, mo.start())
        start = mo.end()
    yield (start, len(data))


def normalize_lineendings(data: str) -> str:
    return data.replace("\r\n", "\n")


def tokenize(data: str) -> TokenGenerator:
    pos = 0
    LR = line_ranges(data)
    L = next(LR, None)
    line = 1
    mo = _next_token(data)
    while mo is not None:
        kind = mo.lastgroup
        if kind != "SP":
            val = mo.group(kind)
            if kind == "QUOTED":
                val = val[1:-1]
                val = re.sub(r"\\\r?\n", "", val)
            elif kind == "BRACKETED":
                val = re.sub(
                    r"^\[(=*)\[(?:\r?\n)?(.*)\]\1\]$", r"\2", val, flags=re.DOTALL
                )
            elif kind == "BRACKET_COMMENT":
                val = re.sub(
                    r"^.\[(=*)\[(?:\r?\n)?(.*)\]\1\]$", r"\2", val, flags=re.DOTALL
                )
                kind = "COMMENT"
            elif kind == "LINE_COMMENT":
                val = val[1:]
                kind = "COMMENT"
            elif kind == "RAW":
                if re.match(r"#?\[=*\[", val):
                    kind = "UNMATCHED_BRACKET"
            yield Token(
                kind=kind,
                value=val,
                span=slice(mo.start(), mo.end()),
                line=line,
                column=mo.start() + 1 - L[0],
            )
        pos = mo.end()
        while L and L[1] < pos:
            L = next(LR, None)
            line += 1
        mo = _next_token(data, pos)
    if pos < len(data):
        yield Token(
            kind="UNPARSEABLE",
            value=None,
            span=slice(pos, len(data)),
            line=line,
            column=pos + 1 - L[0],
        )
