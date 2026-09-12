"""Optional geometric body-height reference while traversing a gap."""
import math

def validate_clearance(config):
    spec=config.get('gap_clearance')
    if spec is None:return None
    if not isinstance(spec,dict) or set(spec)!={'version','apex_m','height_cost'} or spec['version']!='gap_clearance_v1':raise ValueError('Invalid gap clearance contract')
    for key,low,high in [('apex_m',.02,.25),('height_cost',1.,200.)]:
        x=spec[key]
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not low<=x<=high:raise ValueError('Invalid gap clearance value')
    return dict(spec)

def height_reference(root_xy,centers,targets,root_height,apex):
    a=centers[(targets-1).clamp_min(0)];b=centers[targets]
    delta=b[:,:2]-a[:,:2]
    raw=((root_xy-a[:,:2])*delta).sum(1)/delta.square().sum(1).clamp_min(1e-8)
    t=raw.clamp(0,1)
    z=a[:,2]*(1-t)+b[:,2]*t+root_height+4*apex*t*(1-t)
    return z,(raw>=0)&(raw<=1)&(targets>0)
