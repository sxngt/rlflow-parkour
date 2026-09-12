type CourseReport = {
  episodes: number; successes: number;
  required_final_index?: number; mean_completed_surface_transfers?: number;
  mean_measured_jump_count?: number; mean_episode_seconds?: number;
  mean_front_accepted_index?: number; mean_rear_accepted_index?: number;
  demo_target?: {minimum_measured_jumps?: number};
  followed_video_demo_eligible?: boolean; evaluation_scope?: string;
  completed_hops_histogram?: Record<string, number>;
  chain_contract?: {hops: number; absolute_forward_targets_m?: number[]; step_lengths_m?: number[];
    progress_criterion?: string; spacing_contract?: string; root_boundary?: {version: string}};
};
export function CourseEvaluation({report}: {report: CourseReport}) {
  if (report.required_final_index != null) return <section className="panel">
    <h2>공유 발판 긴 코스 평가</h2>
    <p><strong>{report.successes}/{report.episodes}회 완주</strong> · 목표 {report.required_final_index}구간</p>
    <p>평균 완료 구간 {report.mean_completed_surface_transfers?.toFixed(2)} · 실제 점프 {report.mean_measured_jump_count?.toFixed(2)}회 · 실제 episode {report.mean_episode_seconds?.toFixed(2)}초</p>
    <p>앞발 진행 {report.mean_front_accepted_index?.toFixed(2)} / 뒷발 진행 {report.mean_rear_accepted_index?.toFixed(2)}</p>
    <p>추적 영상의 10구간·10초{report.demo_target?.minimum_measured_jumps!=null?`·${report.demo_target.minimum_measured_jumps}점프`:''} 완주 조건: {report.followed_video_demo_eligible ? '충족' : '미충족'}</p>
    <p className="muted">발판 전이와 실제 비행 점프는 별도 측정합니다. 제한 시간까지 서 있는 episode는 완주가 아닙니다. 현재 목표 접촉은 학습용으로 지정하며 자율 Planner 성능은 아닙니다.</p>
  </section>;
  const contract = report.chain_contract;
  if (!contract || contract.hops < 2) return null;
  const targets = contract.absolute_forward_targets_m || [];
  const histogram = report.completed_hops_histogram || {};
  return <section className="panel">
    <h2>연속 코스 완주</h2>
    <p><strong>{report.successes}/{report.episodes}회 완주</strong> · {contract.hops}회 연속 도약
      {targets.length > 0 && ` · 마지막 발 목표 전진 ${(targets[targets.length - 1]*100).toFixed(1)}cm`}</p>
    <p>도약 목표: {targets.map(value => `${(value*100).toFixed(1)}cm`).join(' → ')}</p>
    {contract.step_lengths_m && <p>도약별 간격: {contract.step_lengths_m.map(value => `${(value*100).toFixed(1)}cm`).join(' / ')}</p>}
    <div className="table-wrap"><table><thead><tr><th>완료한 도약 수</th><th>평가 횟수</th><th>비율</th></tr></thead><tbody>
      {Object.entries(histogram).sort(([a],[b]) => Number(a)-Number(b)).map(([hops,count]) =>
        <tr key={hops}><td>{hops}/{contract.hops}</td><td>{count}</td><td>{report.episodes ? (100*count/report.episodes).toFixed(1) : '—'}%</td></tr>)}
    </tbody></table></div>
    <p className="muted">첫 착지·접촉 통계는 마지막 실행 도약의 진단입니다. 전체 코스 완주와 구분해 확인하세요.
      판정: {contract.progress_criterion || '기존 비행거리·착지 기준'}
      {contract.root_boundary && ` · 이동 경계: ${contract.root_boundary.version}`}</p>
  </section>;
}
