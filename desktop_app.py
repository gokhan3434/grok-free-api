import json
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import Tk, StringVar, Text, END, messagebox
from tkinter import ttk

import requests
from fpdf import FPDF


@dataclass
class ParcelQuery:
    district: str
    neighborhood: str
    block: str  # ada
    parcel: str


class CbsClient:
    """Simple CBS API client.

    Notes:
    - Endpoint/template and token are configurable from UI settings.
    - If endpoint fails, returns a structured placeholder so UI remains usable.
    """

    def __init__(self, endpoint_template: str, auth_token: str | None = None):
        self.endpoint_template = endpoint_template.strip()
        self.auth_token = (auth_token or "").strip()

    def fetch_parcel(self, query: ParcelQuery) -> dict:
        if not self.endpoint_template:
            raise ValueError("CBS endpoint template boş olamaz")

        url = self.endpoint_template.format(
            district=query.district,
            neighborhood=query.neighborhood,
            block=query.block,
            parcel=query.parcel,
        )
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["X-Auth-Token"] = self.auth_token

        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()


class ZoningAnalyzer:
    @staticmethod
    def parse_and_compute(raw: dict) -> dict:
        # Flexible extraction with safe defaults
        area = float(raw.get("netArea", raw.get("area", 0)) or 0)
        emsal = float(raw.get("kaks", raw.get("emsal", 0.20)) or 0.20)
        taks = float(raw.get("taks", 0.15) or 0.15)
        yencok = raw.get("yencok", raw.get("katSiniri", "2"))
        function = raw.get("function", raw.get("fonksiyon", "Konut Alanı"))

        base_area = area * taks
        total_construction = area * emsal

        return {
            "net_area": area,
            "function": function,
            "emsal": emsal,
            "taks": taks,
            "yencok": yencok,
            "base_area": round(base_area, 2),
            "total_construction": round(total_construction, 2),
            "risks": [
                "Veriler bilgilendirme amaçlıdır, resmi belge yerine geçmez.",
                "18. madde / DOP kesintisi ihtimalini belediye onayı ile doğrulayın.",
                "Jeolojik-jeoteknik etüt onayı olmadan uygulamaya geçmeyin.",
            ],
        }


class ReportBuilder:
    @staticmethod
    def save_pdf(query: ParcelQuery, analysis: dict, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"imar_raporu_{query.neighborhood}_{query.block}_{query.parcel}.pdf".replace(" ", "_")
        out = output_dir / filename

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Gayrimenkul Ekspertiz Notu", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.cell(0, 8, f"Bolge: {query.district} / {query.neighborhood}", ln=True)
        pdf.cell(0, 8, f"Ada/Parsel: {query.block} / {query.parcel}", ln=True)
        pdf.ln(3)

        lines = [
            f"Net Alan: {analysis['net_area']} m2",
            f"Fonksiyon: {analysis['function']}",
            f"Emsal (KAKS): {analysis['emsal']}",
            f"TAKS: {analysis['taks']}",
            f"Yencok: {analysis['yencok']}",
            f"Maks. taban oturumu: {analysis['base_area']} m2",
            f"Toplam insaat alani: {analysis['total_construction']} m2",
            "",
            "Kirmizi Bayraklar:",
        ] + [f"- {r}" for r in analysis["risks"]]

        for line in lines:
            pdf.multi_cell(0, 7, line)

        pdf.output(str(out))
        return out


class DesktopApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Beykoz CBS Masaustu Analiz")
        self.root.geometry("960x700")

        self.endpoint_var = StringVar(value="https://cbs.beykoz.bel.tr/GiSoftGis/rest/entity/report/parcel/2/{parcel}")
        self.token_var = StringVar(value="")
        self.district_var = StringVar(value="Beykoz")
        self.neighborhood_var = StringVar(value="Pasamandira")
        self.block_var = StringVar(value="133")
        self.parcel_var = StringVar(value="319")

        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="CBS Endpoint Template").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.endpoint_var, width=95).grid(row=0, column=1, columnspan=5, sticky="ew", pady=2)

        ttk.Label(frm, text="X-Auth-Token").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.token_var, width=95).grid(row=1, column=1, columnspan=5, sticky="ew", pady=2)

        labels = ["Ilce", "Mahalle", "Ada", "Parsel"]
        vars_ = [self.district_var, self.neighborhood_var, self.block_var, self.parcel_var]
        for i, (label, var) in enumerate(zip(labels, vars_)):
            ttk.Label(frm, text=label).grid(row=2, column=i, sticky="w")
            ttk.Entry(frm, textvariable=var, width=20).grid(row=3, column=i, sticky="ew", padx=3)

        ttk.Button(frm, text="Sorgula + Analiz", command=self.run_query).grid(row=3, column=4, padx=8)
        ttk.Button(frm, text="PDF Olustur", command=self.export_pdf).grid(row=3, column=5, padx=8)

        self.status = StringVar(value="Hazir")
        ttk.Label(frm, textvariable=self.status).grid(row=4, column=0, columnspan=6, sticky="w", pady=6)

        self.output = Text(frm, wrap="word", height=30)
        self.output.grid(row=5, column=0, columnspan=6, sticky="nsew")

        for c in range(6):
            frm.columnconfigure(c, weight=1)
        frm.rowconfigure(5, weight=1)

        self.last_query = None
        self.last_analysis = None

    def run_query(self):
        self.status.set("Sorgu calisiyor...")
        self.output.delete("1.0", END)

        def _task():
            try:
                query = ParcelQuery(
                    district=self.district_var.get().strip(),
                    neighborhood=self.neighborhood_var.get().strip(),
                    block=self.block_var.get().strip(),
                    parcel=self.parcel_var.get().strip(),
                )
                client = CbsClient(self.endpoint_var.get(), self.token_var.get())
                raw = client.fetch_parcel(query)
                analysis = ZoningAnalyzer.parse_and_compute(raw)

                result = {
                    "query": query.__dict__,
                    "analysis": analysis,
                    "raw_preview": raw,
                }
                self.last_query = query
                self.last_analysis = analysis
                self.root.after(0, lambda: self._show_result(result))
            except Exception as exc:
                self.root.after(0, lambda: self._show_error(str(exc)))

        threading.Thread(target=_task, daemon=True).start()

    def _show_result(self, data: dict):
        self.output.insert(END, json.dumps(data, ensure_ascii=False, indent=2))
        self.status.set("Tamamlandi")

    def _show_error(self, message: str):
        self.status.set("Hata")
        messagebox.showerror("Sorgu hatasi", message)

    def export_pdf(self):
        if not self.last_query or not self.last_analysis:
            messagebox.showwarning("Uyari", "Once sorgu calistirin.")
            return
        out = ReportBuilder.save_pdf(self.last_query, self.last_analysis, Path("reports"))
        messagebox.showinfo("PDF hazir", f"Kaydedildi: {out}")


def main():
    root = Tk()
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
