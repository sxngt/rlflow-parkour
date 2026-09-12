type CourseReport = {
  episodes: number; successes: number;
  completed_hops_histogram?: Record<string, number>;
  chain_contract?: {hops: number; absolute_forward_targets_m?: number[]; step_lengths_m?: number[];
    progress_criterion?: string; spacing_contract?: string; root_boundary?: {version: string}};
};
export function CourseEvaluation({report}: {report: CourseReport}) {
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
