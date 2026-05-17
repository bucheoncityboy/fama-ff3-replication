# Appendix Table Coverage Audit

Reference: `Fama-French 1993 재현 및 정리.md`

This file checks whether the repository implementation follows the appendix table focus, and whether explicitly excluded tables were actually left out.

## Summary

| Table | Appendix intent | Current repo status | Verdict |
|---|---|---|---|
| Table 1 (1)(2) | Include 25 stock portfolio descriptive cells | `07_section0_descriptive_stats.py` + `output/table0_descriptive_stats.csv` covers average firm count / market cap / cap share | Partial |
| Table 1 (3) | Include annual E/P and D/P by 25 size-BE/ME cells | Not implemented in appendix-table form | Missing |
| Table 2 (1) | Include factor summary + autocorrelation + correlation matrix | `03_section3_statistics.py` covers means/std/t-stats only; autocorrelation/correlation matrix not separately exported | Partial |
| Table 2 (2)(3) | Include 25 stock excess return mean/std/t-stat cells | Covered in `output/table2_summary.csv` and README summary | Partial |
| Table 3 stock block | Include 25 stock TERM/DEF regressions | Present inside `output/table3_bond.csv` | Partial |
| Table 3 bond block | Exclude | Still present inside `output/table3_bond.csv` master output | Not excluded in file |
| Table 4 stock block | Include 25 stock market-only regressions | Present inside `output/table1_market.csv` | Partial |
| Table 4 bond block | Exclude | Still present inside `output/table1_market.csv` master output | Not excluded in file |
| Table 5 stock block | Include 25 stock SMB/HML regressions | Present inside `output/table5_smbhml.csv` | Partial |
| Table 5 bond block | Exclude | Still present inside `output/table5_smbhml.csv` master output | Not excluded in file |
| Table 6 stock block | Include 25 stock FF3 regressions | Present inside `output/table4_stock3f.csv` | Partial |
| Table 6 bond block | Exclude | Still present inside `output/table4_stock3f.csv` master output | Not excluded in file |
| Table 7a | Include 25 stock FF5 regressions | Present inside `output/table5_five_factor.csv` | Partial |
| Table 7b | Exclude | Bond rows still present inside `output/table5_five_factor.csv` master output | Not excluded in file |
| Table 8a | Include stock RMO regressions | `08_section8a_rmo_regressions.py` + `output/table8a_rmo.csv` | Covered |
| Table 8b | Exclude | No separate appendix-facing Table 8b output created | Excluded |
| Table 9a | Include stock alpha/t(alpha) across models | `output/intercept_analysis.csv` contains raw alpha results, but not appendix matrix layout | Partial |
| Table 9b | Exclude | Bond alpha rows still present in `output/intercept_analysis.csv` master output | Not excluded in file |
| Table 9c | Additional attempt | `output/grs_test_results.csv` gives joint alpha tests, but not bootstrap version from note | Partial |
| Table 10 | Exclude | No implementation/output | Excluded |
| Table 11 | Additional attempt | `09_section11_ep_dp_portfolios.py` + `output/table11_ep_dp.csv` | Covered |

## What was clearly done around the requested table-focused scope

- Added `07_section0_descriptive_stats.py` for Appendix Table 1 style descriptive outputs.
- Added `08_section8a_rmo_regressions.py` for Appendix Table 8a.
- Added `09_section11_ep_dp_portfolios.py` for Appendix Table 11.
- Updated `README.md` so GitHub now exposes that this repo follows the appendix table focus only partially, with an explicit audit trail.

## Important caveat

Several regression CSVs are still **research/master outputs**, not strict appendix-facing exports. That means they include both:

1. the stock block that the appendix wants to keep, and
2. the bond block that the appendix explicitly marks as excluded.

This affects:

- `output/table3_bond.csv`
- `output/table1_market.csv`
- `output/table5_smbhml.csv`
- `output/table4_stock3f.csv`
- `output/table5_five_factor.csv`
- `output/intercept_analysis.csv`

So the current repository is **good for research replication**, but only **partially cleaned for appendix-only homework presentation**.

## Bottom line

- **Yes**: the work did proceed table-first, especially for Table 8a and Table 11.
- **Partly**: several core tables are implemented but not separated into appendix-only stock blocks.
- **No**: excluded bond subtables were not fully removed from every output file; they remain in master CSVs.

If needed next, the repo should add appendix-facing filtered exports so that included tables and excluded tables are separated at the file level, not just explained in README.
