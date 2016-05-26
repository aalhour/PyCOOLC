# -----------------------------------------------------------------------------
# ast.py
#
# Author:       Ahmad Alhour (github.com/aalhour; aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Abstract Syntax Tree module. Provides classes for managing
#               the parse tree.
# -----------------------------------------------------------------------------


class Base:
    def __init__(self):
        pass

    def to_tuple(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_tuple())


class Program(Base):
    NODE_NAME = "PROGRAM"

    def __init__(self, classes):
        super(Program, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.classes])


class Class(Base):
    NODE_NAME = "CLASS"

    def __init__(self, name, inherits, features):
        super(Class, self).__init__()
        self.name = name
        self.inherits = inherits
        self.features = features

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.name, self.inherits, self.features])


class Inheritance(Base):
    NODE_NAME = "INHERITS"

    def __init__(self, inheritance_type=None):
        super(Inheritance, self).__init__()
        self.inheritance_type = inheritance_type

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.inheritance_type])

