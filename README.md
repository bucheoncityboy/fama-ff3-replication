# Fama-French (1993) 과제 제출 패키지

이 저장소는 **Fama & French (1993)** 논문의 핵심 표를 과제 제출 형식으로 재현한 결과물이다. 현재 저장소는 연구용 `output/` 기준이 아니라, **과제 제출용 `appendix_output/`만 공식 산출물로 사용하는 구조**로 정리되어 있다.

---

## 1. 과제 제출 기준

- 공식 제출 산출물 디렉토리: `appendix_output/`
- 공식 제출 문서: 이 `README.md`
- 표별 포함/제외 감사 문서: `TABLE_COVERAGE_AUDIT.md`
- 공식 빌드 스크립트: `build_submission.py`

과제 제출은 아래 한 줄로 재생성할 수 있다.

```bash
python build_submission.py
```

이 명령은 다음 스크립트를 순서대로 실행한다.

1. `01_section2_factors.py`
2. `01b_section2_bond_factors.py`
3. `02_section2_portfolios.py`
4. `02b_section2_bond_portfolios.py`
5. `07_section0_descriptive_stats.py`
6. `08_section8a_rmo_regressions.py`
7. `09_section11_ep_dp_portfolios.py`
8. `10_appendix_table_exports.py`

---

## 2. 어떻게 구현했는가

### 2.1 주식 측 포트폴리오와 요인

- `compustat_portfolio_builder.py`가 Compustat BE와 CRSP 원시 데이터로 25개 Size×BE/ME 포트폴리오와 6개 포트폴리오를 구축한다.
- BE는 `compustat_be.csv`의 pre-computed 값을 사용한다.
- gvkey↔PERMCO 오픈 매핑과 CRSP PERMCO/PERMNO를 연결해 1964-07 이후 구간을 자체 구축했다.
- 1963-07~1964-06은 논문 방법론상 필요한 1962년 BE가 없어 hybrid seed 구간으로 유지한다.

### 2.2 채권 측 요인과 프록시

- TERM, DEF는 FRED 시계열로 구성했다.
- 채권 포트폴리오는 실제 CRSP 채권 수익률이 아니라 yield-based proxy다.
- 따라서 채권 관련 표는 “논문 원본 수치와의 기계적 일치”보다는 **주식과 다른 위험요인 구조가 나타나는지**를 확인하는 용도로 사용했다.

### 2.3 과제 제출 표 생성

- `10_appendix_table_exports.py`가 `appendix_output/` 아래에 과제 제출용 표를 다시 정리한다.
- 이 스크립트는 연구용 전체 패널을 그대로 노출하지 않고, **가이드 문서에서 포함하라고 한 표만 별도 파일로 분리**한다.
- 제외 대상으로 표시된 채권 하위표(Table 3 bond block, Table 7b 등)는 제출용 디렉토리에서 제외했다.

---

## 3. 논문의 어떤 부분을 어떻게 증명했는가

아래 표는 “논문 주장 → 구현 방식 → 제출 파일 → 증명 포인트”를 연결한 것이다.

| 논문/가이드 항목 | 구현 파일 | 제출 파일 | 무엇을 증명하는가 |
|---|---|---|---|
| Table 1 (1)(2) | `07_section0_descriptive_stats.py` | `appendix_output/table1_panel1_firm_count_market_cap.csv`, `appendix_output/table1_panel2_cap_share_firm_count.csv` | 25개 포트폴리오가 실제로 형성되었고, size 정렬과 시총 비중 구조가 살아 있음을 보임 |
| Table 2 (요인/주식 기술통계) | `01_section2_factors.py`, `02_section2_portfolios.py`, `10_appendix_table_exports.py` | `appendix_output/table2_panel1_factor_summary.csv`, `appendix_output/table2_panel1_correlation_matrix.csv`, `appendix_output/table2_panel2_stock_mean_std.csv`, `appendix_output/table2_panel3_stock_tstats.csv` | 시장, SMB, HML, TERM, DEF의 평균과 분산, 그리고 25개 주식 포트폴리오의 수익률 패턴을 확인 |
| Table 3 | `10_appendix_table_exports.py` | `appendix_output/table3_panel1_m_t_m.csv`, `appendix_output/table3_panel2_d_t_d.csv`, `appendix_output/table3_panel3_r2_se.csv` | TERM/DEF가 주식 수익률에는 약한 설명력만 가진다는 점을 보여줌 |
| Table 4 | `04_section4_regressions.py`, `10_appendix_table_exports.py` | `appendix_output/table4_panel1_b_t_b.csv`, `appendix_output/table4_panel2_r2_se.csv` | 시장 요인 하나만으로는 주식 수익률 설명력이 제한적임을 보임 |
| Table 5 | `10_appendix_table_exports.py` | `appendix_output/table5_panel1_s_t_s.csv`, `appendix_output/table5_panel2_h_t_h.csv`, `appendix_output/table5_panel3_r2_se.csv` | SMB/HML이 가치·규모 효과를 반영한다는 점을 보임 |
| Table 6 | `04_section4_regressions.py`, `10_appendix_table_exports.py` | `appendix_output/table6_panel1_b_t_b.csv`, `appendix_output/table6_panel2_s_t_s.csv`, `appendix_output/table6_panel3_h_t_h.csv`, `appendix_output/table6_panel4_r2_se.csv` | 3요인 모형이 주식 횡단면 설명력을 크게 개선한다는 점을 보임 |
| Table 7a | `04b_section4_five_factor.py`, `10_appendix_table_exports.py` | `appendix_output/table7a_panel1_b_t_b.csv` ~ `appendix_output/table7a_panel6_r2_se.csv` | 5요인 모형에서 TERM/DEF를 추가해도 주식 설명력 개선은 크지 않음을 보임 |
| Table 8a | `08_section8a_rmo_regressions.py`, `10_appendix_table_exports.py` | `appendix_output/table8a_panel1_b_t_b.csv` ~ `appendix_output/table8a_panel6_r2_se.csv` | RMO가 다른 4요인과 직교하고, 직교화 이후에도 주식 수익률 설명력이 유지됨을 보임 |
| Table 9a | `05b_section5_intercepts.py`, `10_appendix_table_exports.py` | `appendix_output/table9a_stock_alphas.csv` | 각 모형의 절편(alpha)이 어떻게 줄어드는지 비교해, 3요인/5요인 모형의 pricing error를 평가 |
| Table 9c | `05_section5_grs_test.py`, `10_appendix_table_exports.py` | `appendix_output/table9c_joint_tests.csv` | 절편이 공동으로 0인지 F-test로 검정해 모형의 공동 설명력을 평가 |
| Table 11 | `09_section11_ep_dp_portfolios.py` | `appendix_output/table11_ep_dp_long.csv` | E/P, D/P 정렬 포트폴리오에서도 CAPM보다 FF3F가 설명력을 높인다는 점을 보임 |

---

## 4. 과제 제출 결과 요약

### 4.1 Size / Value 효과

- 25개 주식 포트폴리오 평균 초과수익률에서 **HiBM > LoBM** 패턴이 5개 size 그룹 모두에서 확인된다.
- **Small > Big** 패턴도 전반적으로 유지되어 규모 효과가 재현된다.

### 4.2 요인 프리미엄

- `Mkt-RF = 0.42%/월`
- `SMB = 0.29%/월`
- `HML = 0.41%/월`

이 값들은 README 이전 버전 기준 비교에서도 논문 수치와 매우 가까웠고, 과제 제출용 표 생성 과정에서도 동일한 원천 데이터를 사용한다.

### 4.3 3요인 모형의 증명

- 주식 평균 R²는 약 `0.8992`
- 1요인 대비 개선폭은 약 `+14.6pp`

즉, 시장요인 하나만으로는 부족하지만 SMB와 HML을 추가하면 주식 수익률 설명력이 크게 좋아진다. 이것이 논문의 핵심 주장 중 하나다.

### 4.4 5요인 모형의 해석

- 주식 평균 R²는 약 `0.8999`
- 3요인 대비 개선폭은 약 `+0.07pp`

즉, TERM/DEF를 주식 포트폴리오에 더해도 개선이 매우 작다. 이는 논문이 말하는 “채권 요인은 주식 설명에 큰 추가 기여를 하지 않는다”는 주장과 방향이 같다.

### 4.5 GRS / 절편 분석으로 본 증명

- `appendix_output/table9a_stock_alphas.csv`는 개별 절편을 보여준다.
- `appendix_output/table9c_joint_tests.csv`는 절편이 공동으로 0인지 검정한다.

여기서 3요인과 5요인 결과를 비교하면, 단순 CAPM보다 다요인 모형이 pricing error를 줄인다는 점을 확인할 수 있다.

---

## 5. 제외 표는 어떻게 처리했는가

가이드 문서 `Fama-French 1993 재현 및 정리.md`에서 제외 대상으로 명시한 항목은 제출용 디렉토리에서 분리했다.

예:

- Table 3 bond block
- Table 4 bond block
- Table 5 bond block
- Table 6 bond block
- Table 7b
- Table 8b
- Table 9b
- Table 10

이 원칙은 `TABLE_COVERAGE_AUDIT.md`와 `appendix_output/README.md`에 다시 정리해 두었다.

---

## 6. 제출 시 보면 되는 파일

가장 중요한 제출 파일은 아래다.

- `appendix_output/table1_panel1_firm_count_market_cap.csv`
- `appendix_output/table1_panel2_cap_share_firm_count.csv`
- `appendix_output/table2_panel1_factor_summary.csv`
- `appendix_output/table2_panel1_correlation_matrix.csv`
- `appendix_output/table2_panel2_stock_mean_std.csv`
- `appendix_output/table2_panel3_stock_tstats.csv`
- `appendix_output/table3_*`
- `appendix_output/table4_*`
- `appendix_output/table5_*`
- `appendix_output/table6_*`
- `appendix_output/table7a_*`
- `appendix_output/table8a_*`
- `appendix_output/table9a_stock_alphas.csv`
- `appendix_output/table9c_joint_tests.csv`
- `appendix_output/table11_ep_dp_long.csv`

---

## 7. 남은 주의사항

- Table 1 panel 3의 25셀 E/P·D/P는 저장소에 원천 기업수준 입력이 없어, 가이드 문서 기준값을 reference snapshot으로 제공했다.
- Table 9c의 bootstrap probability level은 별도 시뮬레이션을 다시 붙이지 않았기 때문에 공란으로 남겨두고, F-distribution 기반 검정 결과를 제공했다.
- 채권 측 결과는 proxy 기반이므로, 주식 측만큼 원 논문과 직접 비교하면 안 된다.

---

## 8. 검증

최종 검증:

```bash
python build_submission.py
python -m pytest -q
```

최근 검증 결과:

- `python -m pytest -q` → `274 passed, 1 skipped`

---

## 9. 참고 문서

- 과제 기준표: `Fama-French 1993 재현 및 정리.md`
- 커버리지 감사: `TABLE_COVERAGE_AUDIT.md`
- 제출 산출물 인덱스: `appendix_output/README.md`
