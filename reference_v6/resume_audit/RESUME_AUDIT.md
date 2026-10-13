# 재개 기능 감사 및 수정

생산 128개 가격 계산은 실행하지 않았다. Google Drive 원본을 읽고 로컬
복사본에서 검사했다. 동결된 프로토콜, 입력, 임계값, acceptance 식은 그대로다.

## 실제 Drive 증거

현재 Drive RUN_IDENTITY는 프로토콜 `15a8e1f8...f273b`, 입력
`5268bcec...9c1a1`, 원래 backend `1acfa66d...996a9`, runner
`3a37abbe...6ecb2`를 기록한다. 현재 ENVIRONMENT의 Git 커밋은
`ab9f4fb7c3e2da65471aaf325daa9fb27801bd5c`다. EXECUTION.log의 다섯
명령은 모두 `/content/drive/MyDrive/MartingaleONet/reference_v6_colab`을
사용했다. PREFLIGHT.log의 다섯 검사는 성공했다.

Drive의 과거 RUN_IDENTITY/ENVIRONMENT revision 목록은 확인했지만, 연결
도구가 JSON revision 본문을 읽지 못했다. 따라서 과거 커밋과 해시를 각각
직접 읽어 동일성을 증명한 것은 아니다. 원래 runner는 해시 불일치 시
명시적으로 중단하며, 체크포인트를 조용히 무시하는 코드가 없다.

| 케이스 | 마지막 저장된 상태 | 마지막 시도 raw 재사용 조회 | 신규 완료 저장 | 그 시도의 로그에서 확인된 신규 저장 |
|---|---|---:|---:|---:|
| v6_01_0 | NUMERICAL_UNRESOLVED | 1101 | 29 | 29 |
| v6_01_1 | PASS | 524 | 119 | 69 |
| v6_01_2 | PASS | 250 | 42 | 42 |

재사용 수는 고유 파일 수가 아니라 조회 횟수다. v6_01_1의 저장된 stats와
로그 개수 차이는 설명되지 않았다. stdout 캡처 누락이나 남은 프로세스의
계산 가능성이 있으며, 동시 실행이 있었다고 확정하지는 않았다.

첫 재실행 로그에서 v6_01_0의 첫 신규 E1은 cutoff 262144/degree24/dps120,
v6_01_1은 cutoff512/degree64/dps120, v6_01_2는 E2 N16384/L16/dps120이다.
v6_01_0의 다음 재실행 첫 신규 E1은 cutoff65536/degree64/dps50이다.
처음의 provisional cutoff256/dps80을 전부 새로 계산한 로그와는 다르다.

세 케이스에서 각각 12개, 총 36개 실제 완료 raw 파일을 가져왔다. 해시와
기존 키를 검증한 뒤 수정된 CaseRunner에 넣었다. 계산 함수를 예외로 막은
상태에서 36개 모두 REUSED로 반환했고 파일 바이트도 보존했다. E1과 E2
양쪽 경로가 포함된다. 실제 partial 6개는 checksum과 MP tuple 구조를
검사했으며, 생산 입력에 partial 계산을 이어서 수행하지는 않았다.

`VERIFIED_SUBEVALUATIONS.csv/json`에는 이 36개의 정확한 key, E1/E2 설정,
모든 좌표, 생성/수정 시각, 저장된 실행 시간, 재사용 검사 결과가 있다.
`LEGACY_NEW_SESSION_CONFIGS.csv`는 세 케이스의 기존 로그를 세션별로
분리한 전체 설정 목록이다. `OBSERVED_PRODUCTION_AUDIT.json`에 세션별
상세 집계와 증거 한계를 보존했다.

**정확히 같은 sub-evaluation의 생산 재계산은 현재 증거로 확정하지 못했다.**
원래 로그는 key와 좌표 및 cache-hit 기록이 없어 같은 config가 다른 물리/
시간 stencil인지 구별할 수 없다. 원격 folder 읽기는 최신100 항목으로
제한된다. 낭비 시간을 0초라고 단정하거나 config 반복 시간의 합을 낭비
시간으로 보고하지 않았다. 정확한 낭비 시간은 현재 산출 불가다.

## 확인한 재개 결함과 수정

1. 원래 미완료 케이스는 run/physical/converge/time 함수를 처음부터
   재진입했다. 완료 raw 값은 재사용하지만 refinement 위치와 파생 상태는
   복원하지 않았다. prefix, 물리 FD step, 축/level, time j/E1/E2/candidate를
   checksum으로 보호한 journal에 저장한다. 다음 누락 단계부터 재개한다.
2. 구 형식에는 cursor가 없다. `hydrate_legacy`가 완료 raw 파일을 한 번
   읽어 cursor를 만들고 첫 누락 raw에서 멈춘다. 계산 호출은 차단되어 있다.
   기존 RESULT/trace/raw/partial/identity는 덮어쓰거나 삭제하지 않는다.
3. partial 합은 원래도 복원됐지만 이미 계산한 COS 계수까지 생성하며
   지나갔다. 이제 저장된 node 뒤에서 시작하며 CF와 COS 계수를 재평가하지
   않는다. E1의 quadrature 순서와 E2의 COS 합산 순서는 그대로다.
4. 원래 Colab Stop 예외 경로는 Popen의 자식 pool을 종료하지 않았다.
   노트북 중단 시 process group을 종료한다. 로컬 kernel lock과 Drive
   heartbeat lease로 같은 출력에 여러 writer가 붙는 것을 차단/감지한다.
   다른 VM의 Drive mount는 지연될 수 있으므로 동시 시작은 금지한다.
5. 기존 정확한 raw key/schema와 원래 RUN_IDENTITY를 보존한다. 실제 사용된
   ab9f4fb 소스 해시만 명시적으로 호환시킨다. 임의의 다른 해시는 거부한다.
   변경된 코드/커밋은 sessions별 compatibility/환경 receipt에 따로 기록한다.
6. 모든 raw 작업에 key와 전체 좌표를 포함한 REUSED/NEW/PARTIAL_RESUMED/
   COMPLETED 이벤트를 저장한다. 이전보다 짧은 trace로 과거 기록을 자르지
   않는다. 기존 과학적 판정과 확정된 FAIL은 자동 재실행하지 않는다.
7. 검증한 완료 raw의 byte hash를 별도 catalog에 보존한다. 새 Drive mount에서
   해당 파일이 일시적으로 보이지 않으면 PENDING으로 멈추며, 이미 완료된
   계산을 NEW로 다시 실행하지 않는다. 부분적으로 보이는 mount를 재계산으로
   보상하지 않는다.

## 테스트와 실행 범위

테스트 입력은 합성 입력뿐이다. 중단/재개 결과를 원래 runner와 비교했고
scientific 결과가 일치했다. 완료 raw 파일의 계산 호출은 0회였다. 구 코드가
만든 E1/E2 partial을 이어서 계산한 결과는 중단 없는 구 코드와 정확히
일치했고, CF 호출 수는 남은 node 수와 같았다. 합성 구 케이스의 cursor
hydration도 가격 호출 없이 첫 누락 key를 찾았다.
총 14개 테스트가 통과했으며 raw catalog의 파일 가시성 실패에서도 계산
함수가 호출되지 않는 것을 확인했다.

실제 Colab 프로세스 그룹 종료는 이 Windows 로컬 환경에서 실행한 검사가
아니다. 실제 Drive 전체 파일을 검증할 수 있도록 Colab에 read-only audit
셀을 추가했다. 노트북은 audit-only가 기본이며 생산 재개 flag는 False다.
