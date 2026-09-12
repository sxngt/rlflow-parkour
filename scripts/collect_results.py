#!/usr/bin/env python3
"""Copy verified final evaluation videos into a titled, browsable result/ archive."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
TASKS = {'a1_continuous_tracker_v1': ('CT-v1', '공유지형_연속앞뒤접촉_스크립트목표'), 'a1_directed_jump_v5': ('T1J-v5', '평지_수평목표도약_출발영역_실비행이동'), 'a1_flat_jump_supported_v4': ('T1J-v4', '평지_정밀착지_지지유지_수직감쇠'), 'a1_flat_jump_precise_v3': ('T1J-v3', '평지_단일도약_최초접촉정밀성_착지안정화'), 'a1_flat_jump_shaped_v2': ('T1J-v2', '평지_단일도약_높이명령보상_착지자세'), 'a1_flat_jump_v1': ('T1J-v1', '평지_단일도약_비행확인_착지안정화'), 'a1_t0_shared_single_foot_v7': ('T0F-v7', '공유정책_네발단독이동_착지안정화'), 'a1_t0_foothold_v1': ('T0-v1', '정적_목표접촉'),
         'a1_t0_sequential_v2': ('T0S-v2', '순차_발디딤_4회'),
         'a1_t0_single_foot_continuous_v6': ('T0F-v6', '단독발이동_전단계네발정렬벌점'),
         'a1_t0_single_foot_aligned_v5': ('T0F-v5', '단독발이동_최종네발정렬벌점'),
         'a1_t0_single_foot_v4': ('T0F-v4', '단독발이동_3발지지_착지안정화'),
         'a1_t0_sequential_stable_v3': ('T0S-v3', '3발지지_순차발디딤_착지안정화')}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(evaluation, result_root=ROOT / 'result'):
    evaluation, result_root = Path(evaluation).resolve(), Path(result_root).resolve()
    run = json.loads((evaluation / 'run.json').read_text())
    supervisor = json.loads(evaluation.with_suffix('.supervisor.json').read_text())
    if run.get('kind') != 'evaluate' or run['status'] != 'SUCCEEDED' or supervisor['exit_code'] != 0 or not supervisor['resource_released']:
        raise ValueError('Only completed, verified evaluations may be archived')
    source_video = evaluation / 'evaluation.mp4'
    expected = run['artifacts'].get('evaluation.mp4')
    if not source_video.exists() or expected != digest(source_video):
        raise ValueError('Missing video or video hash mismatch')
    report = json.loads((evaluation / 'evaluation.json').read_text())
    replay = json.loads((evaluation / 'replay.json').read_text())
    for name in ('evaluation.json','replay.json','scenarios.json','first-frame.png'):
        if not (evaluation/name).exists():
            raise ValueError('Missing evaluation artifact: ' + name)
        if digest(evaluation / name) != run['artifacts'][name]:
            raise ValueError('Evaluation metadata hash mismatch: ' + name)
    task, task_title = TASKS[run['config']['task']]
    if run.get('evaluation_support'):
        support = run['evaluation_support']
        label = {'flat': '평지대조', 'continuous': '발별_연속지지면', 'split': '발별_분리지지면_갭6cm', 'deck': '단일발판_140x120cm', 'course': '불연속발판_발별15cm이동_패드6x12cm_갭9cm', 'shared-course': '공유블록_높이·경사·방향변화_앞뒤접촉', 'full-gap': '분리된대형발판'}[support['mode']]
        if support['mode']=='full-gap':
            label += f"_실제갭{100*support['layout']['gap_width_m']:.2f}cm_발목표전진{100*support['goal_forward_m']:g}cm"
        task_title = label + ('_목표전이15cm_고정정책' if support.get('goal_forward_m') == .15 else '_목표거리별평가')
        if support['mode']=='shared-course':
            layout=support['layout'];level={'easy':'쉬움','medium':'중간','hard':'어려움'}.get(layout.get('level'),'개발')
            task_title=f"{level}_{len(layout['surfaces'])-1}구간_경사·회전_스크립트목표_자율계획아님
        if support.get('matched_material'):
            task_title += '_기본재질·구간별마찰설정' if support.get('surface_material_overrides') else '_동일물리재질'
    if run.get('chain_contract',{}).get('progress_criterion')=='mapped_contact_v1':
        task_title='지도접촉기준v1_몸체비행거리별도_'+task_title
    if run.get('chain_contract', {}).get('spacing_contract') == 'nonuniform_horizontal_v1':
        task_title += '_비균일간격' + '·'.join(f'{100*x:g}' for x in run['chain_contract']['step_lengths_m']) + 'cm'
    if run.get('evaluation_support', {}).get('friction_variation'):
        friction = run['evaluation_support']['friction_variation']
        task_title += f"_발판{friction['start_station']}부터마찰재질{friction['authored_friction']:g}"
    if run.get('chain_contract', {}).get('height_contract'):
        task_title += '_발판높이' + '·'.join(f'{100*x:g}' for x in run['chain_contract']['support_heights_m']) + 'cm'
    history=run['config'].get('observation_history')
    if history:
        task_title += '_관측이력8프레임' if history['mode']=='stack' else '_동일입력크기·이력이없는대조군'
    if run.get('transition_restore'):
        task_title = '저장착지복원_후속도약만_전체코스평가아님_' + task_title
    model = run.get('checkpoint')
    if run.get('chain_contract'):
        task_title += f"_리셋없는{run['chain_contract']['hops']}회도약_안정화후재도약"
        if run['chain_contract'].get('settle_command') == 'hold-last':
            task_title += '_준비구간직전관절명령유지'
    seed, updates = 'NA', 0
    train_run = None
    if model:
        checkpoint = Path(model['path'])
        if digest(checkpoint) != model['sha256']:
            raise ValueError('Model lineage hash mismatch')
        train_run = json.loads((checkpoint.parent / 'run.json').read_text())
        seed = train_run['config']['seed']
        updates = json.loads(checkpoint.with_suffix('.json').read_text())['completed_iterations']
    if run['config']['task'] in ('a1_t0_single_foot_v4','a1_t0_single_foot_aligned_v5','a1_t0_single_foot_continuous_v6'):
        task_title = run['config']['sequence']['foot_order'][0].replace('_foot','')+'_'+task_title
    if run['config']['task'] == 'a1_directed_jump_v5' and train_run:
        jump = train_run['config']['jump']
        if train_run['config'].get('retention_training'):
            task_title += '_혼합' + '·'.join(f'{100*x:g}' for x in train_run['config']['retention_training']['single_goal_choices_m']) + 'cm'
        elif 'train_forward_choices_m' in jump:
            task_title += '_이산학습거리' + '·'.join(f'{100*d:g}' for d in jump['train_forward_choices_m']) + 'cm'
        else:
            low, high = jump['train_forward_range_m']
            task_title += f'_학습거리{100*low:g}–{100*high:g}cm'
    if 'purpose:profiling' in run.get('research_tags', run['config'].get('research_tags', [])):
        task_title += '_처리량측정용_미수렴정책'
    mode = {'policy':'PPO', 'zero':'기본자세_대조군', 'shuffled-target':'PPO_목표셔플'}[run['baseline']]
    action_evaluation = run.get('action_evaluation', {'mode': 'mean'})
    if action_evaluation['mode'] == 'sampled':
        mode += f"_행동샘플링-RNG{action_evaluation['seed']}"
    date = datetime.fromtimestamp(run['finished_unix_s'], timezone(timedelta(hours=9))).strftime('%Y-%m-%d')
    title = f'A1 | {task} {task_title.replace("_", " ")} | {mode} seed {seed} | {updates} updates | 개발군 {report["episodes"]} episodes'
    if train_run and train_run['config'].get('retention_training'):
        goals = '·'.join(f'{100*x:g}' for x in train_run['config']['retention_training']['single_goal_choices_m'])
        title += f' | 학습 step: 연속 도약 50% + 단일 목표 {goals}cm 50%'
        weights = train_run['config']['retention_training'].get('single_goal_weights')
        if weights is not None:
            title += ' | 단일 목표 선택 비중 ' + ':'.join(map(str, weights))
    if train_run and train_run['config'].get('support_assignment'):
        mode = train_run['config']['support_assignment']['single_mode']
        title += f' | 학습 지지면: 연속 deck / 단일 {mode}'
    if run.get('scene_construction'):
        title += ' | 독립 지형 생성 검증'
    folder_name = f'{date}__A1__{task}__seed-{seed}__updates-{updates:06d}__{evaluation.name}'
    result_root.mkdir(parents=True, exist_ok=True)
    folder = result_root / folder_name
    episode = replay['episode']
    outcome = '성공' if episode['success'] else '실패' if episode['failure'] else '시간초과'
    video_name = f'A1__{task_title}__{mode}-seed{seed}__{updates}업데이트__{episode["scenario_id"]}__{outcome}.mp4'
    visible_episodes = replay.get('episodes', [episode])
    parallel = replay.get('layout') == 'parallel'
    if parallel:
        title += f' | {len(visible_episodes)}개 로봇 병렬 평가'
        video_name = f'A1__{task_title}__{mode}-seed{seed}__{updates}업데이트__병렬{len(visible_episodes)}개_최종평가.mp4'
    if replay.get('layout')=='third_person_follow':
        title+=' | 단일 로봇 3인칭 추적'
        video_name='3인칭추적__'+video_name
    # Preserve the full human title in the manifest; filesystem components have
    # byte limits, so shorten only overlong filenames with a stable digest.
    if len(video_name.encode('utf-8')) > 240:
        suffix = '__' + hashlib.sha256(video_name.encode('utf-8')).hexdigest()[:12] + '.mp4'
        prefix = video_name[:-4].encode('utf-8')[:240-len(suffix.encode())].decode('utf-8', errors='ignore')
        video_name = prefix + suffix
    record = {'research_tags':run.get('research_tags',run['config'].get('research_tags',[])), 'title':title, 'evaluation_run':evaluation.name, 'training_run':Path(model['path']).parent.name if model else None,
              'source_evaluation':os.path.relpath(evaluation, result_root), 'source_video_sha256':expected,
              'checkpoint':model, 'action_evaluation':action_evaluation, 'task':run['config']['task'], 'seed':seed, 'updates':updates,
              'video':video_name, 'video_episode':episode, 'aggregate':{k:v for k,v in report.items() if k!='results'},
              'video_layout':replay.get('layout','single'), 'video_episodes':visible_episodes,
              'selection':'fixed render-enabled grid; camera may crop outer robots; not selected for success' if parallel else 'first fixed development scenario; not selected for success', 'date_kst':date}
    with (result_root / '.index.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if folder.exists():
            existing = json.loads((folder/'manifest.json').read_text())
            if existing['source_video_sha256'] != expected or existing['evaluation_run'] != evaluation.name:
                raise ValueError('Archive collision; refusing to overwrite')
            if digest(folder / existing['video']) != expected:
                raise ValueError('Existing archived video is corrupt')
        else:
            temp = Path(tempfile.mkdtemp(prefix='.collect-', dir=result_root))
            try:
                shutil.copyfile(source_video, temp / video_name)
                if train_run and train_run.get('training_video'):
                    training = train_run['training_video']
                    training_source = Path(model['path']).parent/training['file']
                    if digest(training_source) != training['sha256']:
                        raise ValueError('Training video hash mismatch')
                    training_name = f'A1__{task_title}__PPO-seed{seed}__실제병렬학습_{training["learning_iterations"][0]}-{training["learning_iterations"][1]}업데이트.mp4'
                    shutil.copyfile(training_source,temp/training_name)
                    shutil.copyfile(training_source.parent/'parallel-training-replay.json',temp/'training-replay.json')
                    record['training_video'] = {**training, 'file':training_name}
                for name in ('evaluation.json','scenarios.json','replay.json'):
                    shutil.copyfile(evaluation/name, temp/name)
                if (evaluation/'diagnostics.json').exists():
                    if digest(evaluation/'diagnostics.json') != run['artifacts'].get('diagnostics.json'):
                        raise ValueError('Diagnostics hash mismatch')
                    shutil.copyfile(evaluation/'diagnostics.json',temp/'diagnostics.json')
                    record['diagnostics_file']='diagnostics.json'
                if (evaluation/'terrain.json').exists():
                    if digest(evaluation/'terrain.json') != run['artifacts'].get('terrain.json'):
                        raise ValueError('Terrain manifest hash mismatch')
                    shutil.copyfile(evaluation/'terrain.json', temp/'terrain.json')
                    record['terrain_file'] = 'terrain.json'
                if (evaluation/'collision-contract.json').exists():
                    if digest(evaluation/'collision-contract.json') != run['artifacts'].get('collision-contract.json'):
                        raise ValueError('Collision contract hash mismatch')
                    shutil.copyfile(evaluation/'collision-contract.json', temp/'collision-contract.json')
                if (evaluation/'first-frame.png').exists():
                    shutil.copyfile(evaluation/'first-frame.png', temp/'preview.png')
                (temp/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
                completed = episode.get('completed_contacts')
                text = f'# {title}\n\n![첫 프레임](preview.png)\n\n[최종 평가 영상 재생]({quote(video_name)})\n\n'
                if record.get('training_video'):
                    text += f'[실제 PPO 병렬 학습 영상]({quote(record["training_video"]["file"])}) — 전체 {record["training_video"]["total_simulated_envs"]}개 중 {len(record["training_video"]["visible_env_ids"])}개를 관찰합니다.\n\n'
                text += f'- 원본 학습 실행: `{record["training_run"] or "없음: 대조군"}`\n- 평가 실행: `{evaluation.name}`\n'
                text += f'- 전체 개발군: **{report["successes"]}/{report["episodes"]} 성공**, 평균 최종 발 오차 **{report["mean_final_error_m"]*100:.2f} cm**\n'
                if 'mean_completed_contacts' in report:
                    text += f'- 평균 순차 접촉 완료: **{report["mean_completed_contacts"]:.2f}/{report.get("required_contacts",4)}회**\n'
                if parallel:
                    text += f'- 이 영상: **{len(visible_episodes)}개 로봇 병렬**, 보이는 로봇의 첫 episode 성공 **{sum(e["success"] for e in visible_episodes)}/{len(visible_episodes)}**.\n'
                    text += '- 4×4 구역을 카메라로 관찰합니다. 종료 후 자동 reset된 로봇의 후속 episode는 화면에 보일 수 있지만 평가 지표에서 제외합니다.\n'
                else:
                    text += f'- 이 영상: `{episode["scenario_id"]}`, **{outcome}**, simulator {episode["length"]*0.02:.2f}초'
                    if completed is not None:text += f', 순차 접촉 **{completed}/{report.get("required_contacts",4)}회**'
                    text += '\n'
                text += '- 영상 선정: 고정 시나리오/구역. 대표 성공 사례로 선별하지 않음.\n'
                text += f'- 원본 기록: [{evaluation.name}]({quote(os.path.relpath(evaluation, folder))})\n'
                text += '- 파일: `evaluation.json` 전체 평가, `replay.json` 시간·목표·실제 발·행동, `manifest.json` 출처·hash.\n\n'
                text += 'T0/T0S는 평지의 초기 제어 과제이며 점프·연속 파쿠르 성능을 뜻하지 않습니다.\n'
                (temp/'README.md').write_text(text)
                if digest(temp/video_name) != expected:raise ValueError('Copy verification failed')
                temp.replace(folder)
            except BaseException:
                shutil.rmtree(temp)
                raise
        if run.get('chain_contract'):
            source = evaluation / 'chain-events.json'
            event_hash = run['artifacts'].get('chain-events.json')
            if not event_hash or digest(source) != event_hash:
                raise ValueError('Chain event hash mismatch')
            destination = folder / source.name
            if destination.exists() and digest(destination) != event_hash:
                raise ValueError('Archived chain events differ; refusing to overwrite')
            if not destination.exists():
                temporary = folder / '.chain-events.tmp'
                shutil.copyfile(source, temporary)
                if digest(temporary) != event_hash:
                    raise ValueError('Chain event copy verification failed')
                temporary.replace(destination)
            manifest_path = folder / 'manifest.json'
            archived = json.loads(manifest_path.read_text())
            archived['chain_events'] = {'file': source.name, 'sha256': event_hash}
            temporary = folder / '.manifest.tmp'
            temporary.write_text(json.dumps(archived, ensure_ascii=False, indent=2) + '\n')
            temporary.replace(manifest_path)
            readme = folder / 'README.md'
            content = readme.read_text()
            if '[도약별 전환 기록](chain-events.json)' not in content:
                content += '\n[도약별 전환 기록](chain-events.json): 도약 번호·전환 시각·출발 원점·상태 보존 검사. 개별 도약의 접촉 지표와 전체 코스 성공을 구분합니다.\n'
                temporary = folder / '.README.tmp'
                temporary.write_text(content)
                temporary.replace(readme)
        rebuild_index(result_root)
    return folder


def rebuild_index(root):
    entries=[]
    for manifest in root.glob('*/manifest.json'):
        entries.append((manifest.parent,json.loads(manifest.read_text())))
    entries.sort(key=lambda item:(item[1]['task'],item[1]['updates'],str(item[1]['seed']),item[1]['evaluation_run']),reverse=True)
    lines=['# parkour — 실행별 최종 평가 영상', '',
           '각 행은 하나의 평가 실행입니다. 학습 실행·모델 업데이트 수·평가 조건을 제목으로 구분합니다. 고정된 단일 시나리오 또는 4×4 구역을 촬영하며, 전체 평가와 영상에 보이는 로봇의 결과를 구분합니다. 실제 PPO 학습 영상은 별도 링크로 표시합니다.', '',
           '| 상세 제목 · 실행 기록 | 전체 평가 | 이 영상 | MP4 |', '|---|---|---|---|']
    for folder, row in entries:
        report, ep=row['aggregate'],row['video_episode']
        state='성공' if ep['success'] else '실패' if ep['failure'] else '시간초과'
        if 'completed_contacts' in ep:state+=f' · {ep["completed_contacts"]}/{report.get("required_contacts",4)} 접촉'
        if row.get('video_layout') == 'parallel':
            visible=row['video_episodes']
            state=f'병렬 {len(visible)}개 · 첫 episode {sum(e["success"] for e in visible)}/{len(visible)} 성공'
        title=row['title'].replace('|','·')
        rel=quote(folder.name)
        overall=f'{report["successes"]}/{report["episodes"]} 성공'
        if 'mean_completed_contacts' in report:
            overall += f' · 평균 {report["mean_completed_contacts"]:.2f}/{report.get("required_contacts",4)} 접촉'
        links=f'[최종 평가]({rel}/{quote(row["video"])})'
        if row.get('training_video'):
            links += f' · [실제 병렬 학습]({rel}/{quote(row["training_video"]["file"])})'
        lines.append(f'| [{title}]({rel}/README.md) | {overall} | {state} | {links} |')
    lines += ['', '원본 파일은 `artifacts/`에 보존합니다. 이 폴더에는 확인된 MP4 사본과 요약을 저장하며 checksum으로 원본과 일치를 검사합니다.',
              '향후 영상 포함 평가가 supervisor에서 정상 완료되면 자동으로 이 목록에 추가됩니다.']
    temp=root/'README.md.tmp'
    temp.write_text('\n'.join(lines)+'\n')
    temp.replace(root/'README.md')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evaluations',nargs='+',type=Path)
    args=parser.parse_args()
    for path in args.evaluations:print(collect(path))
