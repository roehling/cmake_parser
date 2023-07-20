..
    CMake Parser
    Copyright 2023 Timo Röhling <timo@gaussglocke.de>
    SPDX-License-Identifier: Apache-2.0

cmake_parser
============

:mod:`cmake_parser` is a pure Python parser for CMake code. It is still work in progress,
but has reasonable support for the most important CMake features: 

* AST representation of CMake code
* Correct handling of quoted and bracketed values
* Variable expansion
* Expression evaluation

Notably missing are:

* Generator expressions
* Automatic macro expansion

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/lexer
   api/parser
   api/ast
   api/interpreter
   api/error


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
