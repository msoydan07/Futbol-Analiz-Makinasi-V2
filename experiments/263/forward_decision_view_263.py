"""Read-only experimental result screen for forward decision candidates."""
from __future__ import annotations
def render(decision:dict)->str:
    if decision.get("schema")!="263_forward_decision_candidate_v1":
        raise ValueError("WRONG_DECISION_SCHEMA")
    if decision.get("betting_authorized") is not False or decision.get("pilot_count_increment")!=0 or decision.get("official_S1") is not None or decision.get("official_S2") is not None:
        raise ValueError("UNSAFE_OFFICIAL_CLAIM")
    status=decision.get("status")
    if status not in ("RESEARCH_PAS","RESEARCH_CANDIDATE_NOT_APPROVED"):
        raise ValueError("INVALID_STATUS")
    lines=["# Futbol Maç Analiz Makinası 2.6.3 — Deneysel Sonuç",
           "", "**RESMÎ TERCİH YOK — araştırma ekranı.**",
           "",f"Kilitli kayıt: `{decision['immutable_record_id']}`",
           "", "Bu gösterim bahis önerisi, resmî S1/S2 veya pilot kaydı değildir.",""]
    if status=="RESEARCH_PAS":
        if decision.get("main_candidate") is not None or decision.get("alternative_candidate") is not None:
            raise ValueError("PAS_WITH_PICK")
        lines+=["## PAS", "Neden: "+", ".join(decision.get("pas_reasons",[])),""]
    else:
        main=decision.get("main_candidate")
        if not isinstance(main,dict) or decision.get("pas_reasons"):
            raise ValueError("CANDIDATE_INCONSISTENT")
        lines+=["## Ana aday (onaysız)",f"{main['market']} — kalibre %{100*main['calibrated_probability']:.1f}",""]
        alt=decision.get("alternative_candidate")
        if alt is not None:
            if alt["family"]==main["family"]:
                raise ValueError("CORRELATED_ALTERNATIVE")
            lines+=["## Alternatif aday (onaysız)",f"{alt['market']} — kalibre %{100*alt['calibrated_probability']:.1f}",""]
        else:
            lines+=["Alternatif aday yok: yeterli ayrı pazar ailesi kanıtı bulunmadı.",""]
    lines+=["**Oran/EV:** doğrulanmadı; değer seçimi yapılmadı.",
            "**Karar durumu:** ileri test araştırması; canlı motor değiştirilmedi."]
    return "\n".join(lines)+"\n"
