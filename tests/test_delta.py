import base64,csv,io,json,math,socket,subprocess,sys,time,unittest,urllib.error,urllib.request,zipfile
from dataclasses import replace
from pathlib import Path
from narwhal_delta.model import Survey,Settings
from narwhal_delta.engine import compare,transform,section
from narwhal_delta.demo import pair,change
from narwhal_delta.ingest import load,json_load
from narwhal_delta.export import bundle,restore,report,svg,cells_csv
from narwhal_delta.server import State

def survey(z=0,name='test',xy=None):
    pts=tuple((x,y,z) for x,y in (xy or [(i+.25,j+.25) for j in range(2) for i in range(2)]) for _ in range(3))
    return Survey(name,'FRAME-1','DATUM-1',pts)

def archive(members):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for k,v in members.items():z.writestr(k,v)
    return out.getvalue()

class Contracts(unittest.TestCase):
    def test_nonfinite_point(self):
        for value in (float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):Survey('x','f','d',((value,0,0),))
    def test_huge_integer_coordinates_rejected(self):
        with self.assertRaises(ValueError):Survey('x','f','d',((10**500,0,0),))
    def test_empty_survey(self):
        with self.assertRaises(ValueError):Survey('x','f','d',())
    def test_boolean_settings_rejected(self):
        for kw in ({'min_points':True},{'confidence':True},{'cell_size':True}):
            with self.assertRaises(ValueError):Settings(**kw)
    def test_bad_bounds(self):
        with self.assertRaises(ValueError):Settings(roi=[1,0,0,1])
    def test_min_points_requires_integer(self):
        with self.assertRaises(ValueError):Settings(min_points=3.0)
    def test_frame_mismatch(self):
        with self.assertRaises(ValueError):compare(survey(),replace(survey(),frame_id='OTHER'))
    def test_datum_mismatch(self):
        with self.assertRaises(ValueError):compare(survey(),replace(survey(),vertical_datum='OTHER'))
    def test_large_rectangle_rejected(self):
        with self.assertRaises(ValueError):compare(survey(xy=[(0,0),(999,999)]),survey())

class Numerical(unittest.TestCase):
    def test_mixed_analytic_example(self):
        root=Path(__file__).resolve().parents[1]/'examples';meta={'frame_id':'F','vertical_datum':'D'}
        a=load((root/'minimal-before.csv').read_bytes(),'a.csv',meta);b=load((root/'minimal-after.csv').read_bytes(),'b.csv',meta)
        r=compare(a,b,Settings(cell_size=1));self.assertEqual(r['stats']['gain_volume'],2);self.assertEqual(r['stats']['loss_volume'],1);self.assertEqual(r['stats']['net_thresholded_volume'],1);self.assertTrue(r['synthetic'])
    def test_known_volume(self):
        r=compare(survey(),survey(1),Settings(cell_size=1))
        self.assertEqual(r['stats']['gain_volume'],4);self.assertEqual(r['stats']['changed_area'],4);self.assertEqual(r['stats']['loss_volume'],0)
    def test_negative_volume(self):
        self.assertEqual(compare(survey(1),survey(),Settings(cell_size=1))['stats']['loss_volume'],4)
    def test_threshold_equality_is_not_change(self):
        self.assertEqual(compare(survey(),survey(1),Settings(cell_size=1,min_change=1))['stats']['changed_area'],0)
    def test_zero_change(self):
        self.assertEqual(compare(survey(),survey())['stats']['changed_area'],0)
    def test_missing_coverage_is_not_loss(self):
        r=compare(survey(),survey(xy=[(.25,.25)]),Settings(cell_size=1));self.assertEqual(r['stats']['counts']['only_a'],3);self.assertEqual(r['stats']['loss_volume'],0)
    def test_insufficient_not_significant(self):
        a=replace(survey(),points=((.25,.25,0),));b=replace(a,points=((.25,.25,2),));r=compare(a,b)
        self.assertEqual(r['stats']['counts']['insufficient'],1);self.assertEqual(r['stats']['gain_volume'],0)
    def test_uncertainty_in_quadrature(self):
        s=Settings(sigma_a=.1,sigma_b=.2,sigma_alignment=.3,min_change=0);c=compare(survey(),survey(1),s)['cells'][0]
        self.assertAlmostEqual(c['lod'],1.96*math.sqrt(.14))
    def test_roughness_increases_threshold(self):
        a=Survey('a','f','d',((.1,.1,-.5),(.1,.1,0),(.1,.1,.5)));self.assertGreater(compare(a,replace(a,name='b'))['stats']['median_lod'],1)
    def test_outlier_resistant_median(self):
        a=Survey('a','f','d',tuple((.1,.1,z) for z in [0,0,0,100]));self.assertEqual(compare(a,a)['cells'][0]['a'],0)
    def test_negative_coordinate_floor(self):
        a=survey(xy=[(-.1,-.1)]);self.assertEqual(compare(a,a)['cells'][0]['i'],-1)
    def test_roi_half_open(self):
        r=compare(survey(),survey(1),Settings(cell_size=1,roi=[0,0,1,2]));self.assertEqual(r['stats']['gain_volume'],2);self.assertEqual(r['stats']['counts']['outside_roi'],2)
    def test_yaw_rotation_origin(self):
        p=transform(((1,0,2),),Settings(yaw_deg=90,dx=3,dy=4,dz=5))[0];self.assertAlmostEqual(p[0],3);self.assertAlmostEqual(p[1],5);self.assertEqual(p[2],7)
    def test_regions_four_connected(self):
        a=survey(xy=[(.25,.25),(1.25,1.25)]);r=compare(a,replace(a,points=tuple((x,y,z+1)for x,y,z in a.points)),Settings(cell_size=1));self.assertEqual(len(r['regions']),2)
    def test_no_shared_cells(self):
        r=compare(survey(),survey(xy=[(10,10)]));self.assertEqual(r['stats']['shared_cells'],0);self.assertIsNone(r['stats']['median_lod'])
    def test_deterministic_identity(self):
        a,b=pair();self.assertEqual(compare(a,b),compare(a,b))
    def test_changed_parameter_changes_identity(self):
        a,b=survey(),survey(1);self.assertNotEqual(compare(a,b)['run_id'],compare(a,b,Settings(min_change=.2))['run_id'])
    def test_cross_section_has_only_requested_row(self):
        self.assertTrue(all(c['j']==0 for c in section(compare(survey(),survey()),.25)))
    def test_control_requires_ten_cells(self):
        with self.assertRaises(ValueError):compare(survey(),survey(.1),Settings(control=[0,0,2,2]))
    def test_control_removes_known_bias(self):
        a,b=pair('bias');r=compare(a,b,Settings(control=[0,0,44,5]));self.assertAlmostEqual(r['alignment']['control_dz'],-.12,delta=.003);self.assertEqual(r['stats']['changed_area'],0)
    def test_seeded_unchanged_has_no_detected_change(self):
        a,b=pair('unchanged');self.assertEqual(compare(a,b)['stats']['changed_area'],0)
    def test_known_reference_change_accuracy(self):
        a,b=pair();r=compare(a,b);errors=[abs(c['delta']-change(c['x'],c['y'])) for c in r['cells'] if c['delta']is not None]
        self.assertLess(sum(errors)/len(errors),.012);self.assertEqual(r['stats']['counts']['only_a'],120)

class Imports(unittest.TestCase):
    meta={'frame_id':'F','vertical_datum':'D'}
    def test_csv(self):
        self.assertEqual(load(b'x,y,z\n0,0,-5\n','a.csv',self.meta).points,((0.,0.,-5.),))
    def test_json_roundtrip(self):
        a=survey();self.assertEqual(a.points,load(json.dumps(a.document()).encode(),'a.json').points)
    def test_positive_down_json_rejected(self):
        d=survey().document();d['z_positive']='down'
        with self.assertRaises(ValueError):load(json.dumps(d).encode(),'a.json')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):json_load(b'{"x":NaN}')
    def test_csv_requires_frame(self):
        with self.assertRaises(ValueError):load(b'x,y,z\n0,0,1','a.csv')
    def test_duplicate_csv_headers_rejected(self):
        with self.assertRaises(ValueError):load(b'x,y,z,z\n0,0,1,2','a.csv',self.meta)
    def test_snapshot_metadata_object_required(self):
        with self.assertRaises(ValueError):load(archive({'metadata.json':'[]','points.csv':'x,y,z\n0,0,1'}),'a.zip',self.meta)
    def test_csv_nan_rejected(self):
        with self.assertRaises(ValueError):load(b'x,y,z\n0,0,nan','a.csv',self.meta)
    def test_bad_flags_filtered_and_synthetic_retained(self):
        a=load(b'x,y,z,quality\n0,0,1,1\n0,0,2,32','a.csv',self.meta);self.assertEqual(a.points,((0.,0.,2.),));self.assertTrue(a.synthetic)
    def test_topo_registered_snapshot(self):
        for frame in ('MAP_ENU','POSE_REGISTERED'):
            data=archive({'metadata.json':json.dumps({'metadata':{'frame':frame}}),'points.csv':'x,y,z\n0,0,-3'});self.assertEqual(load(data,'snapshot.zip',self.meta).points[0][2],-3)
    def test_sensor_local_rejected(self):
        data=archive({'metadata.json':json.dumps({'metadata':{'frame':'SENSOR_LOCAL'}}),'points.csv':'x,y,z\n0,0,-3'})
        with self.assertRaises(ValueError):load(data,'a.zip',self.meta)
    def test_zip_traversal_rejected(self):
        with self.assertRaises(ValueError):load(archive({'../evil':'x'}),'a.zip',self.meta)
    def test_zip_duplicate_rejected(self):
        out=io.BytesIO()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');z=zipfile.ZipFile(out,'w');z.writestr('x','1');z.writestr('x','2');z.close()
        with self.assertRaises(ValueError):load(out.getvalue(),'a.zip',self.meta)

class Evidence(unittest.TestCase):
    def test_bundle_restores_identical_identity(self):
        a,b=survey(),survey(1);r=compare(a,b);a2,b2,s,notes,identity=restore(bundle(a,b,r,[{'x':.25,'y':.25,'text':'Inspect'}]));self.assertEqual(identity,compare(a2,b2,s)['run_id']);self.assertEqual(notes[0]['text'],'Inspect')
    def test_bundle_bytes_reproducible(self):
        a,b=survey(),survey(1);r=compare(a,b);self.assertEqual(bundle(a,b,r),bundle(a,b,r))
    def test_tampered_bundle_rejected(self):
        a,b=survey(),survey(1);data=bundle(a,b,compare(a,b))
        with zipfile.ZipFile(io.BytesIO(data))as z:parts={n:z.read(n)for n in z.namelist()}
        parts['before.json']=b'{}'
        with self.assertRaises(ValueError):restore(archive(parts))
    def test_escaped_report(self):
        a=replace(survey(),name='<script>alert(1)</script>');text=report(compare(a,a),[{'x':0,'y':0,'text':'<script>x</script>'}]);self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)
    def test_csv_row_counts(self):
        r=compare(survey(),survey());self.assertEqual(len(list(csv.DictReader(io.StringIO(cells_csv(r))))),len(r['cells']))
    def test_svg_valid_xml(self):
        import xml.etree.ElementTree as ET
        ET.fromstring(svg(compare(survey(),survey())))
    def test_failed_action_is_transactional(self):
        state=State();identity=state.result['run_id']
        with self.assertRaises(ValueError):state.action('/api/compare',{'cell_size':-1})
        self.assertEqual(state.result['run_id'],identity)
    def test_staged_import_never_compares_mismatched_frames(self):
        state=State();s=survey();doc={'slot':'a','filename':'new.json','data':base64.b64encode(json.dumps(s.document()).encode()).decode()};self.assertIsNone(state.action('/api/import',doc)['result']);doc['slot']='b';self.assertIsNotNone(state.action('/api/import',doc)['result'])

class HTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sock=socket.socket();sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1];sock.close();cls.base=f'http://127.0.0.1:{cls.port}'
        cls.process=subprocess.Popen([sys.executable,'-m','narwhal_delta','serve','--port',str(cls.port)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                with urllib.request.urlopen(cls.base,timeout=1):break
            except (OSError,urllib.error.URLError):time.sleep(.05)
        else:raise RuntimeError('Server did not start')
    @classmethod
    def tearDownClass(cls):cls.process.terminate();cls.process.communicate(timeout=10)
    def test_root_and_assets(self):
        for path in ('/','/style.css','/app.js','/api/state'):
            with urllib.request.urlopen(self.base+path)as response:self.assertEqual(response.status,200)
    def test_foreign_origin_rejected(self):
        req=urllib.request.Request(self.base+'/api/demo',data=b'{}',headers={'Origin':'https://example.org','Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError)as error:urllib.request.urlopen(req)
        self.assertEqual(error.exception.code,403)
    def test_wrong_host_rejected(self):
        with self.assertRaises(urllib.error.HTTPError)as error:urllib.request.urlopen(urllib.request.Request(self.base,headers={'Host':'example.org'}))
        self.assertEqual(error.exception.code,403)
    def test_unknown_path_is_not_file_server(self):
        with self.assertRaises(urllib.error.HTTPError)as error:urllib.request.urlopen(self.base+'/pyproject.toml')
        self.assertEqual(error.exception.code,404)
    def test_download_real_evidence(self):
        with urllib.request.urlopen(self.base+'/export.zip')as response:
            a,b,s,notes,identity=restore(response.read());self.assertEqual(identity,compare(a,b,s)['run_id'])
    def test_bad_setting_gives_json_error(self):
        req=urllib.request.Request(self.base+'/api/compare',data=b'{"cell_size":0}',headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError)as error:urllib.request.urlopen(req)
        self.assertIn('error',json.loads(error.exception.read()))

if __name__=='__main__':unittest.main()
