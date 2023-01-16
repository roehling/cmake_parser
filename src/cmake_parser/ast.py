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
from attrs import define
from typing import Generator, List, Optional
from .lexer import Token


class AstNode:
    pass


AstNodeGenerator = Generator[AstNode, None, None]


@define
class AstFileNode:
    line: int
    column: int
    span: slice


@define
class Command(AstFileNode):
    identifier: str
    args: List[Token]


@define
class Builtin(AstFileNode):
    pass


@define
class Comment(AstFileNode):
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
