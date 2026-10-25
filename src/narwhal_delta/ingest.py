"""Strict CSV/JSON and bounded Topo/Replay snapshot ZIP imports; never extract."""
import csv, hashlib, io, json, zipfile
from pathlib import PurePosixPath
from .model import Survey,MAX_BYTES,MAX_POINTS

def json_load(data):
    def reject(x): raise ValueError(f'Non-finite JSON token: {x}')
    try: return json.loads(data,parse_constant=reject)
    except (json.JSONDecodeError,UnicodeDecodeError) as exc: raise ValueError('Invalid UTF-8 JSON.') from exc

def csv_points(data):
    try: text=data.decode('utf-8-sig')
    except UnicodeDecodeError as exc: raise ValueError('CSV must be UTF-8.') from exc
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)) or not {'x','y','z'} <= set(reader.fieldnames): raise ValueError('CSV requires x,y,z headers in metres.')
    points=[];synthetic=False
    for line,row in enumerate(reader,2):
        if len(points)>=MAX_POINTS: raise ValueError('Too many CSV points.')
        try:
            if 'quality' in row:
                flag=int(row['quality'])
                if not 0<=flag<=65535: raise ValueError('quality out of range')
                if flag & (1|2|8): continue
                synthetic=synthetic or bool(flag&32)
            points.append(tuple(float(row[k]) for k in ('x','y','z')))
        except (ValueError,TypeError,KeyError) as exc: raise ValueError(f'Invalid coordinate/quality on CSV line {line}.') from exc
    return points,synthetic

def load(data,filename,metadata=None):
    if not data or len(data)>MAX_BYTES: raise ValueError('Input must be nonempty and at most 32 MiB.')
    meta=dict(metadata or {});suffix=PurePosixPath(filename).suffix.lower();digest=hashlib.sha256(data).hexdigest()
    source=PurePosixPath(filename.replace('\\','/')).name
    if suffix=='.json':
        doc=json_load(data)
        if not isinstance(doc,dict) or doc.get('schema')!='narwhal.survey/1': raise ValueError('Expected narwhal.survey/1 JSON.')
        if doc.get('units')!='m' or doc.get('z_positive')!='up': raise ValueError('JSON requires units m and z_positive up.')
        points=doc.get('points',[]);meta=doc
    elif suffix=='.csv':
        points,flagged=csv_points(data);meta['synthetic']=meta.get('synthetic',False) or flagged
    elif suffix=='.zip':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos=z.infolist();names=[i.filename for i in infos]
                if len(infos)>32 or len(set(names))!=len(names) or sum(i.file_size for i in infos)>MAX_BYTES:
                    raise ValueError('ZIP has too many members, duplicate names or excessive expanded size.')
                for info in infos:
                    p=PurePosixPath(info.filename)
                    if p.is_absolute() or '..' in p.parts or '\\' in info.filename or info.flag_bits&1:
                        raise ValueError('Unsafe or encrypted ZIP member.')
                if 'before.json' in names and 'after.json' in names:
                    raise ValueError('This is a project bundle. Use Restore project instead.')
                if 'points.csv' not in names or 'metadata.json' not in names: raise ValueError('Snapshot ZIP requires points.csv and metadata.json.')
                md=json_load(z.read('metadata.json'))
                if not isinstance(md,dict):raise ValueError('Snapshot metadata must be an object.')
                md=md.get('metadata',md)
                if not isinstance(md,dict):raise ValueError('Snapshot metadata wrapper must be an object.')
                if md.get('frame') not in ('POSE_REGISTERED','MAP_ENU','ENU','LOCAL_ENU'):
                    raise ValueError('Only registered ENU snapshots are accepted; SENSOR_LOCAL is not a common survey frame.')
                points,flagged=csv_points(z.read('points.csv'));meta['synthetic']=meta.get('synthetic',False) or flagged
        except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as exc: raise ValueError('Invalid snapshot ZIP.') from exc
    else: raise ValueError('Use CSV, survey JSON, or a Topo/Replay snapshot ZIP.')
    return Survey(meta.get('name',source),meta.get('frame_id',''),meta.get('vertical_datum',''),tuple(points),
                  meta.get('synthetic',False),source,digest)
