# P2-29 새 학습 분기 검증

train.py --fork-from을추가하고--resume와상호배타로정의했다. fork는동일seed와호환되는로봇/관측/보상/PPO설정을요구하며,지형/목표분포/커리큘럼/탐색일정/분기예산등명시된항목만변경한다. 부모continuous에서continuous/split으로의분기만현재지원한다. 호환성검사와model/normalizer전체tensor의key/shape/dtype/유한성검사를모두끝낸후복사한다.

정책·critic·normalizer를복사하고optimizer/RNG는새실행초기화를유지한다. std_cap/floor는새분기분포설정으로적용한다. 학습전checkpoint000000에부모hash/규약/부모step/새0step을저장하고이후checkpoint및resume에도lineage를유지한다. 기존restore의엄격한동일조건검사는변경하지않았다.

65unit통과 artifacts/p2-29-fork-tests.log. 실제continuous/split64env3update각각완료·auto평가/영상생성,4artifact감사통과 artifacts/p2-29-fork-smoke-audit.jsonl. 학습전checkpoint000000에서부모model(새std_cap제외)/normalizer모든tensor정확일치,optimizer state빈값,completed/steps0을직접검증했다.3update후신규4608step과부모계보일치/탐색상한.1→.05→.05확인.

split smoke checkpoint3에서resume2update수행,실제update4/5및누적7680step·동일lineage보존확인.별도artifact감사통과 artifacts/p2-29-fork-resume-audit.jsonl. 짧은검증run의성공수는연구성능근거로사용하지않는다.

아직평가전용거리override와full8학습/평가배치가구현되지않았다. 이부분을검증한후본학습을시작한다.
