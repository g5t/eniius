from zenlog import log
from dataclasses import dataclass
from mccode.instr import DependentOrientation, OrientationParts, OrientationPart
from nexusformat.nexus import NXfield

@dataclass
class NXOrientation:
    o: OrientationPart

    def translation(self, dep: str) -> NXfield:
        from mccode.instr import RotationPart
        if isinstance(self.o, RotationPart):
            raise RuntimeError('OrientationPart is a rotation!')
        pos = self.o.position()
        norm = pos.length()
        vec = [p if norm.is_zero else p / norm for p in pos]
        return NXfield(norm, vector=vec, depends_on=dep, transformation_type='translation', units='m')

    def rotation(self, dep: str) -> NXfield:
        from mccode.instr import TranslationPart
        if isinstance(self.o, TranslationPart):
            raise RuntimeError('OrientationPart is a translation')
        axis, angle, angle_unit = self.o.rotation_axis_angle
        # handle the case where angle is not a constant?
        return NXfield(angle, vector=axis, depends_on=dep, transformation_type='rotation', units=angle_unit)

    def transformations(self, name: str, dep: str = None) -> list[tuple[str, NXfield]]:
        if self.o.is_translation and self.o.is_rotation:
            return [(f'{name}_t', self.translation(dep)), (f'{name}_r', self.rotation(f'{name}_t'))]
        elif self.o.is_translation:
            return [(name, self.translation(dep))]
        elif self.o.is_rotation:
            return [(name, self.rotation(dep))]
        else:
            return []


@dataclass
class NXOrientationChain:
    oc: OrientationParts

    def transformations(self, name: str) -> list[tuple[str, NXfield]]:
        nxt = []
        dep = '.'
        for index, o in enumerate(self.oc.stack()):
            nxt.extend(NXOrientation(o).transformations(f'{name}_{index}', dep))
            dep = nxt[-1][0] if len(nxt[-1]) else '.'
        return nxt


@dataclass
class NXDependentOrientation:
    do: DependentOrientation

    def transformations(self, name: str) -> dict[str, NXfield]:
        # collapse all possible chained orientation information
        orientations = self.do.combine().reduce()
        if not orientations:
            # Absolute positioning (or no positioning)
            return {}
        # make an ordered list of the requisite NXfield entries
        nxt = NXOrientationChain(orientations).transformations(name)
        return {k: v for k, v in nxt}
