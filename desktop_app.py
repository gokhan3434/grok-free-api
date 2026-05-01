import json
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import END, Tk, StringVar, Text, messagebox
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from fpdf import FPDF

BEYKOZ_NEIGHBORHOODS = ["Acarlar", "Akbaba", "Alibahadır", "Anadolufeneri", "Anadoluhisarı", "Baklacı", "Bozhane", "Cumhuriyet", "Çamlıbahçe", "Çavuşbaşı", "Çengeldere", "Çiftlik", "Dereseki", "Elmalı", "Fatih", "Göksu", "Görele", "Göllü", "Gümüşsuyu", "İncirköy", "Kanlıca", "Kavacık", "Kaynarca", "Mahmutşevketpaşa", "Merkez", "Murat Reis", "Ortaçeşme", "Örnekköy", "Öğümce", "Paşabahçe", "Paşamandıra", "Polonezköy", "Poyrazköy", "Riva", "Rüzgarlıbahçe", "Soğuksu", "Tokatköy", "Yalıköy", "Yavuz Selim", "Yeni Mahalle", "Zerzavatçı"]


@dataclass
class ParcelQuery:
    district: str
    neighborhood: str
    block: str
    parcel: str


class TokenProvider:
    """Automatic token discovery + fallback methods."""

    def __init__(self, base_url: str, token_endpoint: str, token_json_path: str, token_cmd: str):
        self.base_url = base_url.strip()
        self.token_endpoint = token_endpoint.strip()
        self.token_json_path = token_json_path.strip() or "token"
        self.token_cmd = token_cmd.strip()

    def get_token(self, manual_token: str) -> tuple[str, str]:
        if manual_token.strip():
            return manual_token.strip(), "manual"

        auto = self.auto_discover_from_site()
        if auto:
            return auto, "auto-site-discovery"

        if self.token_endpoint:
            req = Request(self.token_endpoint, headers={"Accept": "application/json"})
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return self._extract_by_path(data, self.token_json_path), "token-endpoint"

        if self.token_cmd:
            out = subprocess.check_output(self.token_cmd, shell=True, text=True, timeout=30)
            return out.strip(), "token-command"

        return "", "none"

    def auto_discover_from_site(self) -> str:
        if not self.base_url:
            return ""

        candidates = [
            self.base_url,
            urljoin(self.base_url, "./"),
            urljoin(self.base_url, "./index.html"),
            urljoin(self.base_url, "GiSoftGis/"),
            urljoin(self.base_url, "GiSoftGis/index.html"),
            urljoin(self.base_url, "GiSoftGis/rest/auth/token"),
            urljoin(self.base_url, "GiSoftGis/rest/token"),
            urljoin(self.base_url, "GiSoftGis/api/token"),
            urljoin(self.base_url, "rest/auth/token"),
            urljoin(self.base_url, "rest/token"),
            urljoin(self.base_url, "api/token"),
        ]

        for url in candidates:
            try:
                text = self._fetch_text(url)
                token = self._extract_token_from_text(text)
                if token:
                    return token
                # discover JS bundles and scan them
                for js in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', text):
                    js_url = urljoin(url, js)
                    js_text = self._fetch_text(js_url)
                    token = self._extract_token_from_text(js_text)
                    if token:
                        return token
            except Exception:
                continue
        return ""

    @staticmethod
    def _fetch_text(url: str) -> str:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    @staticmethod
    def _extract_token_from_text(text: str) -> str:
        patterns = [
            r'X-Auth-Token["\']?\s*[:=]\s*["\']([^"\']{12,})',
            r'authToken["\']?\s*[:=]\s*["\']([^"\']{12,})',
            r'token["\']?\s*[:=]\s*["\']([A-Za-z0-9._\-]{16,})',
        ]
        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                return m.group(1)
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
        url = self.endpoint_template.format(district=query.district, neighborhood=query.neighborhood, block=query.block, parcel=query.parcel)
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["X-Auth-Token"] = self.auth_token
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            raise RuntimeError(f"CBS HTTP hatası: {e.code}. Token geçersiz olabilir.") from e
        except URLError as e:
            raise RuntimeError(f"CBS bağlantı hatası: {e.reason}") from e


class ZoningAnalyzer:
    @staticmethod
    def parse_and_compute(raw: dict) -> dict:
        area = float(raw.get("netArea", raw.get("area", 0)) or 0)
        emsal = float(raw.get("kaks", raw.get("emsal", 0.20)) or 0.20)
        taks = float(raw.get("taks", 0.15) or 0.15)
        return {"net_area": area, "emsal": emsal, "taks": taks, "taban_alan": round(area*taks,2), "toplam_insaat": round(area*emsal,2)}


class ReportBuilder:
    @staticmethod
    def save_pdf(query: ParcelQuery, analysis: dict, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"imar_raporu_{query.neighborhood}_{query.block}_{query.parcel}.pdf".replace(" ", "_")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, json.dumps({"query": query.__dict__, "analysis": analysis}, ensure_ascii=False, indent=2))
        pdf.output(str(out))
        return out


class DesktopApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Beykoz CBS Otomatik")
        self.root.geometry("1100x760")
        self.base_url_var = StringVar(value="https://cbs.beykoz.bel.tr/")
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
        f = ttk.Frame(self.root, padding=10); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Base URL").grid(row=0, column=0, sticky="w"); ttk.Entry(f, textvariable=self.base_url_var).grid(row=0, column=1, columnspan=5, sticky="ew")
        ttk.Label(f, text="CBS Endpoint").grid(row=1, column=0, sticky="w"); ttk.Entry(f, textvariable=self.endpoint_var).grid(row=1, column=1, columnspan=5, sticky="ew")
        ttk.Label(f, text="Manual Token").grid(row=2, column=0, sticky="w"); ttk.Entry(f, textvariable=self.token_var).grid(row=2, column=1, columnspan=5, sticky="ew")
        ttk.Label(f, text="Token Endpoint").grid(row=3, column=0, sticky="w"); ttk.Entry(f, textvariable=self.token_endpoint_var).grid(row=3, column=1, sticky="ew")
        ttk.Label(f, text="JSON Path").grid(row=3, column=2); ttk.Entry(f, textvariable=self.token_path_var).grid(row=3, column=3, sticky="ew")
        ttk.Label(f, text="Token Cmd").grid(row=3, column=4); ttk.Entry(f, textvariable=self.token_cmd_var).grid(row=3, column=5, sticky="ew")

        ttk.Label(f, text="Mahalle").grid(row=4, column=0); ttk.Combobox(f, textvariable=self.neighborhood_var, values=BEYKOZ_NEIGHBORHOODS, state="readonly").grid(row=4, column=1, sticky="ew")
        ttk.Label(f, text="Ada").grid(row=4, column=2); ttk.Entry(f, textvariable=self.block_var).grid(row=4, column=3, sticky="ew")
        ttk.Label(f, text="Parsel").grid(row=4, column=4); ttk.Entry(f, textvariable=self.parcel_var).grid(row=4, column=5, sticky="ew")

        ttk.Button(f, text="Sorgula", command=self.run_query).grid(row=5, column=1, sticky="ew")
        ttk.Button(f, text="PDF", command=self.export_pdf).grid(row=5, column=2, sticky="ew")
        self.status = StringVar(value="Hazır"); ttk.Label(f, textvariable=self.status).grid(row=6, column=0, columnspan=6, sticky="w")
        self.output = Text(f, height=30); self.output.grid(row=7, column=0, columnspan=6, sticky="nsew")
        for c in range(6): f.columnconfigure(c, weight=1)
        f.rowconfigure(7, weight=1)

    def run_query(self):
        self.output.delete("1.0", END); self.status.set("Çalışıyor...")
        def worker():
            try:
                q = ParcelQuery(self.district_var.get(), self.neighborhood_var.get(), self.block_var.get(), self.parcel_var.get())
                token, source = TokenProvider(self.base_url_var.get(), self.token_endpoint_var.get(), self.token_path_var.get(), self.token_cmd_var.get()).get_token(self.token_var.get())
                raw = CbsClient(self.endpoint_var.get(), token).fetch_parcel(q)
                analysis = ZoningAnalyzer.parse_and_compute(raw)
                self.last_query, self.last_analysis = q, analysis
                self.root.after(0, lambda: self._show({"token_source": source, "token_found": bool(token), "query": q.__dict__, "analysis": analysis, "raw": raw}))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: self._err(msg))
        threading.Thread(target=worker, daemon=True).start()

    def _show(self, payload):
        self.output.insert(END, json.dumps(payload, ensure_ascii=False, indent=2)); self.status.set("Tamamlandı")

    def _err(self, msg):
        self.status.set("Hata"); messagebox.showerror("Hata", msg)

    def export_pdf(self):
        if not self.last_query or not self.last_analysis:
            return messagebox.showwarning("Uyarı", "Önce sorgu çalıştırın")
        path = ReportBuilder.save_pdf(self.last_query, self.last_analysis, Path("reports"))
        messagebox.showinfo("PDF", f"Kaydedildi: {path}")


if __name__ == "__main__":
    root = Tk(); DesktopApp(root); root.mainloop()
