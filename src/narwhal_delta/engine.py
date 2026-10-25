"""Median DEM differencing. No interpolation, inferred CRS or hidden registration."""
from collections import defaultdict, deque
from statistics import median
import hashlib, json, math
from .model import Settings, MAX_CELLS
from . import __version__


def in_box(x,y,box): return box is None or box[0]<=x<box[2] and box[1]<=y<box[3]

def transform(points,s):
    t=math.radians(s.yaw_deg);c=math.cos(t);sn=math.sin(t)
    return [(c*x-sn*y+s.dx,sn*x+c*y+s.dy,z+s.dz) for x,y,z in points]

def grid(points,s):
    buckets=defaultdict(list)
    for x,y,z in points:
        key=(math.floor(x/s.cell_size),math.floor(y/s.cell_size))
        buckets[key].append(z)
        if len(buckets)>MAX_CELLS: raise ValueError(f'Grid exceeds {MAX_CELLS:,} occupied cells; use larger cells.')
    result={}
    for key,values in buckets.items():
        z=median(values);mad=median(abs(v-z) for v in values)
        result[key]={'z':z,'n':len(values),'roughness':1.4826*mad}
    return result

def components(cells,area):
    lookup={(c['i'],c['j']):c for c in cells if c['state'] in ('gain','loss')}
    regions=[]
    for key in sorted(lookup):
        if lookup[key].get('_seen'): continue
        first=lookup[key];kind=first['state'];queue=deque([key]);first['_seen']=True;group=[]
        while queue:
            ij=queue.popleft();c=lookup[ij];group.append(c)
            for q in ((ij[0]+1,ij[1]),(ij[0]-1,ij[1]),(ij[0],ij[1]+1),(ij[0],ij[1]-1)):
                nxt=lookup.get(q)
                if nxt and not nxt.get('_seen') and nxt['state']==kind:
                    nxt['_seen']=True;queue.append(q)
        peak=max(group,key=lambda c:abs(c['delta']))
        regions.append({'kind':kind,'cells':len(group),'area':len(group)*area,
                        'volume':sum(c['delta']*area for c in group),
                        'peak':peak['delta'],'x':peak['x'],'y':peak['y'],
                        'bounds':[min(c['x'] for c in group),min(c['y'] for c in group),max(c['x'] for c in group),max(c['y'] for c in group)]})
    for c in lookup.values(): c.pop('_seen',None)
    regions.sort(key=lambda r:abs(r['volume']),reverse=True)
    for i,r in enumerate(regions): r['id']=f'D-{i+1:03d}'
    return regions

def compare(a,b,s=Settings()):
    if (a.frame_id,a.vertical_datum)!=(b.frame_id,b.vertical_datum):
        raise ValueError('Frame ID and vertical datum must match. Delta never infers a coordinate conversion.')
    ga=grid(a.points,s);gb=grid(transform(b.points,s),s);keys=sorted(ga.keys()|gb.keys())
    if len(keys)>MAX_CELLS: raise ValueError('Combined grid exceeds occupied-cell limit.')
    if keys:
        width=max(k[0] for k in keys)-min(k[0] for k in keys)+1
        height=max(k[1] for k in keys)-min(k[1] for k in keys)+1
        if width*height>MAX_CELLS: raise ValueError('Grid bounding rectangle exceeds 80,000 cells; crop surveys or enlarge cells.')
    correction=0.0;control_count=0;control_mad=None
    if s.control:
        offsets=[gb[k]['z']-ga[k]['z'] for k in sorted(ga.keys()&gb.keys())
                 if min(ga[k]['n'],gb[k]['n'])>=s.min_points and in_box((k[0]+.5)*s.cell_size,(k[1]+.5)*s.cell_size,s.control)]
        if len(offsets)<10: raise ValueError('Stable control requires at least 10 sufficiently sampled shared cells.')
        correction=-median(offsets);control_count=len(offsets)
        control_mad=1.4826*median(abs(v+correction) for v in offsets)
    cells=[];area=s.cell_size**2
    counts={k:0 for k in ('gain','loss','below_threshold','insufficient','only_a','only_b','outside_roi')}
    raw_net=gain=loss=envelope=0.0;shared=0
    for i,j in keys:
        x=(i+.5)*s.cell_size;y=(j+.5)*s.cell_size;aa=ga.get((i,j));bb=gb.get((i,j))
        c={'i':i,'j':j,'x':x,'y':y,'a':aa['z'] if aa else None,'b':bb['z']+correction if bb else None,
           'n_a':aa['n'] if aa else 0,'n_b':bb['n'] if bb else 0,'delta':None,'sigma':None,'lod':None}
        if not in_box(x,y,s.roi): state='outside_roi'
        elif aa is None: state='only_b'
        elif bb is None: state='only_a'
        elif min(aa['n'],bb['n'])<s.min_points: state='insufficient'
        else:
            shared+=1;d=c['b']-c['a']
            sigma=math.sqrt(s.sigma_a**2+s.sigma_b**2+aa['roughness']**2+bb['roughness']**2+s.sigma_alignment**2)
            lod=max(s.min_change,s.confidence*sigma)
            c.update(delta=d,sigma=sigma,lod=lod)
            state='gain' if d>lod else 'loss' if d < -lod else 'below_threshold'
            raw_net+=d*area;envelope+=lod*area
            if state=='gain': gain+=d*area
            if state=='loss': loss-=d*area
        c['state']=state;counts[state]+=1;cells.append(c)
    regions=components(cells,area)
    stats={'counts':counts,'shared_cells':shared,'shared_area':shared*area,'changed_area':(counts['gain']+counts['loss'])*area,
           'gain_volume':gain,'loss_volume':loss,'net_thresholded_volume':gain-loss,'net_raw_volume':raw_net,
           'threshold_envelope_volume':envelope,
           'overlap_fraction':shared/max(1,len(cells)-counts['outside_roi']),
           'median_lod':median(c['lod'] for c in cells if c['lod'] is not None) if shared else None}
    settings=s.document();identity={'a':a.identity(),'b':b.identity(),'settings':settings,'version':__version__}
    run_id=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'schema':'narwhal.delta/1','version':__version__,'run_id':run_id,'synthetic':a.synthetic or b.synthetic,
            'surveys':{'a':{k:v for k,v in a.document().items() if k!='points'},'b':{k:v for k,v in b.document().items() if k!='points'}},
            'inputs':identity,'settings':settings,'alignment':{'control_dz':correction,'control_cells':control_count,'control_roughness':control_mad},
            'stats':stats,'cells':cells,'regions':regions,'warnings':[
                'Threshold exceedance is conditional on the supplied error model; it is not survey certification.',
                'Horizontal errors, tide/refraction biases and spatial correlation need external assessment.',
                'Gain/loss describes elevation change; material type and cause are not inferred.',
                'Stable-control adjustment assumes the selected area did not change; its uncertainty is operator supplied.' if s.control else 'No automatic alignment applied. Check frame, datum and registration before interpreting change.']}


def section(result,y):
    """Nearest grid-centre east/west transect, preserving gaps."""
    size=result['settings']['cell_size'];j=math.floor(y/size)
    return [c for c in result['cells'] if c['j']==j]
