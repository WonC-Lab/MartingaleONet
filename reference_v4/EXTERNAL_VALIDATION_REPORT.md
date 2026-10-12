# QuantLib 1.41 최종 외부 검증

**planned=8, attempted=8, complete=true**를 최종 raw 파일에서 확인했습니다. 6개 positive-v 사례는 analytic/A/B/MP 가격 예산과 마지막 두 analytic refinement를 통과합니다. exact-v0 2개는 UNSUPPORTED_BY_QUANTLIB이며 모델 불일치로 세지 않습니다. 에러 기록도 삭제하지 않습니다.

| 사례 | analytic/A gap | analytic/B gap | analytic/MP gap | analytic 판정 | PDE level | final PDE price gap |
| --- | --- | --- | --- | --- | --- | --- |
| easy_ATM | 2E-17 | 2E-17 | 1.508935257116289231010762929925385717225188249715522033978014409181600921072832178284975872033711225546429E-16 | PASS | 14 | 1.962457761E-8 |
| deep_OTM | 1.18942590E-16 | 3.70943995E-16 | 1.87120427606775628052049977733879968755338733269670734781141677569604747353631977806390988512969095121620497805E-17 | PASS | 13 | 1.45190100915415E-10 |
| deep_ITM | 5E-16 | 0E-15 | 2.2131980942971291709939297916259762039879260776447148832560088144964952929241010615772119584481837979664E-16 | PASS | 15 | 4.947235287E-7 |
| short_core | 1.09E-16 | 2E-18 | 4.526937956719738362059352126441279173053754673728353202942293593673885693103203547855902986533317273253551E-17 | PASS | 13 | 4.6502040023E-9 |
| high_vol_of_vol | 6E-17 | 0E-17 | 9.444683930329711697171256194581523367776607229399233717568372291277412583863670848995604894694250529454E-18 | PASS | 15 | 1.3468615324E-7 |
| near_Feller | 1.4E-16 | 3E-17 | 1.677842603729394327829096369169788981318278288487968266155798621559100045384909234019182893909552752736914E-16 | PASS | 14 | 2.194080457E-8 |
| severe_failed | — | — | — | UNSUPPORTED_BY_QUANTLIB | 0 | — |
| zero_short_R0 | — | — | — | UNSUPPORTED_BY_QUANTLIB | 0 | — |


Actual365Fixed, NullCalendar, q=0, 2026-10-07 평가일과 정렬된 maturity를 확인했습니다. short-core의 비정수 날짜는 기록된 exact deterministic process time change를 사용합니다. 모든 engine setting과 원래/매핑 입력을 보존했습니다.

PDE는 6개에서 실제 time/spot/variance 축 및 큰 combined grid가 실행됐습니다. level 수 14,13,15,13,15,14 (합84). 큰 grid를 건너뛴 경우 원래 코드의 중단 사유도 기록되어 있습니다. execution complete는 PDE convergence certificate를 의미하지 않습니다. R5의 마지막 (1600,6400,800) 가격 차이는 reference 예산을 조금 초과합니다. 최근 spot grid price 변화 2.2644710e-7,5.6570337e-8로 감소하지만 time/variance 잔여 오차도 분리해야 합니다. PDE Gamma/Delta와 모든 이전 grid 값을 EXTERNAL_RECONCILIATION.json 및 REFERENCE_UNCERTAINTY.json에 보존합니다.

원래 reference engine specification은 PDE를 자체 측정 격자 오차로 평가하는 삼각 검증으로 정의합니다. 따라서 PDE를 절대 정답이나 certified training label로 대체하지 않습니다. 새로운 PDE error band 또는 threshold를 발명하지 않으므로 PDE는 REVIEW_REQUIRED입니다.
