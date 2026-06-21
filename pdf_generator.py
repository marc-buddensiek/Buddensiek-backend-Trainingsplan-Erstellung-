"""
Plan → PDF

Erstellt ein sauber formatiertes PDF für den Klienten.
Verwendung:
  python3 pdf_generator.py output/plan_38ea3675.json
  → Speichert: output/plan_Thomas_Block1.pdf
"""

from __future__ import annotations
import json
import pathlib
import sys
from fpdf import FPDF

from logic.conditioning_formats import CONDITIONING as _CONDITIONING


# ── Farben (Buddensiek-Stil) ──────────────────────────────────────────────────
C_BLACK      = (20, 20, 20)
C_WHITE      = (255, 255, 255)
C_ACCENT     = (220, 53, 34)     # Rot
C_DARK_GREY  = (60, 60, 60)
C_MID_GREY   = (120, 120, 120)
C_LIGHT_GREY = (240, 240, 240)
C_LINE       = (200, 200, 200)


def _clean(text: str) -> str:
    """Ersetze Unicode-Sonderzeichen durch latin-1-kompatible Alternativen."""
    return (text
        .replace("—", " - ")   # em dash
        .replace("–", "-")     # en dash
        .replace("’", "'")     # right single quote
        .replace("“", '"')     # left double quote
        .replace("”", '"')     # right double quote
        .replace("\U0001f4dd", ">") # 📝 Notiz-Emoji
        .replace("→", "->")    # →
        .replace("✓", "ok")    # ✓
        .replace("⚠", "!")     # ⚠️
        .replace("↳", "  ")    # ↳
        .replace("·", "-")     # ·
        .encode("latin-1", errors="replace").decode("latin-1")
    )


class PlanPDF(FPDF):

    def normalize_text(self, text: str) -> str:
        return super().normalize_text(_clean(text))

    def header(self):
        # Roter Balken oben
        self.set_fill_color(*C_ACCENT)
        self.rect(0, 0, 210, 8, "F")

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_MID_GREY)
        self.cell(0, 5, "Buddensiek Performance · Individueller Trainingsplan", align="C")

    def section_title(self, text: str):
        self.ln(4)
        self.set_fill_color(*C_ACCENT)
        self.set_text_color(*C_WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {text.upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def kv(self, label: str, value: str, bold_value: bool = False):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_DARK_GREY)
        self.cell(38, 5, label)
        self.set_font("Helvetica", "B" if bold_value else "", 8)
        self.set_text_color(*C_BLACK)
        self.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")


def build_pdf(plan_data: dict) -> FPDF:
    snap = plan_data["klient_snapshot"]
    vorname = plan_data.get("vorname", "Klient")

    pdf = PlanPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(14, 14, 14)
    pdf.set_auto_page_break(auto=True, margin=16)

    # ── Deckblatt ─────────────────────────────────────────────────────────────
    pdf.add_page()

    # Titel-Block
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(0, 10, "TRAININGSPLAN", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*C_MID_GREY)
    pdf.cell(0, 6, "Buddensiek Performance · Individuell · KI-gestützt", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Trennlinie
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(6)

    # Klienten-Info
    pdf.section_title("Klientenprofil")
    verletzungen = ", ".join(snap["verletzungen"]) if snap["verletzungen"] else "keine"
    session_dauer = snap.get("session_dauer_min", 60)
    tage = snap["tage_pro_woche"]
    wochenzeit = tage * session_dauer

    pdf.kv("Name:", vorname, bold_value=True)
    pdf.kv("Level:", f"Level {snap['level']}/4", bold_value=True)
    pdf.kv("Ziel:", snap["ziel"].replace("_", " ").title())
    pdf.kv("Equipment:", snap["equipment"].replace("_", " ").title())
    pdf.kv("Split:", snap["split_typ"])
    pdf.kv("Tage/Woche:", str(tage))
    pdf.kv("Session-Dauer:", f"{session_dauer} Min.")
    pdf.kv("Wochenzeit:", f"~{wochenzeit} Min. / Woche")
    pdf.kv("Verletzungen:", verletzungen)
    pdf.kv("Block:", f"Block {plan_data['block_nummer']}")
    pdf.kv("Erstellt:", plan_data["erstellt_am"][:10])
    pdf.ln(2)

    # Realism-/Kapazitäts-Warnung bewusst NICHT im Klienten-PDF (2026-06-17): „zu wenig Zeit fürs
    # Ziel gewählt" gehört ins Intake/Frontend (Fillout), nicht ins fertige Premium-PDF (s. BACKLOG).

    # Wochen-Übersicht
    pdf.section_title("4-Wochen-Übersicht")
    for woche in plan_data["wochen"]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_DARK_GREY)
        pdf.set_fill_color(*C_LIGHT_GREY)
        label = f"  Woche {woche['woche_nummer']} — {woche['block_typ'].upper()}  |  {woche['ziel_saetze']} Sätze × RIR {woche['ziel_rir']:g}"
        pdf.cell(0, 6, label, fill=True, new_x="LMARGIN", new_y="NEXT")
        for s in woche["sessions"]:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*C_DARK_GREY)
            cardio_str = f"  +{s['cardio']['typ'].upper()}" if s.get("cardio") else ""
            pst_str = "  [PST RE-TEST]" if s.get("pst_tests") else ""
            tag = s["tag"].capitalize()
            line = f"    {tag:<12}  {s['fokus']:<38} ~{s['dauer_min_geschaetzt']}min{cardio_str}{pst_str}"
            pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ── Wochenseiten ──────────────────────────────────────────────────────────
    for woche in plan_data["wochen"]:
        pdf.add_page()

        # Wochen-Header
        block_label = f"WOCHE {woche['woche_nummer']} — {woche['block_typ'].upper()}"
        vol_label   = f"{woche['ziel_saetze']} Sätze  ·  RIR {woche['ziel_rir']:g}  ·  {woche['volumen_stufe'].replace('_', ' ').title()}"

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*C_BLACK)
        pdf.cell(0, 8, block_label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_MID_GREY)
        pdf.cell(0, 5, vol_label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*C_LINE)
        pdf.set_line_width(0.3)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())
        pdf.ln(3)

        for s in woche["sessions"]:
            # Session-Header
            pdf.set_fill_color(*C_DARK_GREY)
            pdf.set_text_color(*C_WHITE)
            pdf.set_font("Helvetica", "B", 9)
            header = f"  {s['tag'].upper()}  —  {s['fokus'].upper()}  (~{s['dauer_min_geschaetzt']} min)"
            pdf.cell(0, 6, header, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

            # Format-Notiz (AMRAP / Zirkel / Intervalle)
            if s.get("format_notiz"):
                pdf.set_fill_color(30, 30, 30)
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.multi_cell(0, 5, f"  FORMAT: {s['format_notiz']}", fill=True)
                pdf.ln(2)

            # Warm-Up
            pdf.set_font("Helvetica", "BI", 7)
            pdf.set_text_color(*C_ACCENT)
            pdf.cell(0, 4, "  WARM-UP", new_x="LMARGIN", new_y="NEXT")
            wu_items = " · ".join(u["name"] for u in s["warm_up"]["uebungen"])
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*C_MID_GREY)
            pdf.multi_cell(0, 4, f"  {wu_items}")
            pdf.ln(1)

            # Hauptübungen
            pdf.set_font("Helvetica", "BI", 7)
            pdf.set_text_color(*C_ACCENT)
            pdf.cell(0, 4, "  HAUPTÜBUNGEN", new_x="LMARGIN", new_y="NEXT")

            is_metabolic_session = s.get("session_typ") in _CONDITIONING
            for u in s["haupt_uebungen"]:
                if is_metabolic_session:
                    # Metabolic: kein Tempo, Pause nur bei Intervallen
                    if u["saetze"] > 1:
                        vol_str = f"{u['saetze']}× {u['wdh']}"
                    else:
                        vol_str = u["wdh"]
                    spec_parts = []
                    if u.get("rir") is not None:
                        spec_parts.append(f"RIR {u['rir']:g}")
                    if u["pausenzeit_sek"] > 0:
                        spec_parts.append(f"Pause {u['pausenzeit_sek']}s")
                    spec_str = "  ·  ".join(spec_parts)
                else:
                    vol_str  = f"{u['saetze']}×{u['wdh']}"
                    # Conditioning/Athletik & Zeit-Holds tragen kein RIR — RIR-Teil nur wenn gesetzt
                    rir_part = f"RIR {u['rir']:g}  ·  " if u.get("rir") is not None else ""
                    spec_str = f"{rir_part}Tempo {u['tempo']}  ·  Pause {u['pausenzeit_sek']}s"

                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*C_BLACK)
                pdf.cell(6, 5, f"  {u['reihenfolge']}.")
                pdf.cell(78, 5, u["name"])
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*C_ACCENT)
                pdf.cell(22, 5, vol_str)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(*C_MID_GREY)
                pdf.cell(0, 5, spec_str, new_x="LMARGIN", new_y="NEXT")

                # Coaching Cues
                cues = "  ·  ".join(u["coaching_cues"])
                pdf.set_font("Helvetica", "I", 6.5)
                pdf.set_text_color(*C_MID_GREY)
                pdf.set_x(20)
                pdf.multi_cell(176, 3.5, f"↳ {cues}")

                # Notiz von Claude
                if u.get("notiz"):
                    pdf.set_font("Helvetica", "I", 7)
                    pdf.set_text_color(*C_DARK_GREY)
                    pdf.set_fill_color(255, 248, 230)
                    pdf.set_x(20)
                    pdf.multi_cell(176, 4, f"📝 {u['notiz']}", fill=True)
                pdf.ln(1)

            # MetconBlock (Recomp Finisher)
            if s.get("metcon_block"):
                mb = s["metcon_block"]
                pdf.ln(2)
                pdf.set_fill_color(40, 40, 80)
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.cell(0, 6, f"  CONDITIONING FINISHER — {mb['typ'].upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")
                pdf.set_fill_color(50, 50, 100)
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("Helvetica", "I", 7)
                pdf.multi_cell(0, 4.5, f"  {mb['format_notiz']}", fill=True)
                pdf.ln(1)
                for u in mb["uebungen"]:
                    if u["saetze"] > 1:
                        vol_str = f"{u['saetze']}× {u['wdh']}"
                    else:
                        vol_str = u["wdh"]
                    spec_parts = []
                    if u.get("rir") is not None:
                        spec_parts.append(f"RIR {u['rir']:g}")
                    if u["pausenzeit_sek"] > 0:
                        spec_parts.append(f"Pause {u['pausenzeit_sek']}s")
                    spec_str = "  ·  ".join(spec_parts)
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*C_BLACK)
                    pdf.cell(6, 5, f"  {u['reihenfolge']}.")
                    pdf.cell(78, 5, u["name"])
                    pdf.set_text_color(40, 40, 180)
                    pdf.cell(22, 5, vol_str)
                    pdf.set_font("Helvetica", "", 7)
                    pdf.set_text_color(*C_MID_GREY)
                    pdf.cell(0, 5, spec_str, new_x="LMARGIN", new_y="NEXT")
                    cues = "  ·  ".join(u["coaching_cues"])
                    pdf.set_font("Helvetica", "I", 6.5)
                    pdf.set_text_color(*C_MID_GREY)
                    pdf.set_x(20)
                    pdf.multi_cell(176, 3.5, f"-> {cues}")
                    pdf.ln(0.5)
                pdf.ln(1)

            # Conditioning-Block 2 (Naht 4d: zweites Format-Segment langer reiner C-Tage)
            if s.get("conditioning_block_2"):
                mb = s["conditioning_block_2"]
                pdf.ln(2)
                pdf.set_fill_color(40, 40, 80)
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.cell(0, 6, f"  CONDITIONING — FORMAT 2: {mb['typ'].upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")
                pdf.set_fill_color(50, 50, 100)
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("Helvetica", "I", 7)
                pdf.multi_cell(0, 4.5, f"  {mb['format_notiz']}", fill=True)
                pdf.ln(1)
                for u in mb["uebungen"]:
                    vol_str = f"{u['saetze']}× {u['wdh']}" if u["saetze"] > 1 else u["wdh"]
                    spec_str = f"Pause {u['pausenzeit_sek']}s" if u["pausenzeit_sek"] > 0 else ""
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*C_BLACK)
                    pdf.cell(6, 5, f"  {u['reihenfolge']}.")
                    pdf.cell(78, 5, u["name"])
                    pdf.set_text_color(40, 40, 180)
                    pdf.cell(22, 5, vol_str)
                    pdf.set_font("Helvetica", "", 7)
                    pdf.set_text_color(*C_MID_GREY)
                    pdf.cell(0, 5, spec_str, new_x="LMARGIN", new_y="NEXT")
                    cues = "  ·  ".join(u["coaching_cues"])
                    pdf.set_font("Helvetica", "I", 6.5)
                    pdf.set_text_color(*C_MID_GREY)
                    pdf.set_x(20)
                    pdf.multi_cell(176, 3.5, f"-> {cues}")
                    pdf.ln(0.5)
                pdf.ln(1)

            # Cardio
            if s.get("cardio"):
                c = s["cardio"]
                pdf.set_font("Helvetica", "BI", 7)
                pdf.set_text_color(*C_ACCENT)
                pdf.cell(0, 4, "  CARDIO", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*C_DARK_GREY)
                pdf.multi_cell(0, 4, f"  {c['typ'].upper()} · {c['dauer_min']} min  —  {c['beschreibung']}")
                pdf.ln(1)

            # Cool-Down
            pdf.set_font("Helvetica", "BI", 7)
            pdf.set_text_color(*C_ACCENT)
            pdf.cell(0, 4, "  COOL-DOWN", new_x="LMARGIN", new_y="NEXT")
            cd_items = " · ".join(
                f"{u['name']} ({u.get('dauer_sek', '')}s)" for u in s["cool_down"]["uebungen"]
            )
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*C_MID_GREY)
            pdf.multi_cell(0, 4, f"  {cd_items}")

            # PST Re-Test
            if s.get("pst_tests"):
                pdf.ln(1)
                pdf.set_font("Helvetica", "BI", 7)
                pdf.set_text_color(*C_ACCENT)
                pdf.cell(0, 4, "  PST RE-TEST", new_x="LMARGIN", new_y="NEXT")
                tests = " · ".join(t["test"].upper() for t in s["pst_tests"])
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*C_DARK_GREY)
                pdf.cell(0, 4, f"  {tests}", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(4)

    return pdf


def main(plan_path: str):
    plan_data = json.loads(pathlib.Path(plan_path).read_text())

    # Vorname aus client_id nicht verfügbar — aus Snapshot ableiten
    snap = plan_data["klient_snapshot"]
    name_slug = f"Block{plan_data['block_nummer']}"

    pdf = build_pdf(plan_data)

    out_dir = pathlib.Path(plan_path).parent
    out_path = out_dir / f"plan_{plan_data['client_id'][:8]}_{name_slug}.pdf"
    pdf.output(str(out_path))
    print(f"✅ PDF gespeichert: {out_path}")
    return out_path


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "output/plan_38ea3675.json"
    main(path)
