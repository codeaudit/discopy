# -*- coding: utf-8 -*-

"""
discopy computes natural language meaning in pictures.

>>> s, n = Ty('s'), Ty('n')
>>> Alice, Bob = Word('Alice', n), Word('Bob', n)
>>> loves = Word('loves', n.r @ s @ n.l)
>>> grammar = Cup(n, n.r) @ Id(s) @ Cup(n.l, n)
>>> print(Alice @ loves @ Bob >> grammar)
Alice >> Id(n) @ loves >> Id(n @ n.r @ s @ n.l) @ Bob
"""

from discopy import cat, moncat, matrix, circuit, disco, config
from discopy.cat import Quiver
from discopy.moncat import MonoidalFunctor
from discopy.matrix import Dim, Matrix, MatrixFunctor
from discopy.circuit import PRO, Circuit, Gate, Bra, Ket, CircuitFunctor
from discopy.pregroup import Ob, Ty, Box, Diagram, Id, Cup, Cap
from discopy.disco import Word, Model, CircuitModel

__version__ = config.VERSION
