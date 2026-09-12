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


def scripted_pair_targets(layout, initial_foot_xy, half_width_m=.16, terminal_half_length_m=.18, initial_rear_target="own_stance"):
    """Training-only contact script; final front/rear positions form a stance.

    Intermediate rear contacts reuse front targets. At the final platform, the
    groups receive separated targets so all four feet can support the body.
    This script is not an autonomous map planner or a feasibility certificate.
    """
    if initial_rear_target not in ('own_stance','front_stance'):raise ValueError('Unknown initial rear target')
    if len(initial_foot_xy)!=4 or half_width_m<=0 or terminal_half_length_m<=0:
        raise ValueError('Invalid calibrated stance')
    groups=[[],[]];last=len(layout['surfaces'])-1
    for group in range(2):
        for index,s in enumerate(layout['surfaces']):
            if index==0:
                start=0 if group==1 and initial_rear_target=='front_stance' else group*2
                pair=[[x,y,.02] for x,y in initial_foot_xy[start:start+2]]
            else:
                longitudinal=(terminal_half_length_m if group==0 else -terminal_half_length_m) if index==last else 0.
                pair=[world_point(s,[longitudinal,sign*half_width_m,.02]) for sign in (1,-1)]
            if not all(contains_contact_center(s,p) for p in pair):
                raise ValueError('Contact script leaves usable shared surface')
            groups[group].append(pair)
    return {'initial_rear_target':initial_rear_target,'contract':'scripted_front_rear_surface_targets_v2' if initial_rear_target=='front_stance' else 'scripted_front_rear_surface_targets_v1','group_order':['front','rear'],
            'foot_order':['FL_foot','FR_foot','RL_foot','RR_foot'],'positions_m':groups,
            'surface_ids':[s['id'] for s in layout['surfaces']],
            'normals':[s['normal'] for s in layout['surfaces']],
            'terminal_contract':'separate fore/hind targets on final shared platform',
            'scope':'Teacher target script for Tracker development; not planner navigation'}


def build_easy_shared_course(seed=0):
    """Easy shared blocks with nonzero slope, height and heading variation."""
    import random
    rng=random.Random(seed);surfaces=[];x=y=0.
    for i in range(5):
        if i:x+=.45;y+=rng.uniform(-.04,.04)
        yaw=0. if i==0 else rng.uniform(-8,8)
        roll,pitch=(0.,0.) if i in (0,4) else (rng.uniform(-3,3),rng.uniform(-3,3))
        height=0. if i==0 else .02*i
        size=(1.,1.,.15) if i==0 else ((.7,.8,.15) if i==4 else (.55,.7,.15))
        surfaces.append(surface('surface_'+str(i),[x,y,height],size,(roll,pitch,yaw)))
    return {'schema_version':2,'geometry_contract':'oriented_shared_surfaces_v1','kind':'easy-shared','seed':seed,
            'frame':'course_local','surfaces':surfaces,'start_position_m':[0.,0.,0.],
            'goal_position_m':surfaces[-1]['top_center_m'],'catch_floor_z_m':-.8,
            'scope':'Easy development terrain with touching/overlapping projected blocks; not a gap-crossing benchmark'}


def build_long_shared_course(level='easy',seed=0,transitions=10,preparation_fraction=1.):
    """Long scenario geometry; ten surface transfers are not ten proven jumps."""
    import random
    if level not in ('easy','medium','hard') or type(transitions) is not int or not 10<=transitions<=40:
        raise ValueError('Long scenarios use easy/medium/hard and 10..40 transfers')
    step,tilt,height,turn={'easy':(.45,3.,.04,6.),'medium':(.65,10.,.12,15.),'hard':(.85,20.,.24,25.)}[level]
    if preparation_fraction not in (.25,.5,.75,1.) or (preparation_fraction!=1. and level!='medium'):
        raise ValueError('Only medium preparation fractions .25/.5/.75 are supported')
    if preparation_fraction!=1.:
        step,tilt,height,turn=[a+(b-a)*preparation_fraction for a,b in zip((.45,3.,.04,6.),(step,tilt,height,turn))]
    rng=random.Random(seed);surfaces=[];x=y=heading=0.
    for i in range(transitions+1):
        if i:
            heading+=turn*math.sin(i*.7)+rng.uniform(-turn/4,turn/4)
            distance=step+rng.uniform(-.025,.025)
            if i==transitions:distance=max(distance,.6)  # Final rear stance must clear the previous block.
            x+=distance*math.cos(math.radians(heading));y+=distance*math.sin(math.radians(heading))
        z=0. if i==0 else height*(1.+.6*math.sin(i*.9))
        roll,pitch=(0.,0.) if i in (0,transitions) else (rng.uniform(-tilt,tilt),rng.uniform(-tilt,tilt))
        size=(1.,1.,.15) if i==0 else ((.7,.8,.15) if i==transitions else (.55,.7,.15))
        surfaces.append(surface('surface_'+str(i),[x,y,z],size,(roll,pitch,heading)))
    layout={'schema_version':2,'geometry_contract':'oriented_shared_surfaces_v1','scenario_contract':'long_shared_course_v1' if transitions==10 else 'long_shared_course_v2',
            'kind':'long-'+level,'level':level,'seed':seed,'transitions':transitions,'frame':'course_local',
            'surfaces':surfaces,'start_position_m':[0.,0.,0.],'goal_position_m':surfaces[-1]['top_center_m'],
            'catch_floor_z_m':-.8,'nominal_path_length_m':sum(math.dist(a['top_center_m'],b['top_center_m']) for a,b in zip(surfaces,surfaces[1:])),
            'scope':('Ten shared-surface transfers with height, slope and heading variation; actual jumps and feasibility measured during execution' if transitions==10 else 'Extended shared-surface endurance course; transfer count is not jump count; actual moving duration must be measured')}
    if preparation_fraction!=1.:
        layout.update(scenario_contract='long_shared_blend_v1',preparation_fraction=preparation_fraction,
                      scope='Explicit easy-to-medium geometry preparation; not the full medium benchmark')
    return layout


def shared_scene_spacing(layout):
    """Keep existing scenes stable; longer routes need nonoverlapping clone bounds."""
    lows=[float('inf')]*2;highs=[-float('inf')]*2
    for s in layout['surfaces']:
        for axis in range(2):
            extent=sum(abs(s['rotation_local_to_world'][axis][j])*s['size_m'][j]/2 for j in range(3))
            lows[axis]=min(lows[axis],s['center_m'][axis]-extent)
            highs[axis]=max(highs[axis],s['center_m'][axis]+extent)
    return max(14.,max(b-a for a,b in zip(lows,highs))+4.)


def assert_script_contacts_unoccluded(layout,script):
    """Independent local ray/slab check for other cuboids above contact points."""
    for group in script['positions_m']:
        for index,pair in enumerate(group):
            selected=layout['surfaces'][index];n=selected['normal']
            for point in pair:
                origin=[p+.1*v for p,v in zip(point,n)]
                direction=[-v for v in n]
                for other in layout['surfaces']:
                    if other['id']==selected['id']:continue
                    R=other['rotation_local_to_world'];delta=[a-b for a,b in zip(origin,other['center_m'])]
                    o=[sum(R[j][i]*delta[j] for j in range(3)) for i in range(3)]
                    d=[sum(R[j][i]*direction[j] for j in range(3)) for i in range(3)]
                    near,far=0.,.12-1e-6
                    for axis,extent in enumerate(other['size_m']):
                        h=extent/2
                        if abs(d[axis])<1e-12:
                            if not -h<=o[axis]<=h:near,far=1.,0.;break
                        else:
                            a,b=sorted(((-h-o[axis])/d[axis],(h-o[axis])/d[axis]))
                            near=max(near,a);far=min(far,b)
                    if near<=far:
                        raise ValueError(f'Contact on {selected["id"]} occluded by {other["id"]}')


def build_ten_gap_course(level='medium',seed=1,gap_scale=1.):
    """Ten gap locations separated by approach steps; actual flights are measured."""
    import random
    if level not in ('easy','medium','hard') or type(seed) is not int or seed<0 or gap_scale not in (.5,.75,1.):
        raise ValueError('Explicit tier, nonnegative seed and gap scale .5/.75/1 required')
    base_gap,tilt,height,turn={'easy':(.10,3.,.04,6.),'medium':(.45,7.,.06,10.),'hard':(.80,12.,.10,15.)}[level]
    rng=random.Random(seed);surfaces=[];gaps=[];x=y=heading=0.
    for i in range(41):
        is_gap=i>0 and i%4==0
        if i:heading+=turn*math.sin(i*.7)+rng.uniform(-turn/4,turn/4)
        roll,pitch=(0.,0.) if i in (0,40) else (rng.uniform(-tilt,tilt),rng.uniform(-tilt,tilt))
        z=0. if i==0 else height*(1.+.5*math.sin(i*.7))
        size=(1.,1.,.15) if i==0 else ((.7,.8,.15) if i==40 else (.55,.7,.15))
        candidate=surface('surface_'+str(i),[0.,0.,z],size,(roll,pitch,heading))
        if i:
            direction=[math.cos(math.radians(heading)),math.sin(math.radians(heading))]
            if is_gap:
                gap=base_gap*gap_scale*rng.uniform(.9,1.1)
                def projected_half(s):
                    return sum(abs(sum(direction[a]*s['rotation_local_to_world'][a][j] for a in (0,1)))*s['size_m'][j]/2 for j in (0,1))
                distance=projected_half(surfaces[-1])+projected_half(candidate)+gap
                gaps.append({'arrival_surface_index':i,'projected_top_gap_m':gap,'direction_xy':direction})
            else:distance=.45+rng.uniform(-.015,.015)
            x+=distance*direction[0];y+=distance*direction[1]
        candidate=surface('surface_'+str(i),[x,y,z],size,(roll,pitch,heading))
        candidate['scenario_role']='start' if i==0 else ('gap_landing' if is_gap else 'approach')
        surfaces.append(candidate)
    return {'schema_version':2,'geometry_contract':'oriented_shared_surfaces_v1','scenario_contract':'long_ten_gap_course_v1',
            'kind':'ten-gap-'+level,'level':level,'seed':seed,'gap_scale':gap_scale,'transitions':40,'frame':'course_local',
            'surfaces':surfaces,'start_position_m':[0.,0.,0.],'goal_position_m':surfaces[-1]['top_center_m'],
            'catch_floor_z_m':-.8,'planned_gap_count':10,'gap_locations':gaps,
            'nominal_path_length_m':sum(math.dist(a['top_center_m'],b['top_center_m']) for a,b in zip(surfaces,surfaces[1:])),
            'scope':'Ten explicit projected gap locations with approach steps; not ten proven jumps or a feasibility certificate'}
