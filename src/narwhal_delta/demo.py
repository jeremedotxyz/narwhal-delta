"""Seeded synthetic survey pair with analytic change and a deliberate coverage gap."""
import math,random
from .model import Survey

def surface(x,y):
    return -18+.025*x+.3*math.sin(x/4)*math.cos(y/5)+1.2*math.exp(-((x-25)**2+(y-24)**2)/90)

def change(x,y):
    return .85*math.exp(-((x-15)**2/18+(y-18)**2/36))-.7*math.exp(-((x-31)**2/24+(y-14)**2/20))+.38*math.exp(-((x-28)**2/8+(y-27)**2/10))

def pair(scenario='harbor'):
    if scenario not in ('harbor','unchanged','bias'): raise ValueError('Unknown reference scenario.')
    rng=random.Random(532);a=[];b=[]
    for j in range(64):
        for i in range(88):
            x=(i+.5)*.5;y=(j+.5)*.5;z=surface(x,y)
            d=0 if scenario in ('unchanged','bias') else change(x,y)
            for k in range(5):
                ox=rng.uniform(-.2,.2);oy=rng.uniform(-.2,.2)
                a.append((x+ox,y+oy,z+rng.gauss(0,.014)))
                if scenario=='harbor' and 35<x<40 and 23<y<29: continue
                b.append((x+ox,y+oy,z+d+(.12 if scenario=='bias' else 0)+rng.gauss(0,.014)))
    frame='NARWHAL-HARBOR-LOCAL-v1';datum='SYNTHETIC-ZERO'
    return (Survey('Harbor / baseline',frame,datum,tuple(a),True,'reference-before'),
            Survey({'harbor':'Harbor / repeat','unchanged':'Null-change / repeat','bias':'Vertical bias +0.12 m / repeat'}[scenario],frame,datum,tuple(b),True,'reference-after'))
