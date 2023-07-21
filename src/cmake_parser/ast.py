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
"""
Abstract Syntax Tree elements which are returned by
:func:`~cmake_parser.parser.parse_raw` and
:func:`~cmake_parser.parser.parse_tree`.
"""
from attrs import define
from typing import Generator, List, Optional
from .lexer import Token


class AstNode:
    """Base class for all Abstract Syntax Tree elements"""


AstNodeGenerator = Generator[AstNode, None, None]


@define
class AstFileNode:
    """Base class for all AST nodes with associated file location"""

    line: int
    column: int
    span: slice


@define
class Command(AstFileNode):
    """
    Generic representation of a single CMake instruction.

    CMake code consists of a serious of command invocations with a (possibly empty)
    list of arguments in parentheses. :class:`Command` and :class:`Comment` are the two
    possible outputs of :func:`~cmake_parser.parser.parse_raw`.

    :param identifier: the function or instruction name to be invoked
    :param args: the tokens which form the argumen list.

    .. note:: As variable expansion can split tokens into multiple arguments or remove
        them from the argument list altogether, there is no 1:1 relation between tokens and
        arguments.
    """

    identifier: str
    args: List[Token]


@define
class Builtin(AstFileNode):
    """Base class for AST nodes which represent CMake built-in instructions"""


@define
class Comment(AstFileNode):
    """
    CMake Comment.

    This is the only AST node which does not represent executable code. Both
    :func:`~cmake_parser.parser.parse_raw` and :func:`~cmake_parser.parser.parse_tree` can be instructed
    to omit comments from their output.
    """

    comment: str


@define
class Macro(Builtin):
    args: List[Token]
    body: List[AstNode]


@define
class Function(Builtin):
    args: List[Token]
    body: List[AstNode]


@define
class Block(Builtin):
    args: List[Token]
    body: List[AstNode]


@define
class ForEach(Builtin):
    args: List[Token]
    body: List[AstNode]


@define
class While(Builtin):
    args: List[Token]
    body: List[AstNode]


@define
class If(Builtin):
    args: List[Token]
    if_true: List[AstNode]
    if_false: Optional[List[AstNode]]


class Break(Builtin):
    pass


class Continue(Builtin):
    pass


@define
class Return(Builtin):
    args: List[Token]


@define
class Set(Builtin):
    args: List[Token]


@define
class Unset(Builtin):
    args: List[Token]


@define
class Option(Builtin):
    args: List[Token]


@define
class Math(Builtin):
    args: List[Token]


@define
class Include(Builtin):
    args: List[Token]
