# P2-41 보상 계측 검증

최초2attempt는명시적chain CLI에지지면옵션이없어시뮬레이터시작전거부됐다. 원본로그/LOST기록을보존했다. 기존native평가와같이config의chain설정을사용한retry1두개는정상종료했다. 보상/정책/성공기준변경없음.

scripts/p2_41_report.py 검증:동일scenario,episode모든필드,chain-events,모든motion-trace배열이계측전후정확일치. 각50Hz step 성분합과실제reward 최대오차seed1 9.54e-7,seed3 2.38e-7. 전체first episode mask/길이/누적return검사및32가아닌이번2영상MP4/events hash/64camera4검증통과. run artifact감사로보상JSON/NPZ도검증한다. 근거 [진단 결과](p2-41-reward-diagnosis.json).

seed1은두도약64/64성공,평균총reward67.1107. 성분dense-1.2945,flight6,contact8,success16,apex6,firsttouch15.0547,travel17.3506이다. seed3은첫도약거리부족으로64개모두timeout,평균16.9524: dense-1.6019,flight3,contact4,success0,failure0,apex3,firsttouch7.5774,travel.9770. 성공보상이잘못지급된증거는없다. timeout은failure종료와다르므로failure페널티가0인것은현재계약에맞는다.

성공은두도약/실패는한도약이므로총reward차이를정책선호의인과근거로삼지않는다. 실패에도형상화보상이남는다는것은관측했지만그자체로보상버그이거나학습실패원인이라고단정하지않는다. dense는연속비용전체묶음이며개별비용기여분해는아니다.

다음은성공모델의첫도약과실패모델의첫도약을동일범위로집계하고,동일checkpoint의성공/실패사례를가능한범위에서분리한다. 그후거리부족종료에대한학습신호를바꿀필요가있는지사전가설을정한다. 계측파일은원본eval artifacts에보관되고run hash에연결됐다. 새학습은시작하지않았다.


## 첫 도약 범위 비교

scripts/p2_41_first_hop.py로 chain-events의첫도약종료step까지(종료step포함)성분을분리하고hop return과합계일치를검증했다. [결과](p2-41-first-hop.json). 성공seed1은62step/평균33.7642점,실패seed3은200step/16.9524점. gamma.99의관측reward할인합도21.6689 대12.8983으로성공쪽이높다. 이계산은critic bootstrap을포함하지않으며 PPO advantage가아니다. 서로다른두정책자료만으로정책탐색의인과원인을확정하지않는다.

## 시간 초과의 학습 처리 확인

설치된rsl_rl PPO.process_env_step 원문과 scripts/train.py를확인했다. train은모든trunc를time_outs로전달하고,PPO는timeout에gamma×transition.values(행동전가치추정)를reward에더한다. ChainedProgress는hop_steps200기한까지미완수한경우도timeout으로분류한다. 따라서이번raw보상성분만으로실제PPO학습표적을설명할수없다.

고정된4초이내도약완료가과제자체의deadline이라면그미완료를외부수집시간제한과동일하게bootstrap하는것은재검토대상이다. 현재이를학습실패원인또는확정된버그로단정하지않는다. 다음비교에서는보상수치나성공조건을바꾸지않고과제deadline의bootstrap여부만분리하는명시적계약을검토한다. 학습을시작하기전에외부시간제한/과제deadline/worker종료경계를문서화하고구현시험과사전프로토콜을확정한다.
