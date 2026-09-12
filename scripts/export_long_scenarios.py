"""Export the three explicit geometry designs, never a policy performance claim."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_long_shared_course,build_ten_gap_course,world_point

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family',choices=['ten-transfer','ten-gap'],default='ten-transfer')
    args=parser.parse_args()
    ten_gap=args.family=='ten-gap'
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.ticker import MaxNLocator
    out=ROOT/f'result/scenarios/{args.family}-difficulty-designs';out.mkdir(parents=True,exist_ok=True)
    fig=plt.figure(figsize=(15,5));entries=[]
    for index,level in enumerate(('easy','medium','hard')):
        layout=build_ten_gap_course(level,1) if ten_gap else build_long_shared_course(level,1)
        (out/(level+'.json')).write_text(json.dumps(layout,indent=2)+'\n')
        ax=fig.add_subplot(1,3,index+1,projection='3d')
        for i,s in enumerate(layout['surfaces']):
            x,y,z=s['size_m'];corners=[world_point(s,p) for p in [(-x/2,-y/2,0),(x/2,-y/2,0),(x/2,y/2,0),(-x/2,y/2,0),(-x/2,-y/2,-z),(x/2,-y/2,-z),(x/2,y/2,-z),(-x/2,y/2,-z)]]
            faces=[[corners[j] for j in face] for face in [(0,1,2,3),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]
            color='#ed8936' if s.get('scenario_role')=='gap_landing' else plt.cm.viridis(i/layout['transitions'])
            ax.add_collection3d(Poly3DCollection(faces,facecolor=color,edgecolor='#334155',linewidth=.5,alpha=.9))
            cx,cy,cz=s['top_center_m']
            if not ten_gap or i%4==0:ax.text(cx,cy,cz+.08,str(i),fontsize=8)
        p=[s['top_center_m'] for s in layout['surfaces']]
        ax.set_xlim(-.6,max(v[0] for v in p)+.6);ax.set_ylim(min(v[1] for v in p)-.8,max(v[1] for v in p)+.8);ax.set_zlim(-.2,.65)
        ax.set_box_aspect((max(v[0] for v in p)+1.2,max(v[1] for v in p)-min(v[1] for v in p)+1.6,1.3))
        ax.yaxis.set_major_locator(MaxNLocator(3));ax.set_zticks([0.,.3,.6]);ax.tick_params(labelsize=8)
        ax.view_init(elev=30,azim=-65);ax.set_xlabel('X (m)');ax.set_ylabel('Y (m)');ax.set_zlabel('Z (m)')
        heights=[v[2] for v in p];max_step=max(abs(a-b) for a,b in zip(heights,heights[1:]))
        label='10 gaps / 40 transfers' if ten_gap else '10 transfers'
        ax.set_title(f'{level.upper()} | {label}\npath {layout["nominal_path_length_m"]:.2f} m | max height change {max_step:.2f} m')
        entries.append({'level':level,'geometry_seed':1,'transfers':layout['transitions'],'planned_gap_count':layout.get('planned_gap_count'),'nominal_path_length_m':layout['nominal_path_length_m'],'max_center_height_change_m':max_step,'geometry':level+'.json'})
    fig.suptitle('Long shared-surface scenarios — geometry design, not demonstrated robot performance',fontsize=13)
    fig.text(.5,.04,'One shared platform supports multiple feet. Easy projections can overlap; medium/hard add gaps, tilt and heading changes.\nTransfer count does not imply jump count or successful execution. Time is measured in each actual episode.',ha='center',fontsize=10)
    fig.subplots_adjust(top=.84,bottom=.13,wspace=.04)
    fig.savefig(out/'difficulty-overview.png',dpi=180);fig.savefig(out/'difficulty-overview.svg');plt.close(fig)
    (out/'manifest.json').write_text(json.dumps({'kind':'scenario_geometry_catalog','not_policy_result':True,'entries':entries},indent=2)+'\n')
    (out/'README.md').write_text('# 난이도별 긴 공유 발판 맵 · 지형 설계\n\n![시나리오 비교](difficulty-overview.png)\n\n각 맵은 시작면과10개 이동 구간을 가진 공유 발판입니다. 쉬움은 인접 발판의 수평 투영이 겹칠 수 있고, 중급·고급은 간격·경사·높이·진행 방향 변화가 커집니다. 로봇 주행 결과나 물리적 실행 가능성 증명이 아닙니다. 실제 점프 횟수·완주·10초 이상 주행은 평가 영상과 계측으로 별도 확인합니다.\n\n정확한 oriented cuboid geometry는 easy.json, medium.json, hard.json에 보존했습니다.\n')
    if ten_gap:
        (out/'README.md').write_text('# 난이도별 10개 갭 장거리 코스\n\n![코스 설계](difficulty-overview.png)\n\n41개 공유 표면, 40회 발 목표 이동, 10곳의 명시적 갭으로 구성했습니다. 각 갭 전에는 접근 구간이 있고 경사·높이·방향이 변합니다. 주황색은 갭 착지면입니다. 쉬움·중간·어려움의 기준 갭 폭은 각각 0.10/0.45/0.80m이며 개별 폭은 ±10% 변합니다. 실제 값과 좌표는 각 JSON에 있습니다.\n\n지형 설계이며 완주나 10회 실제 도약을 달성했다는 뜻은 아닙니다. 단일 로봇 3인칭 추적 평가에서 실제 이동 시간·도약·완주를 별도로 측정합니다.\n')
    print(out)
if __name__=='__main__':main()
