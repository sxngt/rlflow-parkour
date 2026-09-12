"""Oriented shared contact surfaces, independent of foot names and target plans."""
import math

def rotation(roll,pitch,yaw):
    r,p,y=map(math.radians,(roll,pitch,yaw));cr,sr=math.cos(r),math.sin(r);cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y)
    matrix=[[cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],[sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cp*sr,cp*cr]]
    cr,sr=math.cos(r/2),math.sin(r/2);cp,sp=math.cos(p/2),math.sin(p/2);cy,sy=math.cos(y/2),math.sin(y/2)
    quat=[cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy]
    return matrix,quat

def surface(name,top_center,size,rpy):
    values=list(top_center)+list(size)+list(rpy)
    if len(top_center)!=3 or len(size)!=3 or len(rpy)!=3 or any(not math.isfinite(x) for x in values) or min(size)<=0:
        raise ValueError('Finite oriented cuboid geometry required')
    R,q=rotation(*rpy);normal=[row[2] for row in R]
    center=[x-n*size[2]/2 for x,n in zip(top_center,normal)]
    return {'id':name,'top_center_m':list(top_center),'center_m':center,'size_m':list(size),'orientation_wxyz':q,
            'rotation_local_to_world':R,'normal':normal,'usable_half_extents_m':[size[0]/2-.02,size[1]/2-.02],
            'material':{'static_friction':.5,'dynamic_friction':.5,'combine_mode':'average'},'contact_ownership':'shared'}

def local_point(s,point):
    delta=[a-b for a,b in zip(point,s['top_center_m'])];R=s['rotation_local_to_world']
    return [sum(R[j][i]*delta[j] for j in range(3)) for i in range(3)]

def world_point(s,point):
    return [s['top_center_m'][i]+sum(s['rotation_local_to_world'][i][j]*point[j] for j in range(3)) for i in range(3)]

def contains_contact_center(s,point,normal_offset=(0.,.04)):
    x,y,z=local_point(s,point);hx,hy=s['usable_half_extents_m']
    return abs(x)<=hx and abs(y)<=hy and normal_offset[0]<=z<=normal_offset[1]

def build_shared_course(kind='mixed'):
    if kind not in ('blocks','ramps','turns','mixed'):raise ValueError('Unknown course')
    centers=[[0.,0.,0.],[.85,0.,.08],[1.65,.15,.16],[2.35,.65,.24],[2.45,1.5,.12],[1.85,2.2,.18],[1.,2.45,0.]]
    headings=[0,0,15,45,85,130,160];tilts=[(0,0),(0,8),(-8,-6),(8,10),(-10,0),(5,-8),(0,0)]
    surfaces=[]
    for i,(point,yaw,tilt) in enumerate(zip(centers,headings,tilts)):
        point=list(point)
        if kind in ('blocks','ramps'):point[:2]=[i*.85,0.];yaw=0
        if kind=='turns':point[2]=0.
        roll,pitch=tilt if kind in ('ramps','mixed') else (0,0)
        size=(.7,.7,.18) if 0<i<6 else (1.,1.,.2)
        surfaces.append(surface('surface_'+str(i),point,size,(roll,pitch,yaw)))
    return {'schema_version':2,'geometry_contract':'oriented_shared_surfaces_v1','kind':kind,'frame':'course_local',
            'surfaces':surfaces,'start_position_m':centers[0],'goal_position_m':surfaces[-1]['top_center_m'],
            'catch_floor_z_m':-.8,'scope':'Geometry development set only; no assigned foot targets, planned route or demonstrated policy feasibility'}
