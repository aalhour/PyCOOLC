![PyCOOLC Logo](http://i.imgur.com/pLIqWi5.png)

A (Work In Progress) compiler for the **[COOL](https://en.wikipedia.org/wiki/Cool_(programming_language))** programming language, written entirely in Python 3. **COOL** stands for **C**lassroom **O**bject **O**riented **L**anguage.

**COOL** is a small object oriented language that is type-safe, garbage collected, strongly types and type safe. It has mainly 3 primitive data types: Integers, Strings and Booleans (True and False). It supports control flow and pattern matching. Many example **COOL** programs can be found under the [/examples](/examples/README.md) directory.

A formal treatment of **COOL**'s Context-Free Grammar can be found at [/docs/CFG.md](/docs/CFG.md).

------------------------------

## CONTENTS

  * [Development Status](#dev-status).
  * [Requirements](#requirements).
  * [Usage](#usage).
    + [Standalone](#standalone).
      * [Lexer](#lexer).
      * [Parser](#parser).
    + [Python Module](#python-module).
  * [Language Feature](#language-features).
  * [License](#license)

------------------------------

## DEV. STATUS

Each Compiler stage is designed as a separate component that can be used standalone or as a Python module, the following is the development status of each one:

| Compiler Stage    | Python Module                     | Issue                             | Status          |
|:------------------|:----------------------------------|:----------------------------------|:----------------|
| Lexical Analysis  | [`lexer.py`](/pycoolc/lexer.py)   | [@issue #2](https://git.io/vr1gx) | **done**        |
| Parsing           | [`parser.py`](/pycoolc/parser.py) | [@issue #3](https://git.io/vr12k) | **in progress** |
| Semantic Analysis | -                                 | [@issue #4](https://git.io/vr12O) | -               |
| Optimization      | -                                 | [@issue #5](https://git.io/vr1Vd) | -               | 
| Code Generation   | -                                 | [@issue #6](https://git.io/vr1VA) | -               |

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

