# Working instructions — Futbol 2.6.3 (experimental branch)

Before any 10-league match analysis, model/odds/decision edit, handoff or report:

1. Open `docs/263_AKTIF_KARARLAR.json` FIRST. It is the single active decision index. Read its `active`, `superseded_for_pdf_first` and `validation_status` fields. Do not infer current policy from an older document's filename, its creation date, or its existence.
2. Run `python experiments/263/check_active_decisions_263.py` before new first-PDF execution. If exit != 0, **STOP; report the conflict and do not automatically fall back to legacy code**. This check validates the active decision contract, not live end-to-end success.
3. Old documents, modules and SHA-locked forecast records remain intact as historical evidence. The old EV-/odds-gated PDF-first decision is superseded; it is NOT the currently approved first-PDF route.
4. Current new first-PDF path: `iddaa_pdf_one_step_263.py` → `model_first_iddaa_bridge_263.py` → `model_first_decision_263.py`. M4 for one coherent MS 1/X/2 distribution; C3 raw for KG and 2.5 Alt/Üst; B/C2 are independent supporters. M4 is **xG-free**. Odds only compare **after** the model-only sealed decision. Second PDF is observation-only.
5. A new user decision must explicitly supersede the older decision for the **same topic and scope**. Update the active index and the old decision's archival label; add date and change rationale. Keep one ACTIVE decision per topic. Never silently revive an old selector, never silently promote research-only shadow calibrations or xG.
6. Distinguish (A) a recorded decision, (B) implemented-and-tested code and (C) verified real match-day operation. No real live certification merely from a green unit test. Technical BLOCKED is never model PAS.
7. Do not edit `main`, previously SHA-sealed forecasts, frozen B/C2/C3/M4 formulas, basketball/LITE repositories, or historical evaluations as a side effect of governance work.

These instructions guide work in this repository; they do not make ChatGPT memory, GitHub branch protection, or every separate historical workflow automatically enforce the policy. Check the actual entrypoint before claiming a workflow is protected.
