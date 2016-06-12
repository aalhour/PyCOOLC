![PyCOOLC](misc/pycoolc_logo.png)

A (work in progress) compiler for **[COOL](https://en.wikipedia.org/wiki/Cool_(programming_language))** (**C**lassroom **O**bject **O**riented **L**anguage), targeting the MIPS 32-bit Architecture and written entirely in Python 3.

**COOL** is a small statically-typed object-oriented language that is type-safe and garbage collected. It has mainly 3 primitive data types: Integers, Strings and Booleans (`true`, `false`). It supports conditional and iterative control flow in addition to pattern matching. Everything in COOL is an expression! Many example COOL programs can be found under the [/examples](/examples/README.md) directory.

A formal treatment of **COOL**'s Context-Free Grammar can be found at [/docs/CFG.md](/docs/CFG.md).

------------------------------

## CONTENTS

  * [Overview](#overview).
  * [Development Status](#dev-status).
  * [Requirements](#requirements).
  * [Usage](#usage).
    + [Standalone](#standalone).
      * [Lexer](#lexer).
      * [Parser](#parser).
    + [Python Module](#python-module).
  * [Language Features](#language-features).
  * [License](#license)

------------------------------

## OVERVIEW

PyCOOLC follows classical compiler architecture, it consists mainly of two main logical components: Frontend and Backend.

Given a program file(s), the compiler starts off at the Frotend level, in which it progresses through the compilation process in terms of phases. Firstly, it enters the scanning phase in which Lexical Analysis is done and as a result the program is turned into a list of tokens. It then progresses into the parsing phase where Syntactical Analysis of the token stream is done based on the the language grammar rules. If parsing finishes successfully, an AST (Abstract Syntax Tree) of the program source code is generated as a result. After that, the compiler enters the Semantic Analysis phase in which it performs Type Checking and various other tasks on the generated AST. The completion of Semantic Analysis marks the finish line of the Compiler Frontend component.

Compiler Backend consists of two additional phases: Optimization and Code Generation. Optimization starts right after Semantic Analysis with the modified AST, it modifies the AST even further by carrying several optimization tasks such as: eliminating dead code, preparing it for the 5th, and last, phase of the compilation process: Code Generation. In the Code Generation phase, the compiler processes final version of the AST emitting MIPS 32-bit Assembly Machine Code.


## DEV. STATUS

Each Compiler stage and Runtime feature is designed as a separate component that can be used standalone or as a Python module, the following is the development status of each one:

| Compiler Stage     | Python Module                     | Issue                             | Status          |
|:-------------------|:----------------------------------|:----------------------------------|:----------------|
| Lexical Analysis   | [`lexer.py`](/pycoolc/lexer.py)   | [@issue #2](https://git.io/vr1gx) | **done**        |
| Parsing            | [`parser.py`](/pycoolc/parser.py) | [@issue #3](https://git.io/vr12k) | **done**        |
| Semantic Analysis  | -                                 | [@issue #4](https://git.io/vr12O) | -               |
| Optimization       | -                                 | [@issue #5](https://git.io/vr1Vd) | -               | 
| Code Generation    | -                                 | [@issue #6](https://git.io/vr1VA) | -               |
| Garbage Collection | -                                 | [@issue #8](https://git.io/vof6z) | -               |


## REQUIREMENTS

 * Python >= 3.5.
 * SPIM - MIPS 32-bit Assembly Simulator: [@Homepage](http://spimsimulator.sourceforge.net), [@SourceForge](https://sourceforge.net/projects/spimsimulator/files/).
 * All Python packages listed in: [`requirements.txt`](requirements.txt).


## USAGE

### STANDALONE

#### Lexer

```bash
./lexer.py hello_world.cl
```

#### Parser

```bash
./parser.py hello_world.cl
```

### PYTHON MODULE

```python
from pycoolc.lexer import PyCoolLexer
from pycoolc.parser import PyCoolParser

lexer = PyCoolLexer()
lexer.build()
lexer.input(a_cool_program_source_code_str)
for token in lexer:
    print(token)
```

## LANGUAGE FEATURES

  * Primitive Data Types:
    + Integers.
    + Strings.
    + Booleans (`true`, `false`).
  * Object Oriented:
    + Class Declaration.
    + Object Instantiation.
    + Inheritance.
    + Class Features and Methods.
  * Strong Static Typing.
  * Pattern Matching.
  * Control Flow:
    + Switch Case.
    + If/Then/Else Statements.
    + While Loops.
  * Automatic Memory Management:
    + Garbage Collection.

## LICENSE

This project is licensed under the [MIT License](LICENSE).

All copyrights of the files and documents under the [/docs](/docs) directory belong to their original owners.

