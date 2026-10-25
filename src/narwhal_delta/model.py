"""Bounded, finite, metre-based survey contracts."""
from dataclasses import dataclass, asdict
import hashlib, json, math

MAX_POINTS = 200_000
MAX_CELLS = 80_000
MAX_BYTES = 32 * 1024 * 1024

def number(value, name, lo=-1e7, hi=1e7):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi or not math.isfinite(value):
        raise ValueError(f'{name} must be finite and between {lo} and {hi}.')
    return float(value)

def label(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise ValueError(f'{name} must be 1–160 characters.')
    return value.strip()

@dataclass(frozen=True)
class Survey:
    name: str
    frame_id: str
    vertical_datum: str
    points: tuple
    synthetic: bool = False
    source: str = 'survey.json'
    source_sha256: str = ''

    def __post_init__(self):
        for key in ('name', 'frame_id', 'vertical_datum', 'source'):
            object.__setattr__(self, key, label(getattr(self, key), key))
        if not isinstance(self.synthetic, bool): raise ValueError('synthetic must be a boolean.')
        if not 1 <= len(self.points) <= MAX_POINTS: raise ValueError(f'Surveys need 1–{MAX_POINTS:,} points.')
        clean=[]
        for p in self.points:
            if not isinstance(p, (list, tuple)) or len(p) != 3: raise ValueError('Each point must be [x, y, z].')
            clean.append(tuple(number(v, 'coordinate') for v in p))
        object.__setattr__(self, 'points', tuple(clean))

    def document(self):
        return {'schema':'narwhal.survey/1','name':self.name,'frame_id':self.frame_id,
                'vertical_datum':self.vertical_datum,'units':'m','z_positive':'up',
                'synthetic':self.synthetic,'points':self.points,
                'provenance':{'source':self.source,'source_sha256':self.source_sha256}}

    def identity(self):
        return hashlib.sha256(json.dumps(self.document(), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class Settings:
    cell_size: float = 0.5
    min_points: int = 3
    sigma_a: float = 0.025
    sigma_b: float = 0.025
    sigma_alignment: float = 0.02
    min_change: float = 0.08
    confidence: float = 1.96
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    yaw_deg: float = 0.0
    roi: object = None
    control: object = None

    def __post_init__(self):
        for key,lo,hi in [('cell_size',.1,5),('sigma_a',0,5),('sigma_b',0,5),('sigma_alignment',0,5),
                          ('min_change',0,10),('dx',-100,100),('dy',-100,100),('dz',-100,100),('yaw_deg',-180,180)]:
            object.__setattr__(self,key,number(getattr(self,key),key,lo,hi))
        if isinstance(self.min_points,bool) or not isinstance(self.min_points,int) or not 1 <= self.min_points <= 100:
            raise ValueError('min_points must be an integer from 1 to 100.')
        if isinstance(self.confidence,bool) or self.confidence not in (1.0,1.96,2.576): raise ValueError('confidence must be 1, 1.96 or 2.576.')
        for key in ('roi','control'):
            box=getattr(self,key)
            if box is not None:
                if not isinstance(box,(list,tuple)) or len(box)!=4: raise ValueError(f'{key} needs [xmin, ymin, xmax, ymax].')
                box=tuple(number(v,key) for v in box)
                if box[0]>=box[2] or box[1]>=box[3]: raise ValueError(f'{key} bounds must increase.')
                object.__setattr__(self,key,box)

    def document(self): return asdict(self)
