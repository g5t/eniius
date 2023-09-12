from zenlog import log
from dataclasses import dataclass, field
from mccode.instr import Instr, DependentOrientation


@dataclass
class NXMcCode:
    instr: Instr
    origin_name: str = None
    indexes: dict[str, int] = field(default_factory=dict)
    orientations: dict[str, DependentOrientation] = field(default_factory=dict)

    def __post_init__(self):
        from copy import deepcopy
        for index, instance in enumerate(self.instr.components):
            self.indexes[instance.name] = index
            self.orientations[instance.name] = deepcopy(instance.orientation)
            print(f'Component instance # {index} -- {instance.name}')
            print(instance.orientation)
            print(self.orientations[instance.name])
        # Attempt to re-center all component dependent orientations on the sample
        samples = [instance for instance in self.instr.components if "samples" == instance.type.category]
        if not samples:
            log.warn('No "sample" category components in instrument, using ABSOLUTE positions')
        elif len(samples) > 1:
            log.warn(f'More than one "sample" category component. Using {samples[0].name} for origin name')
        if samples:
            self.origin_name = samples[0].name
            # find the inverse of the position _and_ rotation of the origin sample
            origin_offset = samples[0].orientation.inverse()
            # add this to all components (recentering on the origin)
            for name in self.orientations:
                self.orientations[name] = self.orientations[name] + origin_offset

    def transformations(self, name):
        from .orientation import NXDependentOrientation
        return NXDependentOrientation(self.orientations[name]).transformations(name)

    def component(self, name, only_nx=True):
        """Return a NeXus NXcomponent corresponding to the named McStas component instance"""
        from .instance import NXInstance
        instance = self.instr.components[self.indexes[name]]
        transformations = self.transformations(name)
        nx = NXInstance(instance, self.indexes[name], transformations, only_nx=only_nx)
        if transformations and nx.nx['transformations'] != transformations:
            # if the component modifed the transformations group, make sure we don't use our version again
            del self.orientations[name]
        return nx

    def instrument(self, only_nx=True):
        from .instr import NXInstr
        from nexusformat.nexus import NXinstrument
        nx = NXinstrument()  # this is a NeXus class
        nx['mcstas'] = NXInstr(self.instr).to_nx()
        for name in self.indexes:
            nx[name] = self.component(name, only_nx=only_nx).nx

        return nx
