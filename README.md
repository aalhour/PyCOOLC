![PyCOOLC Logo](http://i.imgur.com/pLIqWi5.png)

A (Work In Progress) compiler for the **[COOL](https://en.wikipedia.org/wiki/Cool_(programming_language))** programming language, written entirely in Python 3. **COOL** stands for **C**lassroom **O**bject **O**riented **L**anguage. Many example COOL programs can be found under the [/example_cool_programs](/example_cool_programs) directory.

## DEV. STATUS

Each Compiler stage is designed as a separate component, the following is the completion status of each one:

 * [X] Lexer ([@issue #2](https://github.com/aalhour/PyCOOLC/issues/2)).
 * [ ] Parser ([@issue #3](https://github.com/aalhour/PyCOOLC/issues/3)).
 * [ ] Semantic Analyser ([@issue #4](https://github.com/aalhour/PyCOOLC/issues/4)).
 * [ ] Code Optimizer.
 * [ ] Code Generator.

## REQUIREMENTS

 * Python >= 3.5.
 * SPIM - MIPS 32-bit Assembly Simulator: [@Homepage](http://spimsimulator.sourceforge.net), [@SourceForge](https://sourceforge.net/projects/spimsimulator/files/).
 * All Python packages listed in: [`requirements.txt`](requirements.txt).

## LANGUAGE FEATURES

 * Object Orientedness:
  + Class Declaration.
  + Object Instantiation.
  + Inheritance.
 * Strong Static Typing.
 * Pattern Matching.
 * Control Flow:
  + Switch Case.
  + If/Then/Else Statments.
  + While Loops.
 * Automatic Memory Management:
  + Garbage Collection.

## LICENSE

This project is licensed under the [MIT License](LICENSE). All copyrights of the files and documents under the [/docs](/docs) directory belong to their original owners.

