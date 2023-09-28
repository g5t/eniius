from zenlog import log
from dataclasses import dataclass
from mccode.instr import Orient, OrientParts, OrientPart
from nexusformat.nexus import NXfield
from .instr import NXInstr

@dataclass
class NXOrientation:
    instr: NXInstr
    o: OrientPart

    def expr2nx(self, expr):
        return self.instr.expr2nx(expr)

    def make_nx(self, nx_class, *args, **kwargs):
        return self.instr.make_nx(nx_class, *args, **kwargs)

    def translation(self, dep: str) -> NXfield:
        from mccode.instr import RotationPart
        if isinstance(self.o, RotationPart):
            raise RuntimeError('OrientationPart is a rotation!')
        pos = self.o.position('coordinates')
        norm = pos.length()
        vec = [p if norm.is_zero else p / norm for p in pos]
        return self.make_nx(NXfield, norm, vector=vec, depends_on=dep, transformation_type='translation', units='m')

    def rotation(self, dep: str) -> NXfield:
        from mccode.instr import TranslationPart
        if isinstance(self.o, TranslationPart):
            raise RuntimeError('OrientationPart is a translation')
        try:
            axis, angle, angle_unit = self.o.rotation_axis_angle
        except RuntimeError as error:
            log.error(f'Failed to get rotation axis and angle: {error}')
            print(repr(self.o))
            raise NotImplementedError()

        print(f'rotation {axis}, {angle}')
        # handle the case where angle is not a constant?
        return self.make_nx(NXfield, angle, vector=axis, depends_on=dep, transformation_type='rotation', units=angle_unit)

    def transformations(self, name: str, dep: str = None) -> list[tuple[str, NXfield]]:
        if self.o.is_translation and self.o.is_rotation:
            print(f'NXOrientation {name} is a translation and a rotation')
            return [(f'{name}_t', self.translation(dep)), (f'{name}_r', self.rotation(f'{name}_t'))]
        elif self.o.is_translation:
            return [(name, self.translation(dep))]
        elif self.o.is_rotation:
            print(f'NXOrientation {name} is only a rotation')
            return [(name, self.rotation(dep))]
        else:
            return []


@dataclass
class NXOrientationChain:
    instr: NXInstr
    oc: OrientParts

    def transformations(self, name: str) -> list[tuple[str, NXfield]]:
        nxt = []
        dep = '.'
        for index, o in enumerate(self.oc.stack()):
            nxt.extend(NXOrientation(self.instr, o).transformations(f'{name}_{index}', dep))
            dep = nxt[-1][0] if len(nxt[-1]) else '.'
        return nxt


@dataclass
class NXOrient:
    instr: NXInstr
    do: Orient

    def transformations(self, name: str) -> dict[str, NXfield]:
        # collapse all possible chained orientation information
        orientations = self.do.combine().reduce()
        if not orientations:
            # Absolute positioning (or no positioning)
            return {}
        # make an ordered list of the requisite NXfield entries
        nxt = NXOrientationChain(self.instr, orientations).transformations(name)
        return {k: v for k, v in nxt}
