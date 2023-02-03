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
from functools import partial
from typing import List, Optional, Type
from .lexer import tokenize, TokenGenerator
from .ast import *
from .error import CMakeParseError


def _bail(item, data, msg):
    raise CMakeParseError(
        f"{msg} at line {item.line}, column {item.column}: {data[item.span]!r}"
    )


def _parse_argument_tokens(G: TokenGenerator) -> List[Token]:
    result = []
    token = next(G, None)
    while token is not None:
        result.append(token)
        if token.kind == "LPAREN":
            result.extend(_parse_argument_tokens(G))
        if token.kind == "RPAREN":
            return result
        token = next(G, None)
    raise CMakeParseError("Expected ')' and got unexpected end of file")


def parse_raw(data: str) -> AstNodeGenerator:
    G = tokenize(data)
    token = next(G, None)
    while token is not None:
        if token.kind == "COMMENT":
            yield Comment(
                line=token.line,
                column=token.column,
                comment=token.value,
                span=token.span,
            )
            token = next(G, None)
            continue
        if token.kind == "UNMATCHED_BRACKET":
            _bail(token, data, "Unmatched opening bracket")
        if token.kind != "RAW":
            _bail(token, data, "Expected command name")
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", token.value):
            _bail(token, data, "Invalid command name identifier")
        lparen = next(G, None)
        if lparen is None:
            raise CMakeParseError("Expected '(' and got unexpected end of file")
        if lparen.kind != "LPAREN":
            _bail(lparen, data, "Expected '('")
        args = _parse_argument_tokens(G)
        rparen = args.pop()
        yield Command(
            line=token.line,
            column=token.column,
            identifier=token.value,
            args=args,
            span=slice(token.span.start, rparen.span.stop),
        )
        token = next(G, None)


def _parse_block(
    cls: Type[AstNode],
    cmd: Command,
    data: str,
    G: AstNodeGenerator,
) -> AstNodeGenerator:
    sequence = list(
        _parse_elements(data, G, parent=cmd, until=[f"end{cmd.identifier.lower()}"])
    )
    end = sequence.pop()
    yield cls(
        line=cmd.line,
        column=cmd.column,
        span=slice(cmd.span.start, end.span.stop),
        args=cmd.args,
        body=sequence,
    )


def _parse_alias(
    cls: Type[Builtin], cmd: Command, data: str, G: AstNodeGenerator
) -> AstNodeGenerator:
    yield cls(line=cmd.line, column=cmd.column, span=cmd.span, args=cmd.args)


def _parse_noargs(
    cls: Type[Builtin], cmd: Command, data: str, G: AstNodeGenerator
) -> AstNodeGenerator:
    if cmd.args:
        _bail(cmd, data, "Builtin command accepts no arguments")
    yield cls(line=cmd.line, column=cmd.column, span=cmd.span)


def _parse_if(cmd: Command, data: str, G: AstNodeGenerator) -> AstNodeGenerator:
    if_true = list(
        _parse_elements(data, G, parent=cmd, until=["else", "elseif", "endif"])
    )
    end = if_true.pop()
    if end.identifier.lower() == "elseif":
        yield If(
            line=cmd.line,
            column=cmd.column,
            span=slice(cmd.span.start, (if_true[-1] if if_true else cmd).span.stop),
            args=cmd.args,
            if_true=if_true,
            if_false=list(_parse_if(end, data, G)),
        )
        return
    if end.identifier.lower() == "else":
        if_false = list(_parse_elements(data, G, parent=cmd, until=["endif"]))
        end = if_false.pop()
    else:
        if_false = None
    yield If(
        line=cmd.line,
        column=cmd.column,
        span=slice(cmd.span.start, end.span.stop),
        args=cmd.args,
        if_true=if_true,
        if_false=if_false,
    )


_transformers = {
    "block": partial(_parse_block, Block),
    "macro": partial(_parse_block, Macro),
    "foreach": partial(_parse_block, ForEach),
    "function": partial(_parse_block, Function),
    "while": partial(_parse_block, While),
    "break": partial(_parse_noargs, Break),
    "continue": partial(_parse_noargs, Continue),
    "return": partial(_parse_alias, Return),
    "math": partial(_parse_alias, Math),
    "set": partial(_parse_alias, Set),
    "unset": partial(_parse_alias, Unset),
    "option": partial(_parse_alias, Option),
    "if": _parse_if,
}


def _parse_elements(
    data: str,
    G: AstNodeGenerator,
    parent: Optional[AstNode] = None,
    until: Optional[List[str]] = None,
) -> AstNodeGenerator:
    elem = next(G, None)
    while elem is not None:
        if isinstance(elem, Command):
            transformer = _transformers.get(elem.identifier.lower(), None)
            if transformer is not None:
                yield from transformer(elem, data, G)
            else:
                yield elem
            if until is not None and elem.identifier.lower() in until:
                return
        else:
            yield elem
        elem = next(G, None)
    if parent is not None and until is not None:
        _bail(
            parent,
            data,
            f"No {' nor '.join(repr(f'{u}()') for u in until)} for command",
        )


def parse_tree(data: str) -> AstNodeGenerator:
    G = parse_raw(data)
    return _parse_elements(data, G)
