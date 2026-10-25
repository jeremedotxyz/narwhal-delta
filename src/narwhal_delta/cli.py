"""Equivalent browser and command-line analysis paths."""
import argparse,json
from pathlib import Path
from .model import Settings
from .demo import pair
from .engine import compare
from .export import bundle
from .ingest import load

def main():
    parser=argparse.ArgumentParser(description='Narwhal Delta / survey comparison')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('serve');p.add_argument('--port',type=int,default=8768)
    p=sub.add_parser('demo');p.add_argument('--scenario',choices=['harbor','unchanged','bias'],default='harbor');p.add_argument('--output',type=Path,default=Path('delta-evidence.zip'))
    p=sub.add_parser('compare');p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--settings',type=Path);p.add_argument('--frame-id');p.add_argument('--vertical-datum');p.add_argument('--output',type=Path,default=Path('delta-evidence.zip'))
    args=parser.parse_args()
    if args.command=='serve':
        if not 1024<=args.port<=65535:parser.error('port must be 1024–65535')
        from .server import serve
        serve(args.port);return
    try:
        s=Settings()
        if args.command=='demo':a,b=pair(args.scenario)
        else:
            meta={'frame_id':args.frame_id,'vertical_datum':args.vertical_datum}
            a=load(args.before.read_bytes(),args.before.name,meta);b=load(args.after.read_bytes(),args.after.name,meta)
            if args.settings:s=Settings(**json.loads(args.settings.read_text()))
        result=compare(a,b,s);args.output.write_bytes(bundle(a,b,result))
        print(json.dumps({'output':str(args.output),'run_id':result['run_id'],'stats':result['stats']},indent=2))
    except (OSError,ValueError,TypeError) as exc:parser.error(str(exc))
