#
# ASTUnitType.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.


from pynestml.modelprocessor.ASTNode import ASTNode


class ASTUnitType(ASTNode):
    """
    This class stores information regarding unit types and their properties.
    ASTUnitType. Represents an unit datatype. It can be a plain datatype as 'mV' or a
    complex data type as 'mV/s'
  
    unitType : leftParentheses='(' unitType rightParentheses=')'
               | base=unitType powOp='**' exponent=INTEGER
               | left=unitType (timesOp='*' | divOp='/') right=unitType
               | unitlessLiteral=INTEGER divOp='/' right=unitType
               | unit=NAME;
    """
    # encapsulated or not
    is_encapsulated = False
    compound_unit = None
    # pow rhs
    base = None
    is_pow = False
    exponent = None
    # arithmetic combination case
    lhs = None
    is_times = False
    is_div = False
    rhs = None
    # simple case, just a name
    unit = None
    # the corresponding symbol
    type_symbol = None

    def __init__(self, is_encapsulated=False, compound_unit=None, base=None, is_pow=False,
                 exponent=None, lhs=None, rhs=None, is_div=False, is_times=False, _unit=None, source_position=None):
        """
        Standard constructor of ASTUnitType.
        :param compound_unit: a unit encapsulated in brackets
        :type compound_unit: ASTUnitType
        :param base: the base rhs
        :type base: ASTUnitType
        :param is_pow: is a power rhs
        :type is_pow: bool
        :param exponent: the exponent rhs
        :type exponent: int
        :param lhs: the left-hand side rhs
        :type lhs: ASTUnitType or Integer
        :param rhs: the right-hand side rhs
        :type rhs: ASTUnitType
        :param is_div: is a division rhs
        :type is_div: bool
        :param is_times: is a times rhs
        :type is_times: bool
        :param _unit: is a single unit, e.g. mV
        :type _unit: string
        """
        super(ASTUnitType, self).__init__(source_position)
        self.is_encapsulated = is_encapsulated
        self.compound_unit = compound_unit
        self.base = base
        self.is_pow = is_pow
        self.exponent = exponent
        self.lhs = lhs
        self.is_times = is_times
        self.is_div = is_div
        self.rhs = rhs
        self.unit = _unit
        return

    def is_simple_unit(self):
        """
        Returns whether the rhs is a simple unit, e.g., mV.
        :return: True if simple unit, otherwise False.
        :rtype: bool
        """
        return self.unit is not None

    def is_arithmetic_expression(self):
        """
        Returns whether the rhs is a arithmetic combination, e.g, mV/mS.
        :return: True if arithmetic rhs, otherwise false.
        :rtype: bool
        """
        return self.lhs is not None and self.rhs is not None and (self.is_div or self.is_times)

    def get_lhs(self):
        """
        Returns the left-hand side rhs if present.
        :return: ASTUnitType instance if present, otherwise None.
        :rtype: ASTUnitType
        """
        return self.lhs

    def get_rhs(self):
        """
        Returns the right-hand side rhs if present.
        :return: ASTUnitType instance if present, otherwise None.
        :rtype: ASTUnitType
        """
        return self.rhs

    def get_type_symbol(self):
        return self.type_symbol

    def set_type_symbol(self, type_symbol):
        self.type_symbol = type_symbol

    def get_parent(self, ast):
        """
        Indicates whether a this node contains the handed over node.
        :param ast: an arbitrary ast node.
        :type ast: AST_
        :return: AST if this or one of the child nodes contains the handed over element.
        :rtype: AST_ or None
        """
        if self.is_encapsulated:
            if self.compound_unit is ast:
                return self
            elif self.compound_unit.get_parent(ast) is not None:
                return self.compound_unit.get_parent(ast)

        if self.is_pow:
            if self.base is ast:
                return self
            elif self.base.get_parent(ast) is not None:
                return self.base.get_parent(ast)
        if self.is_arithmetic_expression():
            if isinstance(self.get_lhs(), ASTUnitType):
                if self.get_lhs() is ast:
                    return self
                elif self.get_lhs().get_parent(ast) is not None:
                    return self.get_lhs().get_parent(ast)
            if self.get_rhs() is ast:
                return self
            elif self.get_rhs().get_parent(ast) is not None:
                return self.get_rhs().get_parent(ast)
        return None

    def __str__(self):
        """
        Returns a string representation of the unit type.
        :return: a string representation.
        :rtype: str
        """
        if self.is_encapsulated:
            return '(' + str(self.compound_unit) + ')'
        elif self.is_pow:
            return str(self.base) + '**' + str(self.exponent)
        elif self.is_arithmetic_expression():
            t_lhs = (str(self.get_lhs()) if isinstance(self.get_lhs(), ASTUnitType) else self.get_lhs())
            if self.is_times:
                return str(t_lhs) + '*' + str(self.get_rhs())
            else:
                return str(t_lhs) + '/' + str(self.get_rhs())
        else:
            return self.unit

    def equals(self, other):
        """
        The equals method.
        :param other: a different object.
        :type other: object
        :return: True if equal, otherwise False.
        :rtype: bool
        """
        if not isinstance(other, ASTUnitType):
            return False
        if self.is_encapsulated + other.is_encapsulated == 1:
            return False
        if self.is_encapsulated and other.is_encapsulated and not self.compound_unit.equals(other.compound_unit):
            return False
        if self.is_pow + other.is_pow == 1:
            return False
        if self.is_pow and other.is_pow and \
                not (self.base.equals(other.base) and self.exponent == other.exponent):
            return False
        if self.is_arithmetic_expression() + other.is_arithmetic_expression() == 1:
            return False
        if self.is_arithmetic_expression() and other.is_arithmetic_expression() and \
                not (self.get_lhs().equals(other.lhs) and self.rhs.equals(other.rhs) and
                     self.is_times == other.is_times and self.is_div == other.is_div):
            return False
        if self.is_simple_unit() + other.is_simple_unit() == 1:
            return False
        if self.is_simple_unit() and other.is_simple_unit() and not self.unit == other.unit:
            return False
        return True
