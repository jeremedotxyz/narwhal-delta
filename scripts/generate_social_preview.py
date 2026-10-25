"""Render blueprint share artwork from actual Delta reference cells.

Only artwork regeneration needs Pillow; the application runtime is stdlib-only.
Run `python scripts/generate_social_preview.py` after installing the package.
The SVG is editable and the PNG is GitHub-ready at 1280 by 640 pixels.
"""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont
from narwhal_delta.demo import pair
from narwhal_delta.engine import compare
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'assets';OUT.mkdir(parents=True,exist_ok=True)
W,H,SCALE=1280,640,3
BG,INK,DIM,ACC,GRID='#09233D','#DCECF6','#83B7D2','#6DE1DE','#17334C'
AMBER='#EDAB67'
image=Image.new('RGB',(W*SCALE,H*SCALE),BG);draw=ImageDraw.Draw(image)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
'<title>Narwhal Delta / repeat-survey evidence</title>',
'<desc>Actual seeded harbor comparison: baseline and repeat terrain mesh, plan change classifications and cross-section. Synthetic reference, no physical accuracy claim.</desc>',
f'<rect width="{W}" height="{H}" fill="{BG}"/>']
def line(points, color=DIM, width=0.7):
    if len(points) < 2:
        return
    draw.line([(x*SCALE, y*SCALE) for x,y in points], fill=color, width=max(1, round(width*SCALE)))
    coords = ' '.join(f'{x:.2f},{y:.2f}' for x,y in points)
    svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}"/>')

def rect(x,y,w,h,color=DIM,width=.7):
    line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],color,width)

def text(x,y,value,size=12,color=INK,bold=False):
    # Menlo is available on macOS; DejaVu is a portable Pillow/fontconfig fallback.
    candidates = ['/System/Library/Fonts/Menlo.ttc',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                  'DejaVuSansMono.ttf']
    for candidate in candidates:
        try:
            font = ImageFont.truetype(candidate, round(size*SCALE), index=1 if bold and candidate.endswith('.ttc') else 0)
            break
        except OSError:
            continue
    else:
        raise RuntimeError('Install a monospace TrueType font to regenerate artwork')
    draw.text((x*SCALE,y*SCALE),value,font=font,fill=color,anchor='ls',stroke_width=0)
    svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Courier New,Courier,monospace" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')

def panel(x,y,w,h,title):
    rect(x,y,w,h)
    text(x+14,y+24,title,13,ACC)
    line([(x,y+37),(x+w,y+37)])


a,b=pair();r=compare(a,b);stats=r['stats'];lookup={(c['i'],c['j']):c for c in r['cells']}
for x in range(24,W-23,20):line([(x,24),(x,H-24)],GRID,.45)
for y in range(24,H-23,20):line([(24,y),(W-24,y)],GRID,.45)
rect(24,24,W-48,H-48,DIM,.9);line([(24,116),(1256,116)])
text(44,74,'NARWHAL / DELTA',39,INK,True)
text(46,100,'REPEAT SURVEY / CHANGE OBSERVATORY',13,DIM)
text(850,51,'NARWHAL TWO PLUS + TOPO + REPLAY',12,ACC)
text(850,75,'OBSERVE / COMPARE / INVESTIGATE',12,INK)
text(850,99,'github.com/jeremedotxyz/narwhal-delta',10.5,DIM)
for i in range(1,10):text(24+i*1232/10,17,str(i),8,DIM)
for y,label in [(158,'A'),(294,'B'),(492,'C'),(594,'D')]:text(10,y,label,8,DIM)
panel(44,134,770,310,'01 / REPEAT TERRAIN + OBSERVED CHANGE')
def iso(x,y,z):return (430+10.5*(.85*(x-22)+.6*(y-16)),305+7*(-.22*(x-22)+.32*(y-16))-42*(z+17.25))
for j in range(0,64,2):
    points=[]
    for i in range(88):
        c=lookup.get((i,j))
        if not c or c['a']is None:line(points,'#32516B',.55);points=[];continue
        points.append(iso(c['x'],c['y'],c['a']))
    line(points,'#32516B',.55)
for i in range(0,88,2):
    points=[]
    for j in range(64):
        c=lookup.get((i,j))
        if not c or c['a']is None:line(points,'#32516B',.55);points=[];continue
        points.append(iso(c['x'],c['y'],c['a']))
    line(points,'#32516B',.55)
for j in range(0,64,2):
    previous=None
    for i in range(88):
        c=lookup[(i,j)]
        if c['b']is None:previous=None;continue
        current=iso(c['x'],c['y'],c['b'])
        if previous:line([previous,current],AMBER if c['state']=='gain' else ACC if c['state']=='loss' else '#63879E',.85)
        previous=current
text(60,196,'44 x 32 m / LOCAL FRAME / 0.50 m GRID',10,DIM)
text(60,428,'BASELINE GHOST + REPEAT MESH / DISPLAY Z EXAGGERATED',10,DIM)
panel(834,134,402,310,'02 / THRESHOLD-EXCEEDING CELLS')
left,top,scale=880,184,6.25
for c in r['cells']:
    x=left+(c['x']-.25)*scale;y=top+(32-c['y']-.25)*scale
    color=AMBER if c['state']=='gain' else ACC if c['state']=='loss' else '#29485F' if c['state']=='below_threshold' else '#102A40'
    draw.rectangle((x*SCALE,y*SCALE,(x+.5*scale)*SCALE,(y+.5*scale)*SCALE),fill=color)
    svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{.5*scale:.2f}" height="{.5*scale:.2f}" fill="{color}"/>')
rect(left,top,44*scale,32*scale,DIM,.6)
for region in r['regions'][:3]:
    x=left+region['x']*scale;y=top+(32-region['y'])*scale
    rect(x-4,y-4,8,8,INK,.8);text(x+8,y-5,region['id'],9,INK)
text(1189,191,'N',10,ACC);line([(1193,228),(1193,198),(1188,208),(1193,198),(1198,208)],INK,.9)
text(850,412,'CYAN / LOSS     AMBER / GAIN',10,DIM)
text(850,430,f"MEDIAN DETECTION LIMIT / {stats['median_lod']:.3f} m",10,DIM)
rect(44,460,1192,72,DIM,.7);text(59,482,'03 / CROSS-SECTION Y = 16.25 m',12,ACC)
row=[lookup[(i,32)] for i in range(88)]
for key,color in [('a',DIM),('b',AMBER)]:
    previous=None
    for c in row:
        if c[key]is None:previous=None;continue
        pt=(390+(c['x']/44)*825,510-18*(c[key]+17.3))
        if previous:line([previous,pt],color,1.1)
        previous=pt
text(60,514,'OBSERVED MEDIANS / GAPS PRESERVED',10,DIM)
line([(24,548),(1256,548)],DIM,.9)
for x in (298,552,806):line([(x,548),(x,616)],DIM,.7)
text(44,582,f"{stats['changed_area']:.2f} m2",25,INK,True);text(44,604,'DETECTED CHANGE AREA',11,DIM)
text(320,582,f"+{stats['gain_volume']:.2f} m3",25,AMBER,True);text(320,604,'ELEVATION GAIN',11,DIM)
text(574,582,f"-{stats['loss_volume']:.2f} m3",25,ACC,True);text(574,604,'ELEVATION LOSS',11,DIM)
text(828,579,'SYNTHETIC REFERENCE',18,ACC,True);text(828,603,'TRACEABLE / REV A / v0.1.0',11,DIM)
svg.append('</svg>');(OUT/'social-preview.svg').write_text('\n'.join(svg)+'\n')
image.resize((W,H),Image.Resampling.LANCZOS).save(OUT/'social-preview.png',optimize=True)
print(f'Saved {OUT}/social-preview.svg and .png ({W} x {H})')
