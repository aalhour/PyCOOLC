#!/usr/bin/env python3

from pycoolc.ast import AST, Self


def print_readable_ast(tree, level=0, inline=False):
    """
    Prints the nodes of an abstract syntax tree on stdout with indentation.

    :param tree: An Abstract Syntax Tree class instance.
    :param level: The indentation level.
    :param inline: Whether or not to indent the first line.
    :return: None. The AST is printed directly to stdout.
    """
    #####
    # INTERNAL HELPERS
    #
    def indent(source_string, level=1, lstrip_first=False):
        """
        Indent each line of the provided string by the specified level.

        :param source_string: The string to indent.
        :param level: The level to indent (`level * '    '`). Defaults to 1.
        :param lstrip_first: If this is `True`, then the first line is not indented. Defaults to `False`.
        :return: string.
        """
        indentation = "    "
        out = '\n'.join((level * indentation) + i for i in source_string.splitlines())
        if lstrip_first:
            return out.lstrip()
        return out

    def is_node(node):
        """
        Checks whether a given object is an instance of an AST class.
        """
        return isinstance(node, AST) and hasattr(node, 'to_tuple')
    
    #####
    # BEGIN
    #
    if is_node(tree):
        attrs = tree.to_tuple()
        
        # First attribute is always the class name
        if len(attrs) <= 1:
            print(indent('{0}()'.format(tree.clsname), level, inline))
        else:
            print(indent('{0}('.format(tree.clsname), level, inline))
            for key, value in attrs:
                if key == "class_name":
                    continue
                print(indent(key + '=', level + 1), end='')
                print_readable_ast(value, level + 1, True)
            print(indent(')', level))

    elif isinstance(tree, (tuple, list)):
        braces = '()' if isinstance(tree, tuple) else '[]'
        if len(tree) == 0:
            print(braces)
        else:
            print(indent(braces[0], level, inline))
            for obj in tree:
                print_readable_ast(obj, level + 1)
            print(indent(braces[1], level))

    else:
        print(indent(repr(tree), level, inline))

