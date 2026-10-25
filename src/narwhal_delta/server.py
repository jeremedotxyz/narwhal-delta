"""Loopback workbench. No cloud uploads, arbitrary file serving or remote URLs."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from importlib.resources import files
import base64,json,threading,urllib.parse
from .demo import pair
from .engine import compare
from .model import Settings,MAX_BYTES,label,number
from .ingest import load,json_load
from .export import bundle,restore,report,svg,cells_csv

class State:
    def __init__(self):
        self.lock=threading.Lock();self.a,self.b=pair();self.settings=Settings();self.annotations=[];self.result=compare(self.a,self.b,self.settings)
    def document(self):
        return {'result':self.result,'annotations':self.annotations,'point_counts':{'a':len(self.a.points),'b':len(self.b.points)}}
    def annotations_clean(self,items):
        if not isinstance(items,list) or len(items)>100: raise ValueError('At most 100 annotations.')
        return [{'text':label(p['text'],'annotation'),'x':number(p['x'],'x'),'y':number(p['y'],'y')} for p in items]
    def action(self,path,doc):
        a,b,s,notes=self.a,self.b,self.settings,list(self.annotations)
        if path=='/api/compare':s=Settings(**doc)
        elif path=='/api/demo':a,b=pair(doc.get('scenario','harbor'));s=Settings();notes=[]
        elif path=='/api/import':
            raw=base64.b64decode(doc['data'],validate=True);survey=load(raw,doc['filename'],doc.get('metadata'))
            if doc['slot']=='a':a=survey
            elif doc['slot']=='b':b=survey
            else:raise ValueError('slot must be a or b.')
            # Allow staged imports, but never compute a comparison across mismatched frames.
            if (a.frame_id,a.vertical_datum)!=(b.frame_id,b.vertical_datum):
                self.a,self.b=a,b;self.annotations=[];self.result=None
                return {'result':None,'annotations':[],'point_counts':{'a':len(a.points),'b':len(b.points)},
                        'pending':f'Import the other survey with frame {survey.frame_id} and datum {survey.vertical_datum}. No comparison is being computed.'}
        elif path=='/api/restore':
            a,b,s,notes,expected=restore(base64.b64decode(doc['data'],validate=True));notes=self.annotations_clean(notes)
            if compare(a,b,s)['run_id']!=expected:raise ValueError('Recomputed project identity differs. Use a matching Delta version.')
        elif path=='/api/annotations':
            if self.result is None: raise ValueError('Complete the survey pair before annotating.')
            self.annotations=self.annotations_clean(doc['annotations']);return self.document()
        else:raise ValueError('Unknown operation.')
        result=compare(a,b,s)
        self.a,self.b,self.settings,self.annotations,self.result=a,b,s,notes,result
        return self.document()

def serve(port=8768):
    state=State();allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,data,status=200,kind='application/json',filename=None):
            if isinstance(data,(dict,list)):data=json.dumps(data,allow_nan=False).encode()
            elif isinstance(data,str):data=data.encode()
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            self.end_headers();self.wfile.write(data)
        def guard(self):
            if self.headers.get('Host') not in allowed: self.send({'error':'Loopback Host required.'},403);return False
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://{h}' for h in allowed}:self.send({'error':'Same-origin requests only.'},403);return False
            return True
        def do_GET(self):
            if not self.guard():return
            path=urllib.parse.urlsplit(self.path).path
            if path=='/api/state':
                with state.lock:self.send(state.document())
            elif path in ('/export.zip','/report.html','/change-map.svg','/cells.csv'):
                with state.lock:
                    if state.result is None:self.send({'error':'Complete the pair first.'},409);return
                    data,kind,name={
                        '/export.zip':(lambda:bundle(state.a,state.b,state.result,state.annotations),'application/zip','narwhal-delta-evidence.zip'),
                        '/report.html':(lambda:report(state.result,state.annotations),'text/html; charset=utf-8','narwhal-delta-report.html'),
                        '/change-map.svg':(lambda:svg(state.result),'image/svg+xml','narwhal-delta-map.svg'),
                        '/cells.csv':(lambda:cells_csv(state.result),'text/csv; charset=utf-8','narwhal-delta-cells.csv')}[path]
                    try:self.send(data(),kind=kind,filename=name)
                    except ValueError as exc:self.send({'error':str(exc)},400)
            elif path in ('/','/style.css','/app.js'):
                name={'/':'index.html','/style.css':'style.css','/app.js':'app.js'}[path]
                self.send(files('narwhal_delta').joinpath('web',name).read_bytes(),kind={'index.html':'text/html; charset=utf-8','style.css':'text/css','app.js':'text/javascript'}[name])
            else:self.send({'error':'Not found.'},404)
        def do_POST(self):
            if not self.guard():return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send({'error':'JSON required.'},415);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=MAX_BYTES*4//3+4096:raise ValueError('Request too large or empty.')
                doc=json_load(self.rfile.read(length))
                if not isinstance(doc,dict):raise ValueError('JSON object required.')
                with state.lock:self.send(state.action(self.path,doc))
            except (ValueError,TypeError,KeyError,OverflowError) as exc:self.send({'error':str(exc)},400)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Narwhal Delta: http://127.0.0.1:{port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
