# Phase 1B.4 증거 조정

| 단계 | 증거 | 당시 유효한 결론 |
| --- | --- | --- |
| 초기 로컬 Phase 1B.3 | CORE 1734, boundary 600; MP 179/1557; 실패 173개 해결, 1374개 미해결 | CORE 전수 계산 완료, 인증 미완료 |
| 이전 Colab ZIP | SHA256 2f5c5a78f2de…; 345 entries; 12,854,380 bytes; 새 MP 로그 48개; 최종 보고서 없음 | 중간 체크포인트 판정은 당시 맞았으며 과거 기록을 변경하지 않음 |
| 후속 계산 | CORE MP1557; boundary MP566; limiting PDE210; continuity15 sequences; external8 attempts | 체크포인트와 최종 구조화 증거가 있는 실제 후속 실행 |
| 이번 최종 ZIP | SHA256 c1049e1053f6ed94fadd41f244cfd5c5cfc43bcee740070ea5db0d89ee1ca77e; 2722 entries; 92,322,839 bytes | CORE 원시 해시 유지; 최종 출력과94개 PNG/PDF 파일 존재 |
| Phase 1B.4 | 저장 스텐실/축 변화를 Decimal로 재계산; 가격 엔진 호출 없음 | CORE1734/0 해결/미해결; boundary 수치600/0, 호환성 검토 필요; Phase1C NO |


이전 중간 ZIP에 대한 미완료 판단은 당시 증거에 맞았습니다. 후속 증거가 생겼다고 과거 판단을 잘못된 것으로 바꾸지 않습니다. 초기 strict PASS 187 / FAIL 1547도 그대로 보존합니다.

후속 커밋 f3c62f2는 51a5cf4의 후손입니다. 증거 재사용 receipt가 immutable_zip 및 283개 검증을 기록합니다. CORE MP 계획 1557개는 반환 체크포인트 1552개와 SHA 검증된 Phase 1B.2 원시 증거 5개로 충족됩니다. 전체 HP JSON의 rows 2122는 CORE와 boundary 및 중복 revision을 포함하므로 CORE 분모로 사용하지 않습니다.

기존 CORE FAIL을 입력으로 쓰지 않고 raw axes와 물리 FD 스텐실을 재계산했습니다. R5는 A/B/MP/analytic 기준을 통과합니다. 유한 격자 PDE 오차를 reference 예산에 직접 넣은 구분 오류는 v4에서 교정하고, 모든 PDE 값은 별도 불확실성 기록으로 보존합니다.

Phase 1B.3 사용자 지정 외부 범위는 사전 정렬된 8개이며, 예전 design의 256 external 목표를 이번에 완료했다고 주장하지 않습니다. CORE PASS는 변경하지 않은 Domain v1의 1734 catalog와 이 사전 선언된 Phase 1B.3 범위의 수치 인증입니다. 연속 영역에 대한 엄밀한 오차 상한이나 미래 모든 훈련 라벨의 자동 인증이 아닙니다.

| artifact | ZIP 시간(시간대 미기록) | 판정 | 이유 |
| --- | --- | --- | --- |
| HP_core.json | [2026, 10, 10, 9, 21, 6] | CURRENT_RAW_EVIDENCE | 원시 수치와 체크포인트가 계획 및 해시와 대응하며, 완료 여부를 내용으로 검증했습니다. |
| HP_boundary.json | [2026, 10, 10, 9, 22, 28] | CURRENT_RAW_EVIDENCE | 원시 수치와 체크포인트가 계획 및 해시와 대응하며, 완료 여부를 내용으로 검증했습니다. |
| EXTERNAL_RESULTS.json | [2026, 10, 10, 9, 22, 2] | CURRENT_RAW_EVIDENCE | 원시 수치와 체크포인트가 계획 및 해시와 대응하며, 완료 여부를 내용으로 검증했습니다. |
| BOUNDARY_CONTINUITY.json | [2026, 10, 10, 9, 22, 34] | CURRENT_DIAGNOSTIC_STALE_ENDPOINT_TAG | R5 tau=.1은 MP 체크포인트 부재로 v0 UNRESOLVED가 기록됐지만 원래 strict PASS를 재검증했습니다. 연속성 판정 기준은 여전히 없습니다. |
| BOUNDARY_PDE_CHECKS.json | [2026, 10, 10, 11, 44, 28] | CURRENT_RAW_EVIDENCE | 원시 수치와 체크포인트가 계획 및 해시와 대응하며, 완료 여부를 내용으로 검증했습니다. |
| REFERENCE_VALIDATION_REPORT.md | [2026, 10, 10, 11, 44, 40] | MIXED_CURRENT_COUNTS_STALE_PROSE | 1557/1557 집계는 최종 증거와 맞지만 Colab 미실행 및 경계 대기 문구는 완료 증거와 충돌합니다. |
| CORE_DOMAIN_CERTIFICATE.md | [2026, 10, 10, 11, 44, 40] | CURRENT_DATA_CLASSIFIER_LOGIC_ARTIFACT | R5 FAIL은 유한 격자 PDE를 reference gap에 직접 합친 데서 비롯됐습니다. 원래 FAIL을 보존하고 v4에서 별도로 판정합니다. |
| BOUNDARY_REQUIRED_CERTIFICATION.md | [2026, 10, 10, 11, 44, 40] | STALE_HARDCODED_INTERPRETATION | 최종 계산 이후 생성된 보고서지만 템플릿에 MP/PDE pending이 남았습니다. 생성 시점만의 문제가 아닙니다. |
| HIGH_PRECISION_REPORT.md | [2026, 10, 10, 11, 44, 40] | CURRENT_RAW_EVIDENCE | 원시 수치와 체크포인트가 계획 및 해시와 대응하며, 완료 여부를 내용으로 검증했습니다. |
| GREEK_CERTIFICATION.md | [2026, 10, 10, 11, 44, 40] | STALE_HARDCODED_INTERPRETATION | 최종 계산 이후 생성된 보고서지만 템플릿에 MP/PDE pending이 남았습니다. 생성 시점만의 문제가 아닙니다. |
| EXTERNAL_VALIDATION_REPORT.md | [2026, 10, 10, 11, 44, 40] | CURRENT_DATA_STALE_SCOPE_PROSE | 최종 refinement 수치는 유효하지만 일반적인 Colab/pending 설명은 실제 실행 환경에 맞게 갱신되지 않았습니다. |
| CERTIFICATION_RESULTS.json | [2026, 10, 10, 11, 44, 40] | CURRENT_DATA_CLASSIFIER_LOGIC_ARTIFACT | R5 FAIL은 유한 격자 PDE를 reference gap에 직접 합친 데서 비롯됐습니다. 원래 FAIL을 보존하고 v4에서 별도로 판정합니다. |
| FAILURE_RESOLUTION_TABLE.csv | [2026, 10, 10, 11, 44, 36] | CURRENT_DATA_CLASSIFIER_LOGIC_ARTIFACT | R5 FAIL은 유한 격자 PDE를 reference gap에 직접 합친 데서 비롯됐습니다. 원래 FAIL을 보존하고 v4에서 별도로 판정합니다. |
