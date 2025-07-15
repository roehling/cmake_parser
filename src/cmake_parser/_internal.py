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
Internal utility functions
"""
from functools import wraps
from warnings import warn
from typing import ParamSpec, TypeVar
from collections.abc import Callable

_P = ParamSpec("_P")
_T = TypeVar("_T")


def deprecated_alias[_T, **_P](
    new_func: Callable[_P, _T],
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def deprecated_alias_impl(old_func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(new_func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            warn(
                f"{old_func.__name__} is a deprecated alias for {new_func.__name__}",
                DeprecationWarning,
                stacklevel=2,
            )
            return new_func(*args, **kwargs)

        return wrapper

    return deprecated_alias_impl
