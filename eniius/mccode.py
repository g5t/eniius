from zenlog import log
from dataclasses import dataclass, field
from typing import Union
from mccode.instr import Instr, Instance, DependentOrientation, OrientationParts, OrientationPart
from mccode.common import Expr, unary_expr
from nexusformat.nexus import NXfield

def norm_value(v: tuple[Expr, Expr, Expr]):
    from math import sqrt
    if v[0].is_zero and v[1].is_zero:
        return unary_expr(abs, 'abs', v[2])
    if v[1].is_zero and v[2].is_zero:
        return unary_expr(abs, 'abs', v[0])
    if v[0].is_zero and v[2].is_zero:
        return unary_expr(abs, 'abs', v[1])
    return unary_expr(sqrt, 'sqrt', v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


@dataclass
class NXOrientation:
    o: OrientationPart

    def translation(self, dep: str) -> NXfield:
        from mccode.instr import RotationPart
        if isinstance(self.o, RotationPart):
            raise RuntimeError('OrientationPart is a rotation!')
        pos = self.o.position()
        norm = norm_value(pos) if any(not x.is_zero for x in pos) else Expr.float(0)
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
            nxt.extend(o.transformations(f'{name}_{index}', dep))
            dep = nxt[-1][0]
        return nxt


@dataclass
class NXDependentOrientation:
    do: DependentOrientation

    def transformations(self, name: str) -> dict[str, NXfield]:
        # collapse all possible chained orientation information
        orientations = self.do.combine().reduce()
        # make an ordered list of the requisite NXfield entries
        nxt = NXOrientationChain(orientations).transformations(name)
        return {k: v for k, v in nxt}


COMPONENT_GROUP_TO_NEXUS = dict(Guide='NXguide', Collimator='NXcollimator')
COMPONENT_CATEGORY_TO_NEXUS = dict(sources='NXmoderator', monitors='NXdetector')
COMPONENT_TYPE_NAME_TO_NEXUS = dict(
    DiskChopper='NXdisk_chopper',
    FermiChopper='NXfermi_chopper',
    FermiChopper_ILL='NXfermi_chopper',
    Fermi_chop2a='NXfermi_chopper',
    Filter_gen='NXfilter',
    Filter_graphite='NXfilter',
    Elliptic_guide_gravity='NXguide',
    Mirror='NXmirror',
    Monochromator_flat='NXmonochromator',
    Monochromator_curved='NXmonochromator',
    Monochromator_pol='NXpolarizer',
    Pol_SF_ideal='NXflipper',
    Pol_bender='NXpolarizer',
    Pol_mirror='NXpolarizer',
    SNS_source='NXmoderator',
    SNS_source_analytic='NXmoderator',
    Source_pulsed='NXmoderator',
    Selector='NXvelocity_selector',
    V_selector='NXvelocity_selector',
    ViewModISIS='NXmoderator',
)
# Each entry here maps a NeXus component to a McStas component
# The second element is a mapping of NeXus component parameters to McStas parameters
# The third element is a mapping of NeXus component parameters to McStas position paramters
NEXUS_TO_COMPONENT = dict(
    NXaperture=['Slit', {'x_gap': 'xwidth', 'y_gap': 'yheight'}, ],
    NXcollimator=['Collimator_linear', {'divergence_x': 'divergence', 'divergence_y': 'divergenceV'}, ],
    NXdetector=['Monitor_nD', {}, ],
    NXdisk_chopper=['DiskChopper', {'slits': 'nslit', 'rotation_speed': 'nu', 'radius': 'radius', 'slit_angle': 'theta_0', 'slit_height': 'yheight', 'phase': 'phase'}, ],
    NXfermi_chopper=['FermiChopper', {'rotation_speed': 'nu', 'radius': 'radius', 'slit': 'w', 'r_slit': 'curvature', 'number': 'nslit', 'width': 'xwidth', 'height': 'yheight'}, {'distance': 'set_AT'}, ],
    NXguide=['Guide', {'m_value': 'm'}, ],
    NXslit=['Slit', {'x_gap': 'xwidth', 'y_gap': 'yheight'}, ],
    NXsample=['Incoherent', {}, ],
    NXmoderator=['Moderator', {}, {'distance': 'set_AT'}, ]
)


@dataclass
class NXInstance:
    obj: Instance
    index: int
    transforms: dict[str, NXfield]
    only_nx: bool
    nx: Union[None, dict, NXfield] = None

    def __post_init__(self):
        from json import dumps
        from eniius.utils import outer_transform_dependency, mccode_component_eniius_data
        self.nx = getattr(self, self.obj.type.name, self.default_translation)()
        self.nx['mcstas'] = dumps({'instance': str(self.obj), 'order': self.index})
        self.nx['transformations'] = self.transforms
        most_dependent = outer_transform_dependency(self.transforms)
        for name, insert in mccode_component_eniius_data(self.obj, only_nx=self.only_nx).items():
            self.nx[name] = insert
            if not hasattr(self.nx[name], 'depends_on'):
                self.nx[name].attrs['depends_on'] = most_dependent
            most_dependent = outer_transform_dependency(self.nx['transformations'])
        self.nx['depends_on'] = f'transformations/{most_dependent}'

    def get_nx_type(self):
        if self.obj.type.name in COMPONENT_TYPE_NAME_TO_NEXUS:
            return COMPONENT_TYPE_NAME_TO_NEXUS[self.obj.type.name]
        elif self.obj.type.category in COMPONENT_CATEGORY_TO_NEXUS:
            return COMPONENT_CATEGORY_TO_NEXUS[self.obj.type.category]
        if any(self.obj.type.name.startswith(x) for x in COMPONENT_GROUP_TO_NEXUS):
            return [t for k, t in COMPONENT_GROUP_TO_NEXUS.items() if self.obj.type.name.startswith(k)][0]
        return 'NXnote'

    def default_translation(self):
        import nexusformat.nexus as nexus
        nx_type = self.get_nx_type()
        nx_2_mc = NEXUS_TO_COMPONENT.get(nx_type, ({}, {}))[1]
        return getattr(nexus, nx_type)(**{n: self.obj.get_parameter(m).value for n, m in nx_2_mc.items()})

    def Slit(self):
        """The Slit component _must_ define (xmin, xmax) _or_ xwidth, and similarly the y-named parameters"""
        from nexusformat.nexus import NXslit
        from eniius.utils import mccode_component_eniius_data
        if self.obj.defines_parameter('xwidth'):
            x_gap = self.obj.get_parameter('xwidth').value
            x_zero = Expr.float(0)
        else:
            x_gap = (self.obj.get_parameter('xmax') - self.obj.get_parameter('xmin')).value
            x_zero = self.obj.get_parameter('xmax') + self.obj.get_parameter('xmin')
        if self.obj.defines_parameter('ywidth'):
            y_gap = self.obj.get_parameter('ywidth').value
            y_zero = Expr.float(0)
        else:
            y_gap = (self.obj.get_parameter('ymax') - self.obj.get_parameter('ymin')).value
            y_zero = self.obj.get_parameter('ymax') + self.obj.get_parameter('ymin')

        if not (x_zero.is_zero and y_zero.is_zero) and len(mccode_component_eniius_data(self.obj)) == 0:
            log.warn(f'{self.obj.name} should be translated by [{x_zero}, {y_zero}, 0] via eniius_data METADATA')
        return NXslit(x_gap=x_gap, y_gap=y_gap)

    def Guide(self):
        from nexusformat.nexus import NXguide
        from eniius.nxoff import NXoff
        off_pars = {k: self.obj.get_parameter(k).value for k in ('l', 'w1', 'h1', 'w2', 'h2')}
        for k in ('w', 'h'):
            off_pars[f'{k}2'] = off_pars[f'{k}1'] if off_pars[f'{k}2'] == 0 else off_pars[f'{k}2']
        return NXguide(m_value=self.obj.get_parameter('m').value, geometry=NXoff.from_wedge(**off_pars).to_nexus())

    Guide_channeled = Guide
    Guide_gravity = Guide
    Guide_simple = Guide
    Guide_wavy = Guide

    def Collimator_linear(self):
        from nexusformat.nexus import NXcollimator
        from eniius.nxoff import NXoff
        pars = {k: self.obj.get_parameter(v).value for k, v in (('l', 'length'), ('w1', 'xwidth'), ('h1', 'yheight'))}
        return NXcollimator(divergence_x=self.obj.get_parameter('divergece').value,
                            divergence_y=self.obj.get_parameter('divergeceV').value,
                            geometry=NXoff.from_wedge(**pars).to_nexus())

    def DiskChopper(self):
        from nexusformat.nexus import NXdisk_chopper
        mpars = {k: self.obj.get_parameter(k).value for k in ('nslit', 'nu', 'radius', 'theta_0', 'phase', 'yheight')}
        pars = {'slits': mpars['nslit'],
                'rotation_speed': NXfield(mpars['nu'], units='Hz'),
                'radius': NXfield(mpars['radius'], units='m'),
                'slit_angle': NXfield(mpars['theta_0'], units='degrees'),
                'phase': NXfield(mpars['phase'], units='degrees'),
                'slit_height': NXfield(mpars['yheight'] if mpars['yheight'] else mpars['radius'], units='m')}
        nslit, delta = mpars['nslit'], mpars['delta'] / 2.0
        slit_edges = [y * 360.0 / nslit + x for y in range(nslit) for x in (-delta, delta)]
        return NXdisk_chopper(slit_edges=NXfield(slit_edges, units='degrees'), **pars)

    def Elliptic_guide_gravity(self):
        from nexusformat.nexus import NXguide
        from numpy import arange, sqrt
        from eniius.nxoff import NXoff
        if 'mid' not in self.obj.get_parameter('dimensionsAt').value:
            log.warn('Only midpoint geometry supported by Elliptic_guide_gravity translator')
            log.debug(f'The current guide has {self.obj.get_parameter("dimensionsAt")} specified')

        def ellipse_width(minor, distance, at):
            major = sqrt((distance / 2) ** 2 + minor ** 2)
            return 0 if abs(at) > major else minor * sqrt(1 - (at / major) ** 2)

        pars = dict(xw='xwidth', xi='linxw', xo='loutxw', yw='yheight', yi='linyh', yo='loutyh', l='l')
        p = {k: self.obj.get_parameter(v).value for k, v in pars.items()}
        n = 10
        rings = arange(n + 1) / n
        faces, vertices = [], []
        for x in rings:
            w = ellipse_width(p['xw'] / 2, p['xi'] + p['l'] + p['xo'], p['xi'] / 2 + (x - 0.5) * p['l'] - p['xo'] / 2)
            h = ellipse_width(p['yw'] / 2, p['yi'] + p['l'] + p['yo'], p['yi'] / 2 + (x - 0.5) * p['l'] - p['yo'] / 2)
            z = x * p['l']
            vertices.extend([[-w, -h, z], [-w, h, z], [w, h, z], [w, -h, z]])

        for i in range(n):
            j0, j1, j2, j3, j4, j5, j6, j7 = [4 * i + k for k in range(8)]
            faces.extend([[j0, j1, j5, j4], [j1, j2, j6, j5], [j2, j3, j7, j6], [j3, j0, j4, j7]])

        return NXguide(geometry=NXoff(vertices, faces).to_nexus())


@dataclass
class NXInstr:
    instrument: Instr

    def to_nx(self):
        # quick and very dirty:
        return NXfield(str(self.instrument))


@dataclass
class NXMcCode:
    instrument: Instr
    origin_name: str = None
    indexes: dict[str, int] = field(default_factory=dict)
    orientations: dict[str, DependentOrientation] = field(default_factory=dict)

    def __post_init__(self):
        from copy import deepcopy
        for index, instance in enumerate(self.instrument.components):
            self.indexes[instance.name] = index
            self.orientations[instance.name] = deepcopy(instance.orientation)
        # Attempt to re-center all component dependent orientations on the sample
        samples = [instance for instance in self.instrument.components if "samples" == instance.type.category]
        if not samples:
            log.warn('No "sample" category components in instrument, using ABSOLUTE positions')
        elif len(samples) > 1:
            log.warn(f'More than one "sample" category component. Using {samples[0].name} for origin name')
        if samples:
            self.origin_name = samples[0].name
            # find the inverse of the position _and_ rotation of the origin sample
            origin_offset = samples[0].orientation.inverse()
            # add this to all components (recentering on the origin)
            for item in self.orientations.items():
                item += origin_offset

    def transformations(self, name):
        return NXDependentOrientation(self.orientations[name]).transformations(name)

    def component(self, name, only_nx=True):
        """Return a NeXus NXcomponent corresponding to the named McStas component instance"""
        instance = self.instrument.components[self.indexes[name]]
        transformations = self.transformations(name)
        nx = NXInstance(instance, self.indexes[name], transformations, only_nx=only_nx)
        if nx.nx['transformations'] != transformations:
            # if the component modifed the transformations group, make sure we don't use our version again
            del self.orientations[name]
        return nx

    def instrument(self, only_nx=True):
        from nexusformat.nexus import NXinstrument
        nx = NXinstrument()  # this is a NeXus class
        nx['mcstas'] = NXInstr(self.instrument).to_nx()
        for name in self.indexes:
            nx[name] = self.component(name, only_nx=only_nx).nx

