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
if __name__ == "__main__":
    import sys

    if 0:
        from pprint import pprint
        from .parser import parse_tree
        with open(sys.argv[1]) as f:
            test_data = f.read()
        pprint(parse_tree(test_data))

    if 1:
        from .lexer import Token
        from .interpreter import resolve_args, Context
        ctx = Context(var={"A": "one", "B": "red\\;violet;green;blue"})
        print(resolve_args(ctx, [Token(kind="RAW", value="${A};${B}", span=None, line=None, column=None)]))
