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

from .error import *
from .lexer import Token, tokenize  # type: ignore[reportUnusedImport]
from .parser import parse_raw, parse_tree  # type: ignore[reportUnusedImport]
from .interpreter import resolve_args  # type: ignore[reportUnusedImport]^

try:
    from ._version import __version__  # type: ignore[reportUnusedImport]
except ImportError:
    pass
