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

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from cmake_parser import __version__  # noqa

project = "cmake_parser"
copyright = "2023, Timo Röhling"
author = "Timo Röhling"
release = __version__

extensions = ["sphinx.ext.autodoc", "sphinx_autodoc_typehints"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "classic"
html_static_path = ["_static"]
