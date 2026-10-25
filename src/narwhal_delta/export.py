"""Portable reports, numerical evidence, deterministic archives and SVG maps."""
import csv,hashlib,io,json,zipfile
from html import escape


def dumps(doc): return json.dumps(doc,sort_keys=True,indent=2,allow_nan=False)

def color(c):
    state=c['state']
    if state=='gain': return '#edab67'
    if state=='loss': return '#56c8e0'
    return {'below_threshold':'#294858','insufficient':'#746b8d','only_a':'#152936','only_b':'#3c4952','outside_roi':'#101b28'}[state]

def svg(result,width=1120,height=720):
    cells=result['cells'];size=result['settings']['cell_size']
    xmin=min(c['x'] for c in cells)-size/2;xmax=max(c['x'] for c in cells)+size/2
    ymin=min(c['y'] for c in cells)-size/2;ymax=max(c['y'] for c in cells)+size/2
    scale=min((width-120)/(xmax-xmin),(height-180)/(ymax-ymin));ox=60;oy=100
    rects=''.join(f'<rect x="{ox+(c["x"]-size/2-xmin)*scale:.2f}" y="{oy+(ymax-c["y"]-size/2)*scale:.2f}" width="{size*scale+.1:.2f}" height="{size*scale+.1:.2f}" fill="{color(c)}"/>' for c in cells)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>Narwhal Delta / elevation change</title><desc>Observed local metre cells; amber gain, cyan loss, slate below threshold. Synthetic: {result['synthetic']}.</desc><rect width="100%" height="100%" fill="#081522"/><g font-family="monospace" fill="#c9e5e6"><text x="60" y="45" font-size="24">NARWHAL / DELTA</text><text x="60" y="72" font-size="12">B − A / METRES / {escape(result['run_id'][:16])}</text></g>{rects}<g fill="#94b9c5" font-family="monospace" font-size="13"><text x="60" y="{height-42}">CYAN / LOSS     AMBER / GAIN     SLATE / BELOW THRESHOLD</text><text x="60" y="{height-20}">LOCAL FRAME · NO INTERPOLATION · {'SYNTHETIC REFERENCE' if result['synthetic'] else 'OPERATOR-SUPPLIED SURVEYS'}</text></g></svg>'''

def cells_csv(result):
    out=io.StringIO(newline='');keys=list(result['cells'][0]);writer=csv.DictWriter(out,keys);writer.writeheader();writer.writerows(result['cells']);return out.getvalue()

def report(result,annotations=None):
    s=result['stats'];e=escape
    rows=''.join(f'<tr><td>{e(k)}</td><td>{e(str(v))}</td></tr>' for k,v in s.items() if k!='counts')
    annotation_html=''.join('<li>'+e(str(n['x']))+', '+e(str(n['y']))+' m / '+e(n['text'])+'</li>' for n in (annotations or []))
    regions=''.join(f'<tr><td>{r["id"]}</td><td>{r["kind"]}</td><td>{r["area"]:.2f}</td><td>{r["volume"]:+.3f}</td><td>{r["peak"]:+.3f}</td></tr>' for r in result['regions'][:100])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Narwhal Delta / investigation report</title><style>body{{font:16px/1.65 system-ui;max-width:1120px;margin:40px auto;padding:0 24px;color:#183448}}h1{{font-size:52px;letter-spacing:-2px}}h2{{margin-top:40px}}.eyebrow{{letter-spacing:3px;color:#24778b}}table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{text-align:left;border-bottom:1px solid #c6d7dd;padding:9px}}pre{{white-space:pre-wrap;background:#eef5f6;padding:20px;overflow-wrap:anywhere}}svg{{width:100%;height:auto}}@media print{{body{{margin:0}}h2{{break-after:avoid}}}}</style><p class="eyebrow">NARWHAL / ENGINEERING REFERENCE / v{result['version']}</p><h1>The difference is evidence.</h1><p>Survey comparison <b>{e(result['surveys']['a']['name'])}</b> → <b>{e(result['surveys']['b']['name'])}</b>.</p><p>{'SYNTHETIC REFERENCE — known constructed terrain, not a physical survey.' if result['synthetic'] else 'OPERATOR-SUPPLIED DATA — coordinate declarations and uncertainty inputs require review.'}</p>{svg(result)}<h2>01 / Quantitative findings</h2><p>Elevation change is B − A, positive up, in metres. Gain/loss volumes integrate only threshold-exceeding cells; raw net integrates all sufficiently sampled shared cells. Volumes are in m³, area in m².</p><table>{rows}</table><h2>02 / Connected change regions</h2><p>Four-neighbour regions; tiny components are retained. First 100 listed here; all are in result.json.</p><table><tr><th>ID</th><th>Class</th><th>Area m²</th><th>Volume m³</th><th>Peak m</th></tr>{regions}</table><h2>Inspection annotations</h2><ul>{annotation_html}</ul><h2>03 / Method and interpretation</h2><p>Both surveys use the same origin-anchored grid. Elevation is the per-cell median. Cell spread is 1.4826 × MAD. Difference σ = √(floor A² + floor B² + spread A² + spread B² + alignment σ²). The operative threshold is max(minimum change, confidence multiplier × difference σ). Equality does not exceed the threshold.</p><p>The threshold envelope is Σ(threshold × cell area), a sensitivity envelope, not a probabilistic confidence interval for total volume. Roughness is a proxy, not a calibrated survey error model. Spatial correlation, tide, refraction, horizontal misalignment and datum uncertainty can dominate these calculations.</p><ul>{''.join('<li>'+e(w)+'</li>' for w in result['warnings'])}</ul><h2>04 / Parameters and alignment</h2><pre>{e(dumps({'settings':result['settings'],'alignment':result['alignment']}))}</pre><h2>05 / Provenance</h2><pre>{e(dumps({'run_id':result['run_id'],'inputs':result['inputs'],'surveys':result['surveys']}))}</pre><p>No third-party certification, hydrographic standard compliance, navigational fitness or independent peer review is asserted.</p><p>Technical basis: <a href="https://gcd.riverscapes.net/Concepts/error-propagation/">GCD error propagation</a>; <a href="https://www.usgs.gov/publications/uncertainty-quantitative-analyses-topographic-change-error-propagation-and-role">USGS / Anderson (2019)</a>. Delta is an independent implementation.</p></html>'''

def bundle(a,b,result,annotations=None):
    files={'before.json':dumps(a.document()).encode(),'after.json':dumps(b.document()).encode(),
           'result.json':dumps(result).encode(),'cells.csv':cells_csv(result).encode(),
           'change-map.svg':svg(result).encode(),'report.html':report(result,annotations).encode(),
           'annotations.json':dumps(annotations or []).encode(),
           'README.txt':b'Narwhal Delta evidence bundle v1. Open report.html. Read docs/methods.md in the source repository. SHA256SUMS covers every member except itself. Source inputs are normalized surveys; original-file hashes are provenance, not original file bytes. No certification.\n'}
    if sum(len(v) for v in files.values())>32*1024*1024-4096:
        raise ValueError('Evidence bundle exceeds 32 MiB expanded limit. Crop/reduce input surveys before export.')
    files['SHA256SUMS']=('\n'.join(hashlib.sha256(data).hexdigest()+'  '+name for name,data in sorted(files.items()))+'\n').encode()
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    return out.getvalue()

def restore(data):
    from .ingest import load,json_load
    from .model import MAX_BYTES,Settings
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos=z.infolist();names=[i.filename for i in infos]
            expected={'before.json','after.json','result.json','cells.csv','change-map.svg','report.html','annotations.json','README.txt','SHA256SUMS'}
            if set(names)!=expected or len(names)!=len(expected) or sum(i.file_size for i in infos)>MAX_BYTES:
                raise ValueError('Project bundle members or expanded size invalid.')
            sums=z.read('SHA256SUMS').decode().splitlines();seen=set()
            for line in sums:
                digest,name=line.split('  ',1)
                if name not in expected-{'SHA256SUMS'} or name in seen: raise ValueError('Invalid checksum manifest.')
                if hashlib.sha256(z.read(name)).hexdigest()!=digest: raise ValueError('Bundle checksum mismatch.')
                seen.add(name)
            if seen!=expected-{'SHA256SUMS'}: raise ValueError('Incomplete checksum manifest.')
            a=load(z.read('before.json'),'before.json');b=load(z.read('after.json'),'after.json')
            # Preserve source provenance so restoring reproduces the same run identity.
            from dataclasses import replace
            for key,survey in [('before.json',a),('after.json',b)]:
                prov=json_load(z.read(key)).get('provenance',{})
                updated=replace(survey,source=prov.get('source',key),source_sha256=prov.get('source_sha256',''))
                if key=='before.json': a=updated
                else:b=updated
            result=json_load(z.read('result.json'));settings=Settings(**result['settings'])
            annotations=json_load(z.read('annotations.json'))
            if not isinstance(annotations,list) or len(annotations)>100: raise ValueError('Invalid annotations.')
            return a,b,settings,annotations,result['run_id']
    except (zipfile.BadZipFile,KeyError,UnicodeDecodeError,TypeError,RuntimeError,NotImplementedError,AttributeError) as exc: raise ValueError('Invalid project bundle.') from exc
