# CMake Parser
# Copyright 2023-2024 Timo Röhling <timo@gaussglocke.de>
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
from dataclasses import dataclass
from typing import Generator, List, Optional
from .lexer import Token


@dataclass
class AstNode:
    """Base class for all Abstract Syntax Tree elements

    :param span: the code location in the parsed string.
    """

    span: slice


AstNodeGenerator = Generator[AstNode, None, None]


@dataclass
class AstFileNode(AstNode):
    """
    Base class for all AST nodes with associated file location

    :param line: the line number where the corresponding code begins.
        Note that the code can span multiple lines.
    :param column: the column where the corresponding code begins.
    """

    line: int
    column: int


@dataclass
class Command(AstFileNode):
    """
    Generic representation of a single CMake instruction.

    CMake code consists of a serious of command invocations with a (possibly empty)
    list of arguments in parentheses. :class:`Command` and :class:`Comment` are the two
    possible outputs of :func:`~cmake_parser.parser.parse_raw`.

    :param identifier: the function or instruction name to be invoked.
    :param args: the tokens which form the argumen list.

    .. include:: argument_note.rst
    """

    identifier: str
    args: List[Token]


@dataclass
class Builtin(AstFileNode):
    """Base class for AST nodes which represent CMake built-in instructions with parseable arguments.

    :param args: the list of arguments.

    .. include:: argument_note.rst

    """

    args: List[Token]


@dataclass
class BuiltinNoArgs(AstFileNode):
    """Base class for AST nodes which represent CMake built-in instructions which can never have arguments"""


@dataclass
class BuiltinBlock(Builtin):
    """Base class for AST nodes which represent a block of CMake commands

    :param body: the list of commands which form the block.

    """

    body: List[AstNode]


@dataclass
class Comment(AstFileNode):
    """
    CMake Comment.

    This is the only AST node which does not represent executable code. Both
    :func:`~cmake_parser.parser.parse_raw` and :func:`~cmake_parser.parser.parse_tree` can be instructed
    to omit comments from their output.

    :param comment: The comment string without leading ``#`` or enclosing brackets.
    """

    comment: str


@dataclass
class Macro(BuiltinBlock):
    """
    Macro definition.

    This node represents a ``macro()``/``endmacro()`` block.
    """


@dataclass
class Function(BuiltinBlock):
    """
    Macro definition.

    This node represents a ``function()``/``endfunction()`` block.
    """


@dataclass
class Block(BuiltinBlock):
    """
    Scoped block.

    This node represents a ``block()``/``endblock()`` block.
    """


@dataclass
class ForEach(BuiltinBlock):
    """
    ForEach Loop.

    This node represents a ``foreach()``/``endforeach()`` block.
    """


@dataclass
class While(BuiltinBlock):
    """
    While Loop.

    This node represents a ``while()``/``endwhile()`` block.
    """


@dataclass
class If(Builtin):
    """
    Conditional block.

    This node represents a ``if()``/``else()``/``endif()`` block. ``elseif()`` statements are converted
    into a single :py:class:`If` command in ``if_false``.

    :param if_true: the list of commands to be executed if the expression evaluates to :py:const:`True`.
    :param if_false: the list of commands to be executed if the expression evaluates to :py:const:`False`.
    """

    if_true: List[AstNode]
    if_false: Optional[List[AstNode]]


class Break(BuiltinNoArgs):
    """
    Loop exit.

    This node represents the ``break()`` command.
    """


class Continue(BuiltinNoArgs):
    """
    Loop continuation.

    This node represents the ``continue()`` command.
    """


@dataclass
class Return(Builtin):
    """
    Return from function or module.

    This node represents the ``return()`` command.
    """


@dataclass
class Set(Builtin):
    """
    Set variable.

    This node represents the ``set()`` command.
    """


@dataclass
class Unset(Builtin):
    """
    Unset variable.

    This node represents the ``unset()`` command.
    """


@dataclass
class Option(Builtin):
    """
    Declare CMake option.

    This node represents the ``option()`` command.
    """


@dataclass
class Math(Builtin):
    """
    Math expression.

    This node represents the ``math()`` command.

    """


@dataclass
class Include(Builtin):
    """
    Include other CMake file.

    This node represents the ``include()`` command.
    """
