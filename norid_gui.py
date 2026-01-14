#!/usr/bin/env python3
"""
Norid GUI - Grafisk grensesnitt for Norid sine offentlige tjenester

Tjenester:
  - RDAP: REST API for domenedata (rdap.norid.no)
  - DAS: Domain Availability Service (finger.norid.no:79)
  - Whois: Tradisjonelt domeneoppslag (whois.norid.no:43)

Ingen autentisering kreves.
"""

import json
import socket
import threading
from typing import Any, Dict, Optional

import customtkinter as ctk
import requests

# Tema og utseende
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# API-konfigurasjon
RDAP_BASE_URL = "https://rdap.norid.no"
RDAP_TEST_URL = "https://rdap.test.norid.no"
WHOIS_HOST = "whois.norid.no"
WHOIS_TEST_HOST = "whois.test.norid.no"
WHOIS_PORT = 43
DAS_HOST = "finger.norid.no"
DAS_TEST_HOST = "finger.test.norid.no"
DAS_PORT = 79


class NoridClient:
    """Klient for Norid sine offentlige tjenester"""

    def __init__(self, use_test: bool = False):
        self.use_test = use_test
        self.rdap_url = RDAP_TEST_URL if use_test else RDAP_BASE_URL
        self.whois_host = WHOIS_TEST_HOST if use_test else WHOIS_HOST
        self.das_host = DAS_TEST_HOST if use_test else DAS_HOST
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/rdap+json, application/json",
            "User-Agent": "Norid-GUI/1.0.0"
        })

    def _rdap_request(self, endpoint: str) -> tuple[bool, Any]:
        """Utfør HTTP-forespørsel mot RDAP API"""
        url = f"{self.rdap_url}/{endpoint}"
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 404:
                return False, "Ikke funnet"
            elif response.status_code == 429:
                return False, "Rate-limit overskredet. Vent litt før du prøver igjen."
            else:
                return False, f"Feil ({response.status_code}): {response.text}"
        except requests.exceptions.ConnectionError:
            return False, f"Kunne ikke koble til {self.rdap_url}"
        except requests.exceptions.Timeout:
            return False, "Forespørselen tok for lang tid (timeout)"
        except Exception as e:
            return False, f"Uventet feil: {str(e)}"

    def _socket_request(self, host: str, port: int, query: str) -> tuple[bool, str]:
        """Utfør socket-forespørsel (for whois og DAS)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)
                sock.connect((host, port))
                sock.sendall(f"{query}\r\n".encode("utf-8"))
                
                response = b""
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
                
                return True, response.decode("utf-8", errors="replace")
        except socket.timeout:
            return False, "Forespørselen tok for lang tid (timeout)"
        except socket.error as e:
            return False, f"Nettverksfeil: {e}"

    def rdap_domain(self, domain: str) -> tuple[bool, Any]:
        return self._rdap_request(f"domain/{domain}")

    def rdap_entity(self, handle: str) -> tuple[bool, Any]:
        return self._rdap_request(f"entity/{handle}")

    def rdap_nameserver(self, handle: str) -> tuple[bool, Any]:
        return self._rdap_request(f"nameserver_handle/{handle}")

    def rdap_nameserver_search(self, pattern: str) -> tuple[bool, Any]:
        return self._rdap_request(f"nameservers?name={pattern}")

    def whois(self, domain: str) -> tuple[bool, str]:
        return self._socket_request(self.whois_host, WHOIS_PORT, domain)

    def das(self, domain: str) -> tuple[bool, str]:
        return self._socket_request(self.das_host, DAS_PORT, domain)


class NoridGUI(ctk.CTk):
    """Hovedvindu for Norid GUI"""

    def __init__(self):
        super().__init__()

        self.title("Norid CLI - Domeneoppslag for .no")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Klient
        self.client = NoridClient(use_test=False)

        # Konfigurer grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self._create_header()

        # Tabs
        self._create_tabs()

        # Statuslinje
        self._create_statusbar()

    def _create_header(self):
        """Opprett header med logo og innstillinger"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Logo/tittel
        title_label = ctk.CTkLabel(
            header_frame,
            text="Norid CLI",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Slå opp .no-domener uten autentisering",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.grid(row=1, column=0, sticky="w")

        # Miljøvalg
        env_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        env_frame.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)

        env_label = ctk.CTkLabel(env_frame, text="Miljø:", font=ctk.CTkFont(size=12))
        env_label.pack(side="left", padx=(0, 10))

        self.env_var = ctk.StringVar(value="Produksjon")
        self.env_menu = ctk.CTkOptionMenu(
            env_frame,
            values=["Produksjon", "Test"],
            variable=self.env_var,
            command=self._on_env_change,
            width=120
        )
        self.env_menu.pack(side="left")

    def _create_tabs(self):
        """Opprett faner for ulike funksjoner"""
        self.tabview = ctk.CTkTabview(self, width=860, height=500)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Legg til faner
        self.tabview.add("🔍 DAS - Ledig domene")
        self.tabview.add("📋 Domeneoppslag")
        self.tabview.add("👤 Entitetsoppslag")
        self.tabview.add("🖥️ Navneserver")
        self.tabview.add("📄 Whois")

        # Konfigurer hver fane
        self._setup_das_tab()
        self._setup_domain_tab()
        self._setup_entity_tab()
        self._setup_nameserver_tab()
        self._setup_whois_tab()

    def _setup_das_tab(self):
        """Sett opp DAS-fanen"""
        tab = self.tabview.tab("🔍 DAS - Ledig domene")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Beskrivelse
        desc = ctk.CTkLabel(
            tab,
            text="Sjekk om et .no-domene er ledig for registrering",
            font=ctk.CTkFont(size=14)
        )
        desc.grid(row=0, column=0, pady=(20, 10))

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, pady=10)

        self.das_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Skriv inn domenenavn (f.eks. example.no)",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.das_entry.pack(side="left", padx=(0, 10))
        self.das_entry.bind("<Return>", lambda e: self._run_das())

        self.das_button = ctk.CTkButton(
            input_frame,
            text="Sjekk",
            command=self._run_das,
            width=100,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.das_button.pack(side="left")

        # Resultat
        self.das_result_frame = ctk.CTkFrame(tab)
        self.das_result_frame.grid(row=2, column=0, sticky="nsew", pady=20, padx=20)
        self.das_result_frame.grid_columnconfigure(0, weight=1)
        self.das_result_frame.grid_rowconfigure(0, weight=1)

        self.das_result = ctk.CTkLabel(
            self.das_result_frame,
            text="Skriv inn et domenenavn og klikk 'Sjekk'",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        self.das_result.grid(row=0, column=0, pady=50)

    def _setup_domain_tab(self):
        """Sett opp domeneoppslag-fanen"""
        tab = self.tabview.tab("📋 Domeneoppslag")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=20)

        self.domain_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Domenenavn (f.eks. norid.no)",
            width=400,
            height=40
        )
        self.domain_entry.pack(side="left", padx=(0, 10))
        self.domain_entry.bind("<Return>", lambda e: self._run_domain())

        self.domain_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_domain,
            width=100,
            height=40
        )
        self.domain_button.pack(side="left", padx=(0, 10))

        self.domain_json_var = ctk.BooleanVar(value=False)
        self.domain_json_check = ctk.CTkCheckBox(
            input_frame,
            text="JSON",
            variable=self.domain_json_var
        )
        self.domain_json_check.pack(side="left")

        # Resultat
        self.domain_result = ctk.CTkTextbox(tab, width=800, height=350)
        self.domain_result.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_entity_tab(self):
        """Sett opp entitetsoppslag-fanen"""
        tab = self.tabview.tab("👤 Entitetsoppslag")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=20)

        ctk.CTkLabel(input_frame, text="Handle:").pack(side="left", padx=(0, 10))

        self.entity_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="f.eks. reg1-NORID eller NH55R-NORID",
            width=350,
            height=40
        )
        self.entity_entry.pack(side="left", padx=(0, 10))
        self.entity_entry.bind("<Return>", lambda e: self._run_entity())

        self.entity_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_entity,
            width=100,
            height=40
        )
        self.entity_button.pack(side="left", padx=(0, 10))

        self.entity_json_var = ctk.BooleanVar(value=False)
        self.entity_json_check = ctk.CTkCheckBox(
            input_frame,
            text="JSON",
            variable=self.entity_json_var
        )
        self.entity_json_check.pack(side="left")

        # Resultat
        self.entity_result = ctk.CTkTextbox(tab, width=800, height=350)
        self.entity_result.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_nameserver_tab(self):
        """Sett opp navneserver-fanen"""
        tab = self.tabview.tab("🖥️ Navneserver")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Valg mellom oppslag og søk
        mode_frame = ctk.CTkFrame(tab, fg_color="transparent")
        mode_frame.grid(row=0, column=0, pady=(20, 10))

        self.ns_mode = ctk.StringVar(value="handle")
        ctk.CTkRadioButton(
            mode_frame,
            text="Oppslag via handle",
            variable=self.ns_mode,
            value="handle"
        ).pack(side="left", padx=20)
        ctk.CTkRadioButton(
            mode_frame,
            text="Søk via hostname",
            variable=self.ns_mode,
            value="search"
        ).pack(side="left", padx=20)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, pady=10)

        self.ns_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Handle (X11H-NORID) eller hostname (*.nic.no)",
            width=400,
            height=40
        )
        self.ns_entry.pack(side="left", padx=(0, 10))
        self.ns_entry.bind("<Return>", lambda e: self._run_nameserver())

        self.ns_button = ctk.CTkButton(
            input_frame,
            text="Søk",
            command=self._run_nameserver,
            width=100,
            height=40
        )
        self.ns_button.pack(side="left", padx=(0, 10))

        self.ns_json_var = ctk.BooleanVar(value=False)
        self.ns_json_check = ctk.CTkCheckBox(
            input_frame,
            text="JSON",
            variable=self.ns_json_var
        )
        self.ns_json_check.pack(side="left")

        # Resultat
        self.ns_result = ctk.CTkTextbox(tab, width=800, height=300)
        self.ns_result.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_whois_tab(self):
        """Sett opp whois-fanen"""
        tab = self.tabview.tab("📄 Whois")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=20)

        self.whois_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Domenenavn (f.eks. norid.no)",
            width=400,
            height=40
        )
        self.whois_entry.pack(side="left", padx=(0, 10))
        self.whois_entry.bind("<Return>", lambda e: self._run_whois())

        self.whois_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_whois,
            width=100,
            height=40
        )
        self.whois_button.pack(side="left")

        # Resultat
        self.whois_result = ctk.CTkTextbox(tab, width=800, height=350, font=ctk.CTkFont(family="Courier"))
        self.whois_result.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _create_statusbar(self):
        """Opprett statuslinje"""
        self.statusbar = ctk.CTkLabel(
            self,
            text="Klar",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.statusbar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

    def _on_env_change(self, value: str):
        """Håndter miljøbytte"""
        use_test = value == "Test"
        self.client = NoridClient(use_test=use_test)
        env_text = "testmiljø" if use_test else "produksjonsmiljø"
        self._set_status(f"Byttet til {env_text}")

    def _set_status(self, text: str):
        """Oppdater statuslinjen"""
        self.statusbar.configure(text=text)

    def _run_in_thread(self, func):
        """Kjør funksjon i egen tråd"""
        thread = threading.Thread(target=func, daemon=True)
        thread.start()

    def _run_das(self):
        """Kjør DAS-oppslag"""
        domain = self.das_entry.get().strip()
        if not domain:
            return

        self.das_button.configure(state="disabled")
        self._set_status(f"Sjekker {domain}...")

        def do_request():
            success, result = self.client.das(domain)
            self.after(0, lambda: self._show_das_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_das_result(self, domain: str, success: bool, result: str):
        """Vis DAS-resultat"""
        self.das_button.configure(state="normal")

        if not success:
            self.das_result.configure(text=f"Feil: {result}", text_color="orange")
            self._set_status("Feil ved oppslag")
            return

        result_lower = result.lower()
        if "available" in result_lower and "not available" not in result_lower:
            self.das_result.configure(
                text=f"✓ {domain} er LEDIG",
                text_color="#00ff00",
                font=ctk.CTkFont(size=24, weight="bold")
            )
        elif "not registered" in result_lower:
            self.das_result.configure(
                text=f"✓ {domain} er LEDIG",
                text_color="#00ff00",
                font=ctk.CTkFont(size=24, weight="bold")
            )
        elif "registered" in result_lower or "delegated" in result_lower:
            self.das_result.configure(
                text=f"✗ {domain} er OPPTATT",
                text_color="#ff4444",
                font=ctk.CTkFont(size=24, weight="bold")
            )
        elif "invalid" in result_lower:
            self.das_result.configure(
                text=f"⚠ {domain} er UGYLDIG",
                text_color="orange",
                font=ctk.CTkFont(size=24, weight="bold")
            )
        else:
            self.das_result.configure(
                text=f"? Ukjent status for {domain}",
                text_color="gray",
                font=ctk.CTkFont(size=18)
            )

        self._set_status(f"DAS-oppslag fullført for {domain}")

    def _run_domain(self):
        """Kjør domeneoppslag"""
        domain = self.domain_entry.get().strip()
        if not domain:
            return

        self.domain_button.configure(state="disabled")
        self._set_status(f"Slår opp {domain}...")

        def do_request():
            success, result = self.client.rdap_domain(domain)
            self.after(0, lambda: self._show_domain_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_domain_result(self, domain: str, success: bool, result):
        """Vis domeneoppslag-resultat"""
        self.domain_button.configure(state="normal")
        self.domain_result.delete("0.0", "end")

        if not success:
            self.domain_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.domain_json_var.get():
            self.domain_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            self.domain_result.insert("0.0", self._format_domain(result))

        self._set_status(f"Domeneoppslag fullført for {domain}")

    def _format_domain(self, data: Dict) -> str:
        """Formater domenedata til lesbar tekst"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  Domene: {data.get('ldhName', data.get('unicodeName', 'Ukjent'))}")
        lines.append("=" * 60)
        lines.append("")

        # Status
        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status: {', '.join(statuses)}")

        # Hendelser
        for event in data.get("events", []):
            action = event.get("eventAction", "")
            date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
            if action == "registration":
                lines.append(f"  Registrert: {date}")
            elif action == "last changed":
                lines.append(f"  Sist endret: {date}")
            elif action == "expiration":
                lines.append(f"  Utløper: {date}")

        # Navneservere
        nameservers = data.get("nameservers", [])
        if nameservers:
            lines.append("")
            lines.append("  Navneservere:")
            for ns in nameservers:
                lines.append(f"    - {ns.get('ldhName', '')}")

        # Registrar
        for entity in data.get("entities", []):
            if "registrar" in entity.get("roles", []):
                lines.append("")
                lines.append(f"  Registrar: {entity.get('handle', '')}")
                vcard = entity.get("vcardArray", [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == "fn":
                            lines.append(f"    Navn: {item[3]}")

        return "\n".join(lines)

    def _run_entity(self):
        """Kjør entitetsoppslag"""
        handle = self.entity_entry.get().strip()
        if not handle:
            return

        self.entity_button.configure(state="disabled")
        self._set_status(f"Slår opp {handle}...")

        def do_request():
            success, result = self.client.rdap_entity(handle)
            self.after(0, lambda: self._show_entity_result(handle, success, result))

        self._run_in_thread(do_request)

    def _show_entity_result(self, handle: str, success: bool, result):
        """Vis entitetsoppslag-resultat"""
        self.entity_button.configure(state="normal")
        self.entity_result.delete("0.0", "end")

        if not success:
            self.entity_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.entity_json_var.get():
            self.entity_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            self.entity_result.insert("0.0", self._format_entity(result))

        self._set_status(f"Entitetsoppslag fullført for {handle}")

    def _format_entity(self, data: Dict) -> str:
        """Formater entitetsdata til lesbar tekst"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  Entitet: {data.get('handle', 'Ukjent')}")
        lines.append("=" * 60)
        lines.append("")

        # Roller
        roles = data.get("roles", [])
        if roles:
            lines.append(f"  Roller: {', '.join(roles)}")

        # Status
        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status: {', '.join(statuses)}")

        # vCard
        vcard = data.get("vcardArray", [])
        if len(vcard) > 1:
            for item in vcard[1]:
                if item[0] == "fn":
                    lines.append(f"  Navn: {item[3]}")
                elif item[0] == "org":
                    lines.append(f"  Organisasjon: {item[3]}")
                elif item[0] == "email":
                    lines.append(f"  E-post: {item[3]}")
                elif item[0] == "tel":
                    lines.append(f"  Telefon: {item[3]}")
                elif item[0] == "adr" and isinstance(item[3], list):
                    city = item[3][3] if len(item[3]) > 3 else ""
                    country = item[3][6] if len(item[3]) > 6 else ""
                    if city or country:
                        lines.append(f"  Sted: {city}, {country}")

        # Hendelser
        for event in data.get("events", []):
            action = event.get("eventAction", "")
            date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
            if action == "registration":
                lines.append(f"  Registrert: {date}")
            elif action == "last changed":
                lines.append(f"  Sist endret: {date}")

        return "\n".join(lines)

    def _run_nameserver(self):
        """Kjør navneserveroppslag"""
        query = self.ns_entry.get().strip()
        if not query:
            return

        self.ns_button.configure(state="disabled")
        self._set_status(f"Søker etter {query}...")

        def do_request():
            if self.ns_mode.get() == "handle":
                success, result = self.client.rdap_nameserver(query)
            else:
                success, result = self.client.rdap_nameserver_search(query)
            self.after(0, lambda: self._show_ns_result(query, success, result))

        self._run_in_thread(do_request)

    def _show_ns_result(self, query: str, success: bool, result):
        """Vis navneserver-resultat"""
        self.ns_button.configure(state="normal")
        self.ns_result.delete("0.0", "end")

        if not success:
            self.ns_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.ns_json_var.get():
            self.ns_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if self.ns_mode.get() == "handle":
                self.ns_result.insert("0.0", self._format_nameserver(result))
            else:
                self.ns_result.insert("0.0", self._format_ns_search(result))

        self._set_status(f"Navneserveroppslag fullført for {query}")

    def _format_nameserver(self, data: Dict) -> str:
        """Formater navneserverdata"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  Navneserver: {data.get('ldhName', 'Ukjent')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Handle: {data.get('handle', '')}")

        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status: {', '.join(statuses)}")

        ips = data.get("ipAddresses", {})
        if ips.get("v4"):
            lines.append("")
            lines.append("  IPv4:")
            for ip in ips["v4"]:
                lines.append(f"    - {ip}")
        if ips.get("v6"):
            lines.append("")
            lines.append("  IPv6:")
            for ip in ips["v6"]:
                lines.append(f"    - {ip}")

        return "\n".join(lines)

    def _format_ns_search(self, data: Dict) -> str:
        """Formater navneserver-søkeresultater"""
        results = data.get("nameserverSearchResults", [])
        if not results:
            return "Ingen navneservere funnet."

        lines = [f"Fant {len(results)} navneserver(e):", ""]
        lines.append(f"{'Handle':<15} {'Navn':<30} {'IPv4':<20}")
        lines.append("-" * 65)

        for ns in results:
            handle = ns.get("handle", "")
            name = ns.get("ldhName", "")
            ips = ns.get("ipAddresses", {})
            v4 = ", ".join(ips.get("v4", []))
            lines.append(f"{handle:<15} {name:<30} {v4:<20}")

        return "\n".join(lines)

    def _run_whois(self):
        """Kjør whois-oppslag"""
        domain = self.whois_entry.get().strip()
        if not domain:
            return

        self.whois_button.configure(state="disabled")
        self._set_status(f"Whois-oppslag for {domain}...")

        def do_request():
            success, result = self.client.whois(domain)
            self.after(0, lambda: self._show_whois_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_whois_result(self, domain: str, success: bool, result: str):
        """Vis whois-resultat"""
        self.whois_button.configure(state="normal")
        self.whois_result.delete("0.0", "end")

        if not success:
            self.whois_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        self.whois_result.insert("0.0", result)
        self._set_status(f"Whois-oppslag fullført for {domain}")


def main():
    app = NoridGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
