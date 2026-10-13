# 기존 Colab 생산 계산 이어가기

1. 기존 계산 셀과 다른 Colab runtime을 모두 종료한다. 기존 notebook의 Stop만
   누르면 구 runner가 남았을 수 있으므로 이전 runtime도 종료한다. Drive의
   `reference_v6_colab` 폴더와 체크포인트는 삭제/이동하지 않는다.
2. GitHub main의 최신 `colab/phase1b6_boundary_certification.ipynb`를 새로
   열고 CPU runtime을 선택한다. 원래와 같은 Google 계정의 Drive를 mount한다.
3. 원래 OUT 값은 `/content/drive/MyDrive/MartingaleONet/reference_v6_colab`이다.
   초기 셀 및 read-only audit 셀만 실행한다. `CHECKPOINTS_ACCEPTED=True`와
   실제 case/raw 개수, 오류 목록이 비었는지 확인한다. 기본값으로 전체 실행해도
   생산 flag가 False여서 계산하지 않는다. 결과는 sibling
   `reference_v6_resume_audit`와 그 ZIP에 저장된다.
4. 감사 내용을 확인한 뒤 `PREPARE_RESUME_JOURNALS=True`로 바꾸고 해당 셀을
   실행한다. 가격 계산 없이 구 raw를 읽어 첫 누락 key/node를 journal에 저장한다.
   HYDRATION_REPORT에서 `production_pricing_calls=0`을 확인한다.
5. 그 뒤 `ALLOW_PRODUCTION_RESUME=True`로 설정하고 생산 재개 셀만 실행한다.
   PASS/기존 확정 FAIL 케이스는 건너뛰며 pending 케이스만 계산한다. NEW 또는
   PARTIAL_RESUMED의 key/node를 HYDRATION_REPORT의 next_missing과 대조한다.
6. 이후에는 같은 OUT에 재개한다. RUN_IDENTITY는 수정하지 않는다. 다른
   runtime은 동시에 실행하지 않는다. 새 runner를 강제 종료했다면 lease가
   남을 수 있다. 다른 runtime이 종료됐고 heartbeat 후 180초가 지난 경우에만
   `TAKEOVER_STALE_LEASE=True` 또는 CLI flag로 명시적으로 인계한다.

터미널에서의 정확한 명령(프로토콜/입력과 수정 커밋을 checkout한 상태):

```
python -m pip install -r reference_v6/requirements-colab.txt
python -m reference_v6.run_boundary_certification --output /content/drive/MyDrive/MartingaleONet/reference_v6_colab --preflight-only
python -m reference_v6.audit_resume --output /content/drive/MyDrive/MartingaleONet/reference_v6_colab --audit-dir /content/drive/MyDrive/MartingaleONet/reference_v6_resume_audit
python -m reference_v6.hydrate_legacy --output /content/drive/MyDrive/MartingaleONet/reference_v6_colab --audit-dir /content/drive/MyDrive/MartingaleONet/reference_v6_resume_audit
python -m reference_v6.run_boundary_certification --output /content/drive/MyDrive/MartingaleONet/reference_v6_colab --workers 4 --execute-frozen-v6
```

마지막 명령은 감사·hydration 확인 후에만 실행한다. worker 수는 가용 CPU에
맞춰 1~4로 설정한다. 30 CPU 분/케이스와 8시간/배치 제한은 그대로다.
처음 감사는 기존 로그의 좌표 누락을 복원하지 못하므로 과거의 정확한 중복/
낭비 시간까지 자동 확정하지 않는다. 이후 실행의 key별 이벤트와 감사의
CHECKPOINT_SNAPSHOT으로 실제 재계산 여부를 비교할 수 있다.
