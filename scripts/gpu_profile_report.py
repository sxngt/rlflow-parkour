"""Report bounded throughput samples; does not infer convergence speed."""
import json
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[1]

def summarize(folder):
    run=json.loads((folder/'run.json').read_text())
    assert run['status']=='SUCCEEDED'
    metrics=[json.loads(l) for l in (folder/'metrics.jsonl').read_text().splitlines()]
    assert [r['iteration'] for r in metrics]==list(range(1,101))
    rows=[json.loads(l) for l in folder.with_suffix('.host-profile.jsonl').read_text().splitlines()]
    samples=[r for r in rows if r['training_status']=='RUNNING' and 20<=r.get('training_iteration',0)<100]
    assert len(samples)>1
    supervisor=json.loads(folder.with_suffix('.supervisor.json').read_text())
    uuid=supervisor['gpu_uuid']
    gpu=[g for r in samples for g in r.get('gpus',[]) if g['uuid']==uuid]
    n=run['config']['num_envs'];times=[r['wall_seconds'] for r in metrics[20:]]
    dt=samples[-1]['unix_s']-samples[0]['unix_s']
    a,b=samples[0]['host']['cpu_times'],samples[-1]['host']['cpu_times']
    busy=sum(b[k]-a[k] for k in ['user','nice','system','irq','softirq','steal'])/dt
    pids=set(supervisor['worker_pids'])
    rss=[sum(p['rss_bytes'] for p in r['processes'] if p['pid'] in pids) for r in samples]
    io0,io1=samples[0]['host']['disk_io'],samples[-1]['host']['disk_io']
    return {'run':folder.name,'envs':n,'gpu_uuid':uuid,'steps_per_second':80*n*24/sum(times),
        'update_seconds_mean':mean(times),'update_seconds_median':median(times),
        'update_seconds_min':min(times),'update_seconds_max':max(times),
        'sample_count':len(samples),'gpu_missing_samples':len(samples)-len(gpu),
        'sample_spacing_max_s':max(b['unix_s']-a['unix_s'] for a,b in zip(samples,samples[1:])),
        'gpu_utilization_mean_pct':mean(float(g['utilization_pct']) for g in gpu),
        'gpu_memory_sampled_max_mib':max(float(g['memory_mib']) for g in gpu),
        'gpu_power_mean_w':mean(float(g['power_w']) for g in gpu),
        'worker_rss_sampled_max_gib':max(rss)/2**30,'host_available_min_gib':min(r['host']['memory']['available'] for r in samples)/2**30,
        'host_busy_cpu_equivalents':busy,'host_disk_read_mib_s':(io1['read_bytes']-io0['read_bytes'])/dt/2**20,
        'host_disk_write_mib_s':(io1['write_bytes']-io0['write_bytes'])/dt/2**20,
        'supervisor_wall_seconds':supervisor['wall_seconds']}


def main():
    solo=[summarize(ROOT/f'artifacts/gpu-env-sweep-n{n}-solo') for n in [1024,2048,4096,8192]]
    concurrent=[summarize(ROOT/f'artifacts/gpu-env-sweep-n8192-concurrent-gpu{i}') for i in range(4)]
    baseline=solo[-1]['steps_per_second']
    for r in concurrent:r['slowdown_ratio']=baseline/r['steps_per_second']
    payload={'solo':solo,'concurrent':concurrent,'sum_individual_concurrent_steps_s':sum(r['steps_per_second'] for r in concurrent),
        'limitations':['Each condition has one short throughput run; optimizer batch changes with environment count.',
        'Sum of individual warmup-excluded rates is not a synchronized end-to-end makespan rate.',
        'GPU values are roughly 2-second samples, not true instantaneous peaks. Host CPU and I/O include other services.',
        'Concurrent mode runs four samplers versus one in solo mode; monitoring overhead differs.']}
    (ROOT/'docs/gpu-env-sweep-summary.json').write_text(json.dumps(payload,indent=2)+'\n')
    lines=['# GPU 환경 수 처리량 측정','', '동일100update 중 처음20회를 제외한80회. 학습 수렴 속도나 제어 성능을 증명하는 비교가 아니다.','', '| 실행 | 환경 | step/s | GPU 평균 사용률 | 표본 최대 VRAM(MiB) | 평균 전력(W) |','|---|---:|---:|---:|---:|---:|']
    for r in solo+concurrent:lines.append(f"| {r['run']} | {r['envs']} | {r['steps_per_second']:.0f} | {r['gpu_utilization_mean_pct']:.1f}% | {r['gpu_memory_sampled_max_mib']:.0f} | {r['gpu_power_mean_w']:.1f} |")
    lines+=['',f"동시 실행의 개별 처리량 합은 {payload['sum_individual_concurrent_steps_s']:.0f}step/s이다. 동기화된 makespan 처리량과 구분한다.",'','단독 환경 수당 한 번의 짧은 측정이며 PPO batch가 달라진다. 자원 수치는 약2초 간격 표본이며 진짜 순간 최대값이 아니다. CPU·I/O는 호스트 전체 서비스가 포함된다. 동시 측정은 sampler4개로 호출 부하도 증가한다. 원본·추가 지표는 gpu-env-sweep-summary.json 및 artifacts/*.host-profile.jsonl 참조.']
    (ROOT/'docs/gpu-env-sweep-results.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(payload,indent=2))

if __name__=='__main__':main()
