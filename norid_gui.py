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

# DNS-oppslag
try:
    import dns.resolver as dns_resolver
    DNS_AVAILABLE = True
except ImportError:
    dns_resolver = None
    DNS_AVAILABLE = False

# ============================================================================
# FARGEPALETT - Developer Tool / IDE Theme
# ============================================================================
COLORS = {
    "bg_dark": "#0F172A",        # Bakgrunn (slate-900)
    "bg_card": "#1E293B",        # Kort/panel bakgrunn (slate-800)
    "bg_input": "#334155",       # Input bakgrunn (slate-700)
    "primary": "#3B82F6",        # Primær blå
    "primary_hover": "#2563EB",  # Primær hover
    "success": "#22C55E",        # Grønn - ledig
    "error": "#EF4444",          # Rød - opptatt
    "warning": "#F59E0B",        # Oransje - advarsel
    "text": "#F1F5F9",           # Hovedtekst (slate-100)
    "text_muted": "#94A3B8",     # Dempet tekst (slate-400)
    "border": "#475569",         # Kantlinje (slate-600)
    "accent": "#60A5FA",         # Aksent lyseblå
}

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

    def dns_lookup(self, domain: str) -> tuple[bool, Dict[str, list]]:
        """Hent DNS-records for et domene"""
        records = {}
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']
        
        if DNS_AVAILABLE and dns_resolver:
            for rtype in record_types:
                try:
                    answers = dns_resolver.resolve(domain, rtype)
                    records[rtype] = [str(r) for r in answers]
                except dns_resolver.NoAnswer:
                    pass
                except dns_resolver.NXDOMAIN:
                    return False, f"Domenet {domain} finnes ikke"
                except dns_resolver.NoNameservers:
                    return False, f"Ingen navneservere svarer for {domain}"
                except Exception:
                    pass
        else:
            # Fallback: Google DNS-over-HTTPS
            for rtype in record_types:
                try:
                    url = f"https://dns.google/resolve?name={domain}&type={rtype}"
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("Answer"):
                            records[rtype] = [a["data"] for a in data["Answer"]]
                except Exception:
                    pass
        
        if not records:
            return False, "Ingen DNS-records funnet"
        
        return True, records


class LoadingIndicator(ctk.CTkFrame):
    """Animert loading-indikator"""
    
    def __init__(self, parent, text="Laster...", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"]
        )
        self.label.pack()
        
        self.dots = 0
        self.base_text = text
        self.animating = False
    
    def start(self, text="Laster"):
        """Start animasjon"""
        self.base_text = text
        self.animating = True
        self._animate()
    
    def stop(self):
        """Stopp animasjon"""
        self.animating = False
    
    def _animate(self):
        """Animer prikker"""
        if not self.animating:
            return
        
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.label.configure(text=f"{self.base_text}{dots_text}")
        self.after(300, self._animate)


class ResultCard(ctk.CTkFrame):
    """Stilisert resultatkort for DAS-oppslag"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Innhold
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, padx=40, pady=40)
        
        # Ikon/symbol
        self.icon_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=COLORS["text_muted"]
        )
        self.icon_label.pack(pady=(0, 10))
        
        # Hovedtekst
        self.main_label = ctk.CTkLabel(
            self.content_frame,
            text="Skriv inn et domenenavn",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"]
        )
        self.main_label.pack(pady=(0, 5))
        
        # Undertekst
        self.sub_label = ctk.CTkLabel(
            self.content_frame,
            text="og klikk 'Sjekk' for å se om det er ledig",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"]
        )
        self.sub_label.pack()
    
    def show_loading(self, domain: str):
        """Vis loading-tilstand"""
        self.configure(border_color=COLORS["primary"])
        self.icon_label.configure(text="...", text_color=COLORS["primary"])
        self.main_label.configure(text=f"Sjekker {domain}", text_color=COLORS["text"])
        self.sub_label.configure(text="Kobler til Norid...")
    
    def show_available(self, domain: str):
        """Vis ledig-tilstand"""
        self.configure(border_color=COLORS["success"])
        self.icon_label.configure(text="[OK]", text_color=COLORS["success"])
        self.main_label.configure(text=domain, text_color=COLORS["success"])
        self.sub_label.configure(text="Dette domenet er LEDIG for registrering")
    
    def show_taken(self, domain: str):
        """Vis opptatt-tilstand"""
        self.configure(border_color=COLORS["error"])
        self.icon_label.configure(text="[X]", text_color=COLORS["error"])
        self.main_label.configure(text=domain, text_color=COLORS["error"])
        self.sub_label.configure(text="Dette domenet er allerede REGISTRERT")
    
    def show_invalid(self, domain: str):
        """Vis ugyldig-tilstand"""
        self.configure(border_color=COLORS["warning"])
        self.icon_label.configure(text="[!]", text_color=COLORS["warning"])
        self.main_label.configure(text=domain, text_color=COLORS["warning"])
        self.sub_label.configure(text="Ugyldig domenenavn")
    
    def show_error(self, message: str):
        """Vis feil-tilstand"""
        self.configure(border_color=COLORS["error"])
        self.icon_label.configure(text="[!]", text_color=COLORS["error"])
        self.main_label.configure(text="Feil", text_color=COLORS["error"])
        self.sub_label.configure(text=message)
    
    def reset(self):
        """Tilbakestill til standardtilstand"""
        self.configure(border_color=COLORS["border"])
        self.icon_label.configure(text="", text_color=COLORS["text_muted"])
        self.main_label.configure(text="Skriv inn et domenenavn", text_color=COLORS["text"])
        self.sub_label.configure(text="og klikk 'Sjekk' for å se om det er ledig")


class NoridGUI(ctk.CTk):
    """Hovedvindu for Norid GUI"""

    def __init__(self):
        super().__init__()

        # Vinduinnstillinger
        self.title("Norid - Domeneoppslag for .no")
        self.geometry("950x750")
        self.minsize(850, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        # Klient
        self.client = NoridClient(use_test=False)

        # Konfigurer grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Bygg UI
        self._create_header()
        self._create_tabs()
        self._create_statusbar()

    def _create_header(self):
        """Opprett header med logo og innstillinger"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header_frame.grid_columnconfigure(1, weight=1)

        # Logo/tittel
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Norid",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["text"]
        )
        title_label.pack(side="left")
        
        # Versjon/tag
        version_label = ctk.CTkLabel(
            title_frame,
            text="  CLI",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["accent"]
        )
        version_label.pack(side="left", pady=(8, 0))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Slå opp .no-domener uten autentisering",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Miljøvalg
        env_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        env_frame.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)

        env_label = ctk.CTkLabel(
            env_frame,
            text="Miljø",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        env_label.pack(side="left", padx=(0, 12))

        self.env_var = ctk.StringVar(value="Produksjon")
        self.env_menu = ctk.CTkSegmentedButton(
            env_frame,
            values=["Produksjon", "Test"],
            variable=self.env_var,
            command=self._on_env_change,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg_card"],
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"],
            unselected_color=COLORS["bg_input"],
            unselected_hover_color=COLORS["border"]
        )
        self.env_menu.pack(side="left")

    def _create_tabs(self):
        """Opprett faner for ulike funksjoner"""
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_card"],
            segmented_button_fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_selected_hover_color=COLORS["primary_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["bg_input"],
            corner_radius=12
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)

        # Legg til faner (uten emojis for profesjonelt utseende)
        self.tabview.add("DAS")
        self.tabview.add("Domene")
        self.tabview.add("Entitet")
        self.tabview.add("Navneserver")
        self.tabview.add("Whois")
        self.tabview.add("DNS")

        # Konfigurer hver fane
        self._setup_das_tab()
        self._setup_domain_tab()
        self._setup_entity_tab()
        self._setup_nameserver_tab()
        self._setup_whois_tab()
        self._setup_dns_tab()

    def _setup_das_tab(self):
        """Sett opp DAS-fanen - sjekk om domene er ledig"""
        tab = self.tabview.tab("DAS")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Toppseksjon
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.grid(row=0, column=0, pady=(24, 16))

        # Beskrivelse
        desc = ctk.CTkLabel(
            top_frame,
            text="Domain Availability Service",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        desc.pack(pady=(0, 4))
        
        desc_sub = ctk.CTkLabel(
            top_frame,
            text="Sjekk om et .no-domene er ledig for registrering",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        desc_sub.pack(pady=(0, 16))

        # Input-ramme
        input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        input_frame.pack()

        self.das_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="domenenavn.no",
            width=380,
            height=44,
            font=ctk.CTkFont(size=15),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"],
            corner_radius=8
        )
        self.das_entry.pack(side="left", padx=(0, 12))
        self.das_entry.bind("<Return>", lambda e: self._run_das())

        self.das_button = ctk.CTkButton(
            input_frame,
            text="Sjekk",
            command=self._run_das,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.das_button.pack(side="left")

        # Resultatkort
        self.das_result_card = ResultCard(tab)
        self.das_result_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

    def _setup_domain_tab(self):
        """Sett opp domeneoppslag-fanen"""
        tab = self.tabview.tab("Domene")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=(24, 16))

        self.domain_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Domenenavn (f.eks. norid.no)",
            width=380,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.domain_entry.pack(side="left", padx=(0, 12))
        self.domain_entry.bind("<Return>", lambda e: self._run_domain())

        self.domain_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_domain,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.domain_button.pack(side="left", padx=(0, 12))

        self.domain_json_var = ctk.BooleanVar(value=False)
        self.domain_json_check = ctk.CTkSwitch(
            input_frame,
            text="JSON",
            variable=self.domain_json_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            progress_color=COLORS["primary"]
        )
        self.domain_json_check.pack(side="left")

        # Resultat
        self.domain_result = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="SF Mono, Menlo, Monaco, Consolas, monospace", size=13),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.domain_result.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

    def _setup_entity_tab(self):
        """Sett opp entitetsoppslag-fanen"""
        tab = self.tabview.tab("Entitet")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=(24, 16))

        label = ctk.CTkLabel(
            input_frame,
            text="Handle:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        label.pack(side="left", padx=(0, 12))

        self.entity_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="f.eks. reg1-NORID",
            width=320,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.entity_entry.pack(side="left", padx=(0, 12))
        self.entity_entry.bind("<Return>", lambda e: self._run_entity())

        self.entity_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_entity,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.entity_button.pack(side="left", padx=(0, 12))

        self.entity_json_var = ctk.BooleanVar(value=False)
        self.entity_json_check = ctk.CTkSwitch(
            input_frame,
            text="JSON",
            variable=self.entity_json_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            progress_color=COLORS["primary"]
        )
        self.entity_json_check.pack(side="left")

        # Resultat
        self.entity_result = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="SF Mono, Menlo, Monaco, Consolas, monospace", size=13),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.entity_result.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

    def _setup_nameserver_tab(self):
        """Sett opp navneserver-fanen"""
        tab = self.tabview.tab("Navneserver")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Valg mellom oppslag og søk
        mode_frame = ctk.CTkFrame(tab, fg_color="transparent")
        mode_frame.grid(row=0, column=0, pady=(24, 12))

        self.ns_mode = ctk.StringVar(value="handle")
        
        handle_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Oppslag via handle",
            variable=self.ns_mode,
            value="handle",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"]
        )
        handle_radio.pack(side="left", padx=(0, 24))
        
        search_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Søk via hostname",
            variable=self.ns_mode,
            value="search",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"]
        )
        search_radio.pack(side="left")

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, pady=(0, 16))

        self.ns_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="X11H-NORID eller *.nic.no",
            width=380,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.ns_entry.pack(side="left", padx=(0, 12))
        self.ns_entry.bind("<Return>", lambda e: self._run_nameserver())

        self.ns_button = ctk.CTkButton(
            input_frame,
            text="Søk",
            command=self._run_nameserver,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.ns_button.pack(side="left", padx=(0, 12))

        self.ns_json_var = ctk.BooleanVar(value=False)
        self.ns_json_check = ctk.CTkSwitch(
            input_frame,
            text="JSON",
            variable=self.ns_json_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            progress_color=COLORS["primary"]
        )
        self.ns_json_check.pack(side="left")

        # Resultat
        self.ns_result = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="SF Mono, Menlo, Monaco, Consolas, monospace", size=13),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.ns_result.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))

    def _setup_whois_tab(self):
        """Sett opp whois-fanen"""
        tab = self.tabview.tab("Whois")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=(24, 16))

        self.whois_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Domenenavn (f.eks. norid.no)",
            width=380,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.whois_entry.pack(side="left", padx=(0, 12))
        self.whois_entry.bind("<Return>", lambda e: self._run_whois())

        self.whois_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_whois,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.whois_button.pack(side="left")

        # Resultat
        self.whois_result = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="SF Mono, Menlo, Monaco, Consolas, monospace", size=12),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.whois_result.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

    def _setup_dns_tab(self):
        """Sett opp DNS-fanen"""
        tab = self.tabview.tab("DNS")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Input-ramme
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, pady=(24, 16))

        self.dns_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Domenenavn (f.eks. norid.no)",
            width=380,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.dns_entry.pack(side="left", padx=(0, 12))
        self.dns_entry.bind("<Return>", lambda e: self._run_dns())

        self.dns_button = ctk.CTkButton(
            input_frame,
            text="Slå opp",
            command=self._run_dns,
            width=100,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=8
        )
        self.dns_button.pack(side="left")

        # JSON checkbox
        self.dns_json_var = ctk.BooleanVar(value=False)
        json_check = ctk.CTkCheckBox(
            input_frame,
            text="Vis som JSON",
            variable=self.dns_json_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"]
        )
        json_check.pack(side="left", padx=(16, 0))

        # Resultat
        self.dns_result = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="SF Mono, Menlo, Monaco, Consolas, monospace", size=12),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.dns_result.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.dns_result.insert("1.0", "Skriv inn et domenenavn for å hente DNS-records\n\nViser: A, AAAA, MX, NS, TXT, CNAME")

    def _create_statusbar(self):
        """Opprett statuslinje"""
        status_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=36, corner_radius=0)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.grid_propagate(False)
        
        self.statusbar = ctk.CTkLabel(
            status_frame,
            text="Klar",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.statusbar.pack(side="left", padx=24, pady=8)
        
        # Miljøindikator i statuslinjen
        self.env_indicator = ctk.CTkLabel(
            status_frame,
            text="rdap.norid.no",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.env_indicator.pack(side="right", padx=24, pady=8)

    def _on_env_change(self, value: str):
        """Håndter miljøbytte"""
        use_test = value == "Test"
        self.client = NoridClient(use_test=use_test)
        
        if use_test:
            self._set_status("Byttet til testmiljø")
            self.env_indicator.configure(text="rdap.test.norid.no", text_color=COLORS["warning"])
        else:
            self._set_status("Byttet til produksjonsmiljø")
            self.env_indicator.configure(text="rdap.norid.no", text_color=COLORS["text_muted"])

    def _set_status(self, text: str):
        """Oppdater statuslinjen"""
        self.statusbar.configure(text=text)

    def _run_in_thread(self, func):
        """Kjør funksjon i egen tråd"""
        thread = threading.Thread(target=func, daemon=True)
        thread.start()

    # ========================================================================
    # DAS
    # ========================================================================
    def _run_das(self):
        """Kjør DAS-oppslag"""
        domain = self.das_entry.get().strip()
        if not domain:
            return

        # Legg til .no hvis det mangler
        if not domain.endswith(".no"):
            domain = domain + ".no"
            self.das_entry.delete(0, "end")
            self.das_entry.insert(0, domain)

        self.das_button.configure(state="disabled", text="...")
        self.das_result_card.show_loading(domain)
        self._set_status(f"Sjekker {domain}...")

        def do_request():
            success, result = self.client.das(domain)
            self.after(0, lambda: self._show_das_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_das_result(self, domain: str, success: bool, result: str):
        """Vis DAS-resultat"""
        self.das_button.configure(state="normal", text="Sjekk")

        if not success:
            self.das_result_card.show_error(result)
            self._set_status("Feil ved oppslag")
            return

        result_lower = result.lower()
        if "available" in result_lower and "not available" not in result_lower:
            self.das_result_card.show_available(domain)
        elif "not registered" in result_lower:
            self.das_result_card.show_available(domain)
        elif "registered" in result_lower or "delegated" in result_lower:
            self.das_result_card.show_taken(domain)
        elif "invalid" in result_lower:
            self.das_result_card.show_invalid(domain)
        else:
            self.das_result_card.show_error(f"Ukjent status: {result[:100]}")

        self._set_status(f"Oppslag fullført for {domain}")

    # ========================================================================
    # Domeneoppslag
    # ========================================================================
    def _run_domain(self):
        """Kjør domeneoppslag"""
        domain = self.domain_entry.get().strip()
        if not domain:
            return

        self.domain_button.configure(state="disabled", text="...")
        self._set_status(f"Slår opp {domain}...")

        def do_request():
            success, result = self.client.rdap_domain(domain)
            self.after(0, lambda: self._show_domain_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_domain_result(self, domain: str, success: bool, result):
        """Vis domeneoppslag-resultat"""
        self.domain_button.configure(state="normal", text="Slå opp")
        self.domain_result.delete("0.0", "end")

        if not success:
            self.domain_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.domain_json_var.get():
            self.domain_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            self.domain_result.insert("0.0", self._format_domain(result))

        self._set_status(f"Oppslag fullført for {domain}")

    def _format_domain(self, data: Dict) -> str:
        """Formater domenedata til lesbar tekst"""
        lines = []
        domain_name = data.get('ldhName', data.get('unicodeName', 'Ukjent'))
        
        lines.append(f"{'─' * 56}")
        lines.append(f"  DOMENE: {domain_name}")
        lines.append(f"{'─' * 56}")
        lines.append("")

        # Status
        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status      │ {', '.join(statuses)}")

        # Hendelser
        for event in data.get("events", []):
            action = event.get("eventAction", "")
            date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
            if action == "registration":
                lines.append(f"  Registrert  │ {date}")
            elif action == "last changed":
                lines.append(f"  Sist endret │ {date}")
            elif action == "expiration":
                lines.append(f"  Utløper     │ {date}")

        # Navneservere
        nameservers = data.get("nameservers", [])
        if nameservers:
            lines.append("")
            lines.append("  NAVNESERVERE")
            lines.append(f"  {'─' * 40}")
            for ns in nameservers:
                lines.append(f"    • {ns.get('ldhName', '')}")

        # Registrar
        for entity in data.get("entities", []):
            if "registrar" in entity.get("roles", []):
                lines.append("")
                lines.append("  REGISTRAR")
                lines.append(f"  {'─' * 40}")
                lines.append(f"    Handle: {entity.get('handle', '')}")
                vcard = entity.get("vcardArray", [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == "fn":
                            lines.append(f"    Navn:   {item[3]}")

        return "\n".join(lines)

    # ========================================================================
    # Entitetsoppslag
    # ========================================================================
    def _run_entity(self):
        """Kjør entitetsoppslag"""
        handle = self.entity_entry.get().strip()
        if not handle:
            return

        self.entity_button.configure(state="disabled", text="...")
        self._set_status(f"Slår opp {handle}...")

        def do_request():
            success, result = self.client.rdap_entity(handle)
            self.after(0, lambda: self._show_entity_result(handle, success, result))

        self._run_in_thread(do_request)

    def _show_entity_result(self, handle: str, success: bool, result):
        """Vis entitetsoppslag-resultat"""
        self.entity_button.configure(state="normal", text="Slå opp")
        self.entity_result.delete("0.0", "end")

        if not success:
            self.entity_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.entity_json_var.get():
            self.entity_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            self.entity_result.insert("0.0", self._format_entity(result))

        self._set_status(f"Oppslag fullført for {handle}")

    def _format_entity(self, data: Dict) -> str:
        """Formater entitetsdata til lesbar tekst"""
        lines = []
        handle = data.get('handle', 'Ukjent')
        
        lines.append(f"{'─' * 56}")
        lines.append(f"  ENTITET: {handle}")
        lines.append(f"{'─' * 56}")
        lines.append("")

        # Roller
        roles = data.get("roles", [])
        if roles:
            lines.append(f"  Roller      │ {', '.join(roles)}")

        # Status
        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status      │ {', '.join(statuses)}")

        # vCard
        vcard = data.get("vcardArray", [])
        if len(vcard) > 1:
            lines.append("")
            lines.append("  KONTAKTINFO")
            lines.append(f"  {'─' * 40}")
            for item in vcard[1]:
                if item[0] == "fn":
                    lines.append(f"    Navn:     {item[3]}")
                elif item[0] == "org":
                    lines.append(f"    Org:      {item[3]}")
                elif item[0] == "email":
                    lines.append(f"    E-post:   {item[3]}")
                elif item[0] == "tel":
                    lines.append(f"    Telefon:  {item[3]}")
                elif item[0] == "adr" and isinstance(item[3], list):
                    city = item[3][3] if len(item[3]) > 3 else ""
                    country = item[3][6] if len(item[3]) > 6 else ""
                    if city or country:
                        lines.append(f"    Sted:     {city}, {country}")

        # Hendelser
        events = data.get("events", [])
        if events:
            lines.append("")
            for event in events:
                action = event.get("eventAction", "")
                date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
                if action == "registration":
                    lines.append(f"  Registrert  │ {date}")
                elif action == "last changed":
                    lines.append(f"  Sist endret │ {date}")

        return "\n".join(lines)

    # ========================================================================
    # Navneserver
    # ========================================================================
    def _run_nameserver(self):
        """Kjør navneserveroppslag"""
        query = self.ns_entry.get().strip()
        if not query:
            return

        self.ns_button.configure(state="disabled", text="...")
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
        self.ns_button.configure(state="normal", text="Søk")
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

        self._set_status(f"Oppslag fullført for {query}")

    def _format_nameserver(self, data: Dict) -> str:
        """Formater navneserverdata"""
        lines = []
        name = data.get('ldhName', 'Ukjent')
        
        lines.append(f"{'─' * 56}")
        lines.append(f"  NAVNESERVER: {name}")
        lines.append(f"{'─' * 56}")
        lines.append("")
        lines.append(f"  Handle      │ {data.get('handle', '')}")

        statuses = data.get("status", [])
        if statuses:
            lines.append(f"  Status      │ {', '.join(statuses)}")

        ips = data.get("ipAddresses", {})
        if ips.get("v4"):
            lines.append("")
            lines.append("  IPv4-ADRESSER")
            lines.append(f"  {'─' * 40}")
            for ip in ips["v4"]:
                lines.append(f"    • {ip}")
                
        if ips.get("v6"):
            lines.append("")
            lines.append("  IPv6-ADRESSER")
            lines.append(f"  {'─' * 40}")
            for ip in ips["v6"]:
                lines.append(f"    • {ip}")

        return "\n".join(lines)

    def _format_ns_search(self, data: Dict) -> str:
        """Formater navneserver-søkeresultater"""
        results = data.get("nameserverSearchResults", [])
        if not results:
            return "Ingen navneservere funnet."

        lines = []
        lines.append(f"  Fant {len(results)} navneserver(e)")
        lines.append(f"{'─' * 56}")
        lines.append("")
        lines.append(f"  {'HANDLE':<16} {'NAVN':<28} {'IPv4'}")
        lines.append(f"  {'─' * 16} {'─' * 28} {'─' * 10}")

        for ns in results:
            handle = ns.get("handle", "")[:15]
            name = ns.get("ldhName", "")[:27]
            ips = ns.get("ipAddresses", {})
            v4 = ", ".join(ips.get("v4", []))[:20]
            lines.append(f"  {handle:<16} {name:<28} {v4}")

        return "\n".join(lines)

    # ========================================================================
    # Whois
    # ========================================================================
    def _run_whois(self):
        """Kjør whois-oppslag"""
        domain = self.whois_entry.get().strip()
        if not domain:
            return

        self.whois_button.configure(state="disabled", text="...")
        self._set_status(f"Whois-oppslag for {domain}...")

        def do_request():
            success, result = self.client.whois(domain)
            self.after(0, lambda: self._show_whois_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_whois_result(self, domain: str, success: bool, result: str):
        """Vis whois-resultat"""
        self.whois_button.configure(state="normal", text="Slå opp")
        self.whois_result.delete("0.0", "end")

        if not success:
            self.whois_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        self.whois_result.insert("0.0", result)
        self._set_status(f"Whois-oppslag fullført for {domain}")

    def _run_dns(self):
        """Kjør DNS-oppslag"""
        domain = self.dns_entry.get().strip()
        if not domain:
            return

        self.dns_button.configure(state="disabled", text="...")
        self._set_status(f"Henter DNS-records for {domain}...")

        def do_request():
            success, result = self.client.dns_lookup(domain)
            self.after(0, lambda: self._show_dns_result(domain, success, result))

        self._run_in_thread(do_request)

    def _show_dns_result(self, domain: str, success: bool, result):
        """Vis DNS-resultat"""
        self.dns_button.configure(state="normal", text="Slå opp")
        self.dns_result.delete("0.0", "end")

        if not success:
            self.dns_result.insert("0.0", f"Feil: {result}")
            self._set_status("Feil ved oppslag")
            return

        if self.dns_json_var.get():
            import json
            self.dns_result.insert("0.0", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            lines = []
            lines.append(f"DNS Records for {domain}")
            lines.append("=" * 50)
            lines.append("")
            lines.append(f"{'Type':<8} Record")
            lines.append("-" * 50)
            
            for rtype, values in result.items():
                for value in values:
                    lines.append(f"{rtype:<8} {value}")
            
            self.dns_result.insert("0.0", "\n".join(lines))

        self._set_status(f"DNS-oppslag fullført for {domain}")


def main():
    app = NoridGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
