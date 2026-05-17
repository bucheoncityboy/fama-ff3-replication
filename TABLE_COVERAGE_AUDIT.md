# Table Coverage Audit for Assignment Submission

Reference document: `Fama-French 1993 재현 및 정리.md`

This repository is now organized around **assignment submission outputs only**. The canonical deliverables live in `appendix_output/`.

---

## 1. Coverage summary

| Table | Assignment status | Submission file(s) | Note |
|---|---|---|---|
| Table 1 panel 1 | Covered | `appendix_output/table1_panel1_firm_count_market_cap.csv` | 25 stock cells |
| Table 1 panel 2 | Covered | `appendix_output/table1_panel2_cap_share_firm_count.csv` | 25 stock cells |
| Table 1 panel 3 | Covered with note | `appendix_output/table1_panel3_ep_dp_reference.md` | Reference snapshot because raw 25-cell E/P, D/P inputs are unavailable |
| Table 2 panel 1 summary | Covered | `appendix_output/table2_panel1_factor_summary.csv` | mean, std, t, autocorrelation |
| Table 2 panel 1 correlation matrix | Covered | `appendix_output/table2_panel1_correlation_matrix.csv` | factor correlation matrix |
| Table 2 panel 2 | Covered | `appendix_output/table2_panel2_stock_mean_std.csv` | stock mean/std grid |
| Table 2 panel 3 | Covered | `appendix_output/table2_panel3_stock_tstats.csv` | stock t-stat grid |
| Table 3 stock block | Covered | `appendix_output/table3_*` | stock-only export |
| Table 3 bond block | Excluded | not exported | intentionally omitted |
| Table 4 stock block | Covered | `appendix_output/table4_*` | stock-only export |
| Table 4 bond block | Excluded | not exported | intentionally omitted |
| Table 5 stock block | Covered | `appendix_output/table5_*` | stock-only export |
| Table 5 bond block | Excluded | not exported | intentionally omitted |
| Table 6 stock block | Covered | `appendix_output/table6_*` | stock-only export |
| Table 6 bond block | Excluded | not exported | intentionally omitted |
| Table 7a | Covered | `appendix_output/table7a_*` | stock-only export |
| Table 7b | Excluded | not exported | intentionally omitted |
| Table 8a | Covered | `appendix_output/table8a_*` | stock-only export |
| Table 8b | Excluded | not exported | intentionally omitted |
| Table 9a | Covered | `appendix_output/table9a_stock_alphas.csv` | stock alpha matrix |
| Table 9b | Excluded | not exported | intentionally omitted |
| Table 9c | Covered with note | `appendix_output/table9c_joint_tests.csv` | F-test exported, bootstrap column left blank |
| Table 10 | Excluded | not exported | intentionally omitted |
| Table 11 | Covered | `appendix_output/table11_ep_dp_long.csv` | long-format export |

---

## 2. How the submission package is built

- `build_submission.py` is the official build entrypoint.
- `10_appendix_table_exports.py` is the final formatter that assembles appendix-facing tables.
- Intermediate supporting files are written into the same canonical submission directory, `appendix_output/`.

---

## 3. Notes

1. Table 1 panel 3 is provided as a reference snapshot because the repository does not contain the raw firm-level inputs needed to reconstruct the full 25-cell E/P and D/P grid directly.
2. Table 9c includes F-distribution based joint alpha tests. The bootstrap probability column is left blank rather than filled with fabricated values.
3. Excluded subtables are omitted at the file level in `appendix_output/`, not just hidden in README text.
