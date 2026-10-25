"""Reproduce the numerical reference experiments without a running browser."""
from pathlib import Path
import json
from narwhal_delta.demo import pair,change
from narwhal_delta.engine import compare
from narwhal_delta.model import Settings
from narwhal_delta.export import bundle

out=Path('runs');out.mkdir(exist_ok=True);records={}
for scenario in ('harbor','unchanged','bias'):
    a,b=pair(scenario);result=compare(a,b)
    records[scenario]={'run_id':result['run_id'],'stats':result['stats'],'alignment':result['alignment']}
    if scenario=='harbor':
        errors=[abs(c['delta']-change(c['x'],c['y'])) for c in result['cells'] if c['delta']is not None]
        records[scenario]['mean_absolute_delta_error_m']=sum(errors)/len(errors)
        assert records[scenario]['mean_absolute_delta_error_m']<.012
        assert result['stats']['counts']['only_a']==120
        (out/'harbor-evidence.zip').write_bytes(bundle(a,b,result))
    if scenario=='unchanged':assert result['stats']['changed_area']==0
    if scenario=='bias':
        corrected=compare(a,b,Settings(control=[0,0,44,5]))
        assert corrected['stats']['changed_area']==0
        assert abs(corrected['alignment']['control_dz']+.12)<.003
        records['bias_corrected']={'run_id':corrected['run_id'],'stats':corrected['stats'],'alignment':corrected['alignment']}
(out/'reference-results.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
