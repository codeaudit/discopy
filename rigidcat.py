# -*- coding: utf-8 -*-

"""
Implements the free rigid monoidal category.

The objects are given by the free pregroup, the arrows by planar diagrams.

>>> unit, s, n = Ty(), Ty('s'), Ty('n')
>>> t = n.r @ s @ n.l
>>> assert t @ unit == t == unit @ t
>>> assert t.l.r == t == t.r.l
>>> left_snake, right_snake = Id(n.r).transpose_l(), Id(n.l).transpose_r()
>>> assert left_snake.normal_form() == Id(n) == right_snake.normal_form()
"""

import networkx as nx
from discopy import cat, moncat, config
from discopy.cat import AxiomError


class Ob(cat.Ob):
    """
    Implements simple pregroup types: basic types and their iterated adjoints.

    >>> a = Ob('a')
    >>> assert a.l.r == a.r.l == a and a != a.l.l != a.r.r
    """
    @property
    def z(self):
        """ Winding number """
        return self._z

    @property
    def l(self):
        """ Left adjoint """
        return Ob(self.name, self.z - 1)

    @property
    def r(self):
        """ Right adjoint """
        return Ob(self.name, self.z + 1)

    def __init__(self, name, z=0):
        if not isinstance(z, int):
            raise TypeError(config.Msg.type_err(int, z))
        self._z = z
        super().__init__(name)

    def __eq__(self, other):
        if not isinstance(other, Ob):
            return False
        return (self.name, self.z) == (other.name, other.z)

    def __repr__(self):
        return "Ob({}{})".format(
            repr(self.name), ", z=" + repr(self.z) if self.z else '')

    def __str__(self):
        return str(self.name) + (
            - self.z * '.l' if self.z < 0 else self.z * '.r')


class Ty(moncat.Ty):
    """ Implements pregroup types as lists of simple types.

    >>> s, n = Ty('s'), Ty('n')
    >>> assert n.l.r == n == n.r.l
    >>> assert (s @ n).l == n.l @ s.l and (s @ n).r == n.r @ s.r
    """
    @property
    def l(self):
        """ Left adjoint. """
        return Ty(*[x.l for x in self.objects[::-1]])

    @property
    def r(self):
        """ Right adjoint. """
        return Ty(*[x.r for x in self.objects[::-1]])

    def tensor(self, other):
        return Ty(*super().tensor(other))

    def __init__(self, *t):
        t = [x if isinstance(x, Ob) else Ob(x) for x in t]
        super().__init__(*t)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Ty(*super().__getitem__(key))
        return super().__getitem__(key)

    def __repr__(self):
        return "Ty({})".format(', '.join(
            repr(x if x.z else x.name) for x in self.objects))


class Diagram(moncat.Diagram):
    """ Implements diagrams in the free rigid monoidal category.

    >>> I, n, s = Ty(), Ty('n'), Ty('s')
    >>> Alice, jokes = Box('Alice', I, n), Box('jokes', I, n.r @ s)
    >>> boxes, offsets = [Alice, jokes, Cup(n, n.r)], [0, 1, 0]
    >>> print(Diagram(Alice.dom @ jokes.dom, s, boxes, offsets))
    Alice >> Id(n) @ jokes >> Cup(n, n.r) @ Id(s)
    """
    def __init__(self, dom, cod, boxes, offsets, _fast=False):
        if not isinstance(dom, Ty):
            raise TypeError(config.Msg.type_err(Ty, dom))
        if not isinstance(cod, Ty):
            raise TypeError(config.Msg.type_err(Ty, cod))
        super().__init__(dom, cod, boxes, offsets, _fast=_fast)

    def then(self, other):
        result = super().then(other)
        return Diagram(Ty(*result.dom), Ty(*result.cod),
                       result.boxes, result.offsets, _fast=True)

    def tensor(self, other):
        result = super().tensor(other)
        return Diagram(Ty(*result.dom), Ty(*result.cod),
                       result.boxes, result.offsets, _fast=True)

    def dagger(self):
        result = super().dagger()
        return Diagram(Ty(*result.dom), Ty(*result.cod),
                       result.boxes, result.offsets, _fast=True)

    @staticmethod
    def id(x):
        return Id(x)

    def draw(self, _test=False, _data=None):
        """
        Draws a diagram with cups and caps.
        """
        graph, positions, labels = moncat.Diagram.draw(self, _test=True)
        for i, (box, off) in enumerate(zip(self.boxes, self.offsets)):
            if isinstance(box, (Cup, Cap)):  # We draw cups and caps as wires.
                node, wire = 'box_{}'.format(i), 'wire_{}_{}'.format(i, off)
                positions[wire] = positions[node]
                del positions[node]
                del labels[node]
                graph = nx.relabel_nodes(graph, {node: wire})
        return super().draw(_test=_test, _data=(graph, positions, labels))

    @staticmethod
    def cups(x, y):
        """ Constructs nested cups witnessing adjointness of x and y

        >>> a, b = Ty('a'), Ty('b')
        >>> assert Diagram.cups(a, a.r) == Cup(a, a.r)
        >>> assert Diagram.cups(a @ b, (a @ b).r) ==\\
        ...     Id(a) @ Cup(b, b.r) @ Id(a.r) >> Cup(a, a.r)
        """
        if not isinstance(x, Ty):
            raise TypeError(config.Msg.type_err(Ty, x))
        if not isinstance(y, Ty):
            raise TypeError(config.Msg.type_err(Ty, y))
        cups = Id(x @ y)
        for i in range(len(x)):
            j = len(x) - i - 1
            cups = cups\
                >> Id(x[:j]) @ Cup(x[j:j + 1], y[i:i + 1]) @ Id(y[i + 1:])
        return cups

    @staticmethod
    def caps(x, y):
        """ Constructs nested cups witnessing adjointness of x and y

        >>> a, b = Ty('a'), Ty('b')
        >>> assert Diagram.caps(a, a.l) == Cap(a, a.l)
        >>> assert Diagram.caps(a @ b, (a @ b).l) == (Cap(a, a.l)
        ...                 >> Id(a) @ Cap(b, b.l) @ Id(a.l))
        """
        if not isinstance(x, Ty):
            raise TypeError(config.Msg.type_err(Ty, x))
        if not isinstance(y, Ty):
            raise TypeError(config.Msg.type_err(Ty, y))
        caps = Id(x @ y)
        for i in range(len(x)):
            j = len(x) - i - 1
            caps = caps\
                << Id(x[:j]) @ Cap(x[j:j + 1], y[i:i + 1]) @ Id(y[i + 1:])
        return caps

    def transpose_r(self):
        """
        >>> a, b = Ty('a'), Ty('b')
        >>> double_snake = Id(a @ b).transpose_r()
        >>> two_snakes = Id(b).transpose_r() @ Id(a).transpose_r()
        >>> double_snake == two_snakes
        False
        >>> *_, two_snakes_nf = moncat.Diagram.normalize(two_snakes)
        >>> assert double_snake == two_snakes_nf
        >>> f = Box('f', a, b)
        """
        return Diagram.caps(self.dom.r, self.dom) @ Id(self.cod.r)\
            >> Id(self.dom.r) @ self @ Id(self.cod.r)\
            >> Id(self.dom.r) @ Diagram.cups(self.cod, self.cod.r)

    def transpose_l(self):
        """
        >>> a, b = Ty('a'), Ty('b')
        >>> double_snake = Id(a @ b).transpose_l()
        >>> two_snakes = Id(b).transpose_l() @ Id(a).transpose_l()
        >>> double_snake == two_snakes
        False
        >>> *_, two_snakes_nf = moncat.Diagram.normalize(two_snakes, left=True)
        >>> assert double_snake == two_snakes_nf
        >>> f = Box('f', a, b)
        """
        return Id(self.cod.l) @ Diagram.caps(self.dom, self.dom.l)\
            >> Id(self.cod.l) @ self @ Id(self.dom.l)\
            >> Diagram.cups(self.cod.l, self.cod) @ Id(self.dom.l)

    def interchange(self, i, j, left=False):
        """
        >>> x, y = Ty('x'), Ty('y')
        >>> f = Box('f', x.r, y.l)
        >>> d = (f @ f.dagger()).interchange(0, 1)
        >>> assert d == Id(x.r) @ f.dagger() >> f @ Id(x.r)
        >>> print((Cup(x, x.r) >> Cap(x, x.l)).interchange(0, 1))
        Cap(x, x.l) @ Id(x @ x.r) >> Id(x @ x.l) @ Cup(x, x.r)
        >>> print((Cup(x, x.r) >> Cap(x, x.l)).interchange(0, 1, left=True))
        Id(x @ x.r) @ Cap(x, x.l) >> Cup(x, x.r) @ Id(x @ x.l)
        """
        result = super().interchange(i, j, left=left)
        return Diagram(Ty(*result.dom), Ty(*result.cod),
                       result.boxes, result.offsets, _fast=True)

    def normalize(self, left=False):
        """
        Return a generator which yields normalization steps.

        >>> n, s = Ty('n'), Ty('s')
        >>> cup, cap = Cup(n, n.r), Cap(n.r, n)
        >>> f, g, h = Box('f', n, n), Box('g', s @ n, n), Box('h', n, n @ s)
        >>> diagram = g @ cap >> f.dagger() @ Id(n.r) @ f >> cup @ h
        >>> for d in diagram.normalize(): print(d)  # doctest: +ELLIPSIS
        g >> f.dagger() >> ... >> Cup(n, n.r) @ Id(n) >> h
        g >> f.dagger() >> Id(n) @ Cap(n.r, n) >> Cup(n, n.r) @ Id(n) >> f >> h
        g >> f.dagger() >> f >> h
        """
        def follow_wire(diagram, i, j):
            """
            Given a diagram, the index of a box i and the offset j of an output
            wire, returns (i, j, obstructions) where:
            - i is the index of the box which takes this wire as input, or
            len(diagram) if it is connected to the bottom boundary.
            - j is the offset of the wire at its bottom end.
            - obstructions is a pair of lists of indices for the diagrams on
            the left and right of the wire we followed.
            """
            left_obstruction, right_obstruction = [], []
            while i < len(diagram) - 1:
                i += 1
                box, off = diagram.boxes[i], diagram.offsets[i]
                if off <= j < off + len(box.dom):
                    return i, j, (left_obstruction, right_obstruction)
                if off <= j:
                    j += len(box.cod) - len(box.dom)
                    left_obstruction.append(i)
                else:
                    right_obstruction.append(i)
            return len(diagram), j, (left_obstruction, right_obstruction)

        def find_move(diagram):
            """
            Given a diagram, returns (cup, cap, obstructions, left_snake)
            if there is a yankable pair, otherwise returns None.
            """
            for cap in range(len(diagram)):
                if not isinstance(diagram.boxes[cap], Cap):
                    continue
                for left_snake, wire in [(True, diagram.offsets[cap]),
                                         (False, diagram.offsets[cap] + 1)]:
                    cup, wire, obstructions =\
                        follow_wire(diagram, cap, wire)
                    not_yankable =\
                        cup == len(diagram)\
                        or not isinstance(diagram.boxes[cup], Cup)\
                        or left_snake and diagram.offsets[cup] + 1 != wire\
                        or not left_snake and diagram.offsets[cup] != wire
                    if not_yankable:
                        continue
                    return cup, cap, obstructions, left_snake
            return None

        def move(diagram, cup, cap, obstructions, left_snake=False):
            """
            Given a diagram and the indices for a cup and cap pair
            and a pair of lists of obstructions on the left and right,
            returns a new diagram with the snake removed.

            A left snake is one of the form Id @ Cap >> Cup @ Id.
            A right snake is one of the form Cap @ Id >> Id @ Cup.
            """
            left_obstruction, right_obstruction = obstructions
            if left_snake:
                for box in left_obstruction:
                    diagram = diagram.interchange(box, cap)
                    yield diagram
                    for i, right_box in enumerate(right_obstruction):
                        if right_box < box:
                            right_obstruction[i] += 1
                    cap += 1
                for box in right_obstruction[::-1]:
                    diagram = diagram.interchange(box, cup)
                    yield diagram
                    cup -= 1
            else:
                for box in left_obstruction[::-1]:
                    diagram = diagram.interchange(box, cup)
                    yield diagram
                    for i, right_box in enumerate(right_obstruction):
                        if right_box > box:
                            right_obstruction[i] -= 1
                    cup -= 1
                for box in right_obstruction:
                    diagram = diagram.interchange(box, cap)
                    yield diagram
                    cap += 1
            boxes = diagram.boxes[:cap] + diagram.boxes[cup + 1:]
            offsets = diagram.offsets[:cap] + diagram.offsets[cup + 1:]
            yield Diagram(diagram.dom, diagram.cod, boxes, offsets, _fast=True)

        diagram = self
        while True:
            yankable = find_move(diagram)
            if yankable is None:
                break
            for _diagram in move(diagram, *yankable):
                yield _diagram
                diagram = _diagram
        for _diagram in moncat.Diagram.normalize(diagram, left=left):
            yield _diagram

    def normal_form(self, left=False):
        """
        Implements the normalisation of rigid monoidal categories,
        see arxiv:1601.05372, definition 2.12.
        """
        return moncat.Diagram.normal_form(self, left=left)


class Box(moncat.Box, Diagram):
    """ Implements generators of rigid monoidal diagrams.

    >>> a, b = Ty('a'), Ty('b')
    >>> Box('f', a, b.l @ b, data={42})
    Box('f', Ty('a'), Ty(Ob('b', z=-1), 'b'), data={42})
    """
    def __init__(self, name, dom, cod, data=None, _dagger=False):
        """
        >>> a, b = Ty('a'), Ty('b')
        >>> Box('f', a, b.l @ b)
        Box('f', Ty('a'), Ty(Ob('b', z=-1), 'b'))
        """
        moncat.Box.__init__(self, name, dom, cod, data=data, _dagger=_dagger)
        Diagram.__init__(self, dom, cod, [self], [0], _fast=True)


class Id(Diagram):
    """ Define an identity arrow in a free rigid category

    >>> t = Ty('a', 'b', 'c')
    >>> assert Id(t) == Diagram(t, t, [], [])
    """
    def __init__(self, t):
        super().__init__(t, t, [], [], _fast=True)

    def __repr__(self):
        """
        >>> Id(Ty('n'))
        Id(Ty('n'))
        """
        return "Id({})".format(repr(self.dom))

    def __str__(self):
        """
        >>> n = Ty('n')
        >>> print(Id(n))
        Id(n)
        """
        return "Id({})".format(str(self.dom))


class Cup(Box):
    """ Defines cups for simple types.

    >>> n = Ty('n')
    >>> Cup(n, n.r)
    Cup(Ty('n'), Ty(Ob('n', z=1)))
    """
    def __init__(self, x, y):
        if not isinstance(x, Ty):
            raise TypeError(config.Msg.type_err(Ty, x))
        if not isinstance(y, Ty):
            raise TypeError(config.Msg.type_err(Ty, y))
        if x.r != y and x != y.r:
            raise AxiomError(config.Msg.are_not_adjoints(x, y))
        if len(x) != 1 or len(y) != 1:
            raise ValueError(config.Msg.cup_vs_cups(x, y))
        if x == y.r:
            raise NotImplementedError(config.Msg.pivotal_not_implemented())
        super().__init__('Cup', x @ y, Ty())

    def dagger(self):
        raise NotImplementedError(config.Msg.pivotal_not_implemented())

    def __repr__(self):
        """
        >>> n = Ty('n')
        >>> assert repr(Cup(n, n.r)) == "Cup(Ty('n'), Ty(Ob('n', z=1)))"
        """
        return "Cup({}, {})".format(repr(self.dom[:1]), repr(self.dom[1:]))

    def __str__(self):
        """
        >>> n = Ty('n')
        >>> assert str(Cup(n, n.r)) == "Cup(n, n.r)"
        """
        return "Cup({}, {})".format(self.dom[:1], self.dom[1:])


class Cap(Box):
    """ Defines cups for simple types.

    >>> n = Ty('n')
    >>> print(Cap(n, n.l).cod)
    n @ n.l
    >>> print(Cap(n.l, n.l.l).cod)
    n.l @ n.l.l
    """
    def __init__(self, x, y):
        if not isinstance(x, Ty):
            raise TypeError(config.Msg.type_err(Ty, x))
        if not isinstance(y, Ty):
            raise TypeError(config.Msg.type_err(Ty, y))
        if x != y.r and x.r != y:
            raise AxiomError(config.Msg.are_not_adjoints(x, y))
        if len(x) != 1 or len(y) != 1:
            raise ValueError(config.Msg.cap_vs_caps(x, y))
        if x.r == y:
            raise NotImplementedError(config.Msg.pivotal_not_implemented())
        super().__init__('Cap', Ty(), x @ y)

    def dagger(self):
        raise NotImplementedError(config.Msg.pivotal_not_implemented())

    def __repr__(self):
        """
        >>> n = Ty('n')
        >>> Cap(n, n.l)
        Cap(Ty('n'), Ty(Ob('n', z=-1)))
        """
        return "Cap({}, {})".format(repr(self.cod[:1]), repr(self.cod[1:]))

    def __str__(self):
        """
        >>> n = Ty('n')
        >>> print(Cap(n, n.l))
        Cap(n, n.l)
        """
        return "Cap({}, {})".format(self.cod[:1], self.cod[1:])


class RigidFunctor(moncat.MonoidalFunctor):
    """
    Implements rigid monoidal functors, i.e. preserving cups and caps.

    >>> s, n = Ty('s'), Ty('n')
    >>> Alice, Bob = Box("Alice", Ty(), n), Box("Bob", Ty(), n)
    >>> loves = Box('loves', Ty(), n.r @ s @ n.l)
    >>> love_box = Box('loves', n @ n, s)
    >>> ob = {s: s, n: n}
    >>> ar = {Alice: Alice, Bob: Bob}
    >>> ar.update({loves: Cap(n.r, n) @ Cap(n, n.l)
    ...                   >> Id(n.r) @ love_box @ Id(n.l)})
    >>> F = RigidFunctor(ob, ar)
    >>> sentence = Alice @ loves @ Bob >> Cup(n, n.r) @ Id(s) @ Cup(n.l, n)
    >>> assert F(sentence).normal_form() == Alice >> Id(n) @ Bob >> love_box
    """
    def __init__(self, ob, ar, ob_cls=Ty, ar_cls=Diagram):
        """
        >>> F = RigidFunctor({Ty('x'): Ty('y')}, {})
        >>> F(Id(Ty('x')))
        Id(Ty('y'))
        """
        super().__init__(ob, ar, ob_cls=ob_cls, ar_cls=ar_cls)

    def __repr__(self):
        """
        >>> RigidFunctor({Ty('x'): Ty('y')}, {})
        RigidFunctor(ob={Ty('x'): Ty('y')}, ar={})
        """
        return super().__repr__().replace("MonoidalFunctor", "RigidFunctor")

    def __call__(self, diagram):
        """
        >>> x, y, z = Ty('x'), Ty('y'), Ty('z')
        >>> f, g = Box('f', x, y), Box('g', y, z)
        >>> F = RigidFunctor({x: y, y: z}, {f: g})
        >>> assert F(f.transpose_l()) == F(f).transpose_l()
        >>> assert F(f.transpose_r()) == F(f).transpose_r()
        """
        if isinstance(diagram, Ob):
            result = self.ob[Ty(diagram.name)]
            if diagram.z < 0:
                for _ in range(-diagram.z):
                    result = result.l
            elif diagram.z > 0:
                for _ in range(diagram.z):
                    result = result.r
            return result
        if isinstance(diagram, Ty):
            return sum([self(b) for b in diagram.objects], self.ob_cls())
        if isinstance(diagram, Cup):
            return self.ar_cls.cups(self(diagram.dom[0]), self(diagram.dom[1]))
        if isinstance(diagram, Cap):
            return self.ar_cls.caps(self(diagram.cod[0]), self(diagram.cod[1]))
        if isinstance(diagram, Diagram):
            return super().__call__(diagram)
        raise TypeError(config.Msg.type_err(Diagram, diagram))
