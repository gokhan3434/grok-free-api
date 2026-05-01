import json
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import END, Tk, StringVar, Text, messagebox
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fpdf import FPDF

BEYKOZ_NEIGHBORHOODS = [
    "Acarlar", "Akbaba", "Alibahadır", "Anadolufeneri", "Anadoluhisarı", "Baklacı", "Bozhane",
    "Cumhuriyet", "Çamlıbahçe", "Çavuşbaşı", "Çengeldere", "Çiftlik", "Dereseki", "Elmalı",
    "Fatih", "Göksu", "Görele", "Göllü", "Gümüşsuyu", "İncirköy", "Kanlıca", "Kavacık",
    "Kaynarca", "Mahmutşevketpaşa", "Merkez", "Murat Reis", "Ortaçeşme", "Örnekköy", "Öğümce",
    "Paşabahçe", "Paşamandıra", "Polonezköy", "Poyrazköy", "Riva", "Rüzgarlıbahçe", "Soğuksu",
    "Tokatköy", "Yalıköy", "Yavuz Selim", "Yeni Mahalle", "Zerzavatçı"
]

@dataclass
class ParcelQuery:
    district: str
    neighborhood: str
    block: str
    parcel: str


class TokenProvider:
    """Token acquisition helper.

    Strategy:
    1) If token endpoint provided, call it and parse token_json_path.
    2) Else run optional shell command to produce token (advanced use).
    3) Fallback to manual token input.
    """

    def __init__(self, token_endpoint: str, token_json_path: str, token_cmd: str):
        self.token_endpoint = token_endpoint.strip()
        self.token_json_path = token_json_path.strip() or "token"
        self.token_cmd = token_cmd.strip()

    def get_token(self, manual_token: str) -> str:
        if manual_token.strip():
            return manual_token.strip()
        if self.token_endpoint:
            req = Request(self.token_endpoint, headers={"Accept": "application/json"})
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return self._extract_by_path(data, self.token_json_path)
        if self.token_cmd:
            out = subprocess.check_output(self.token_cmd, shell=True, text=True, timeout=20)
            return out.strip()
        return ""

    @staticmethod
    def _extract_by_path(data: dict, path: str) -> str:
        node = data
        for part in path.split('.'):
            node = node[part]
        return str(node)


class CbsClient:
    def __init__(self, endpoint_template: str, auth_token: str):
        self.endpoint_template = endpoint_template.strip()
        self.auth_token = auth_token.strip()

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
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            raise RuntimeError(f"CBS HTTP hatası: {e.code}") from e
        except URLError as e:
            raise RuntimeError(f"CBS bağlantı hatası: {e.reason}") from e


class ZoningAnalyzer:
    @staticmethod
    def parse_and_compute(raw: dict) -> dict:
        area = float(raw.get("netArea", raw.get("area", 0)) or 0)
        emsal = float(raw.get("kaks", raw.get("emsal", 0.20)) or 0.20)
        taks = float(raw.get("taks", 0.15) or 0.15)
        yencok = raw.get("yencok", raw.get("katSiniri", "2"))
        function = raw.get("function", raw.get("fonksiyon", "Konut Alanı"))
        min_ifraz = float(raw.get("minIfraz", 500) or 500)

        return {
            "net_area": area,
            "function": function,
            "emsal": emsal,
            "taks": taks,
            "yencok": yencok,
            "base_area": round(area * taks, 2),
            "total_construction": round(area * emsal, 2),
            "ifraz_possible": area >= (2 * min_ifraz),
            "risks": [
                "18. madde / DOP kesintisi belediye plan uygulamasına göre değişebilir.",
                "DSİ / kurum görüşü gereken alanlarda resmi görüş zorunludur.",
                "Onaylı jeolojik-jeoteknik etüt olmadan ruhsat süreci ilerletilmemelidir.",
                "Veriler bilgilendirme amaçlıdır, resmi belge yerine geçmez.",
            ],
        }


class ReportBuilder:
    @staticmethod
    def save_pdf(query: ParcelQuery, analysis: dict, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / f"imar_raporu_{query.neighborhood}_{query.block}_{query.parcel}.pdf".replace(" ", "_")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Beykoz Parsel Analiz Raporu", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, json.dumps({"query": query.__dict__, "analysis": analysis}, ensure_ascii=False, indent=2))
        pdf.output(str(out))
        return out


class DesktopApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Beykoz CBS Tam Otomatik Masaüstü")
        self.root.geometry("1100x760")

        self.endpoint_var = StringVar(value="https://cbs.beykoz.bel.tr/GiSoftGis/rest/entity/report/parcel/2/{parcel}")
        self.token_var = StringVar(value="")
        self.token_endpoint_var = StringVar(value="")
        self.token_path_var = StringVar(value="token")
        self.token_cmd_var = StringVar(value="")
        self.district_var = StringVar(value="Beykoz")
        self.neighborhood_var = StringVar(value=BEYKOZ_NEIGHBORHOODS[0])
        self.block_var = StringVar(value="133")
        self.parcel_var = StringVar(value="319")

        self.last_query = None
        self.last_analysis = None
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="CBS Endpoint Template").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.endpoint_var, width=100).grid(row=0, column=1, columnspan=5, sticky="ew")
        ttk.Label(frm, text="Manual X-Auth-Token").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.token_var, width=100).grid(row=1, column=1, columnspan=5, sticky="ew")

        ttk.Label(frm, text="Token Endpoint (opsiyonel)").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.token_endpoint_var).grid(row=2, column=1, columnspan=2, sticky="ew")
        ttk.Label(frm, text="JSON Path").grid(row=2, column=3, sticky="w")
        ttk.Entry(frm, textvariable=self.token_path_var).grid(row=2, column=4, sticky="ew")
        ttk.Entry(frm, textvariable=self.token_cmd_var).grid(row=2, column=5, sticky="ew")

        ttk.Label(frm, text="İlçe").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.district_var).grid(row=3, column=1, sticky="ew")
        ttk.Label(frm, text="Mahalle").grid(row=3, column=2, sticky="w")
        ttk.Combobox(frm, textvariable=self.neighborhood_var, values=BEYKOZ_NEIGHBORHOODS, state="readonly").grid(row=3, column=3, sticky="ew")
        ttk.Label(frm, text="Ada").grid(row=3, column=4, sticky="w")
        ttk.Entry(frm, textvariable=self.block_var, width=10).grid(row=3, column=5, sticky="ew")
        ttk.Label(frm, text="Parsel").grid(row=4, column=4, sticky="w")
        ttk.Entry(frm, textvariable=self.parcel_var, width=10).grid(row=4, column=5, sticky="ew")

        ttk.Button(frm, text="Sorgula + Analiz", command=self.run_query).grid(row=4, column=1, sticky="ew")
        ttk.Button(frm, text="PDF Oluştur", command=self.export_pdf).grid(row=4, column=2, sticky="ew")

        self.status = StringVar(value="Hazır")
        ttk.Label(frm, textvariable=self.status).grid(row=5, column=0, columnspan=6, sticky="w")
        self.output = Text(frm, wrap="word", height=32)
        self.output.grid(row=6, column=0, columnspan=6, sticky="nsew")

        for c in range(6):
            frm.columnconfigure(c, weight=1)
        frm.rowconfigure(6, weight=1)

    def run_query(self):
        self.status.set("Çalışıyor...")
        self.output.delete("1.0", END)

        def worker():
            try:
                query = ParcelQuery(self.district_var.get(), self.neighborhood_var.get(), self.block_var.get(), self.parcel_var.get())
                token = TokenProvider(self.token_endpoint_var.get(), self.token_path_var.get(), self.token_cmd_var.get()).get_token(self.token_var.get())
                raw = CbsClient(self.endpoint_var.get(), token).fetch_parcel(query)
                analysis = ZoningAnalyzer.parse_and_compute(raw)
                self.last_query, self.last_analysis = query, analysis
                payload = {"query": query.__dict__, "token_source": "auto" if token else "manual/none", "analysis": analysis, "raw": raw}
                self.root.after(0, lambda: self._show(payload))
            except Exception as e:
                self.root.after(0, lambda: self._err(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _show(self, payload: dict):
        self.output.insert(END, json.dumps(payload, ensure_ascii=False, indent=2))
        self.status.set("Tamamlandı")

    def _err(self, msg: str):
        self.status.set("Hata")
        messagebox.showerror("Hata", msg)

    def export_pdf(self):
        if not self.last_query or not self.last_analysis:
            messagebox.showwarning("Uyarı", "Önce sorgu çalıştırın")
            return
        path = ReportBuilder.save_pdf(self.last_query, self.last_analysis, Path("reports"))
        messagebox.showinfo("Tamam", f"Rapor: {path}")


if __name__ == "__main__":
    root = Tk()
    DesktopApp(root)
    root.mainloop()
