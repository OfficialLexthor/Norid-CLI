#!/usr/bin/env python3
"""
Norid CLI - Et kommandolinjeverktøy for Norid sine offentlige tjenester

Bruk: norid [KOMMANDO] [ALTERNATIVER]

Tjenester:
  - RDAP: REST API for domenedata (rdap.norid.no)
  - DAS: Domain Availability Service (finger.norid.no:79)
  - Whois: Tradisjonelt domeneoppslag (whois.norid.no:43)

Ingen autentisering kreves for disse tjenestene.
"""

import json
import socket
import sys
from typing import Any, Dict, List, Optional

import click
import requests
from tabulate import tabulate

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
            "User-Agent": "Norid-CLI/1.0.0"
        })

    def _rdap_request(self, endpoint: str, method: str = "GET") -> Optional[Dict]:
        """Utfør HTTP-forespørsel mot RDAP API"""
        url = f"{self.rdap_url}/{endpoint}"
        try:
            response = self.session.request(method=method, url=url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:
                raise click.ClickException(
                    "Rate-limit overskredet. Maks 300 GET/3000 HEAD per 24 timer, "
                    "eller 10 oppslag per minutt."
                )
            else:
                raise click.ClickException(
                    f"RDAP-feil ({response.status_code}): {response.text}"
                )
        except requests.exceptions.ConnectionError:
            raise click.ClickException(f"Kunne ikke koble til {self.rdap_url}")
        except requests.exceptions.Timeout:
            raise click.ClickException("Forespørselen tok for lang tid (timeout)")

    def _rdap_head(self, endpoint: str) -> bool:
        """Sjekk om et objekt eksisterer via HEAD-request"""
        url = f"{self.rdap_url}/{endpoint}"
        try:
            response = self.session.head(url, timeout=30)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _socket_request(self, host: str, port: int, query: str) -> str:
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
                
                return response.decode("utf-8", errors="replace")
        except socket.timeout:
            raise click.ClickException("Forespørselen tok for lang tid (timeout)")
        except socket.error as e:
            raise click.ClickException(f"Nettverksfeil: {e}")

    # RDAP-metoder
    def rdap_domain(self, domain: str) -> Optional[Dict]:
        """Hent domenedata via RDAP"""
        return self._rdap_request(f"domain/{domain}")

    def rdap_entity(self, handle: str) -> Optional[Dict]:
        """Hent entitet (kontakt/registrar) via RDAP"""
        return self._rdap_request(f"entity/{handle}")

    def rdap_nameserver_handle(self, handle: str) -> Optional[Dict]:
        """Hent navneserver via handle"""
        return self._rdap_request(f"nameserver_handle/{handle}")

    def rdap_nameserver_search(self, pattern: str) -> Optional[Dict]:
        """Søk etter navneservere"""
        return self._rdap_request(f"nameservers?name={pattern}")

    def rdap_domain_exists(self, domain: str) -> bool:
        """Sjekk om domene eksisterer (HEAD-request)"""
        return self._rdap_head(f"domain/{domain}")

    # Whois-metode
    def whois(self, domain: str) -> str:
        """Tradisjonelt whois-oppslag"""
        return self._socket_request(self.whois_host, WHOIS_PORT, domain)

    # DAS-metode
    def das(self, domain: str) -> str:
        """Domain Availability Service (DAS) oppslag"""
        return self._socket_request(self.das_host, DAS_PORT, domain)


# Hjelpefunksjoner for output
def format_json(data: Any) -> str:
    """Formater data som JSON"""
    return json.dumps(data, indent=2, ensure_ascii=False)


def print_table(data: List[Dict], headers: List[str], keys: List[str]) -> None:
    """Skriv ut data som tabell"""
    rows = [[row.get(k, "") for k in keys] for row in data]
    click.echo(tabulate(rows, headers=headers, tablefmt="simple"))


def format_domain_info(data: Dict) -> None:
    """Formater og vis domeneinfo"""
    click.echo()
    click.echo(click.style("=" * 60, fg="blue"))
    
    # Domenenavn
    domain_name = data.get("ldhName", data.get("unicodeName", "Ukjent"))
    click.echo(click.style(f"  Domene: {domain_name}", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="blue"))
    
    # Status
    statuses = data.get("status", [])
    if statuses:
        click.echo(f"\n  Status: {', '.join(statuses)}")
    
    # Hendelser (registrering, sist endret, utløper)
    events = data.get("events", [])
    for event in events:
        action = event.get("eventAction", "")
        date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
        
        if action == "registration":
            click.echo(f"  Registrert: {date}")
        elif action == "last changed":
            click.echo(f"  Sist endret: {date}")
        elif action == "expiration":
            click.echo(f"  Utløper: {date}")
    
    # Navneservere
    nameservers = data.get("nameservers", [])
    if nameservers:
        click.echo(f"\n  Navneservere:")
        for ns in nameservers:
            ns_name = ns.get("ldhName", "")
            click.echo(f"    - {ns_name}")
    
    # Entiteter (registrar, etc.)
    entities = data.get("entities", [])
    for entity in entities:
        roles = entity.get("roles", [])
        handle = entity.get("handle", "")
        
        if "registrar" in roles:
            click.echo(f"\n  Registrar: {handle}")
            vcard = entity.get("vcardArray", [])
            if len(vcard) > 1:
                for item in vcard[1]:
                    if item[0] == "fn":
                        click.echo(f"    Navn: {item[3]}")
    
    # Notices
    notices = data.get("notices", [])
    if notices:
        click.echo(f"\n  Merknader:")
        for notice in notices:
            title = notice.get("title", "")
            if title:
                click.echo(f"    - {title}")
    
    click.echo()


def format_entity_info(data: Dict) -> None:
    """Formater og vis entitetsinfo"""
    click.echo()
    click.echo(click.style("=" * 60, fg="blue"))
    
    handle = data.get("handle", "Ukjent")
    click.echo(click.style(f"  Entitet: {handle}", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="blue"))
    
    # Roller
    roles = data.get("roles", [])
    if roles:
        click.echo(f"\n  Roller: {', '.join(roles)}")
    
    # Status
    statuses = data.get("status", [])
    if statuses:
        click.echo(f"  Status: {', '.join(statuses)}")
    
    # vCard-data
    vcard = data.get("vcardArray", [])
    if len(vcard) > 1:
        for item in vcard[1]:
            if item[0] == "fn":
                click.echo(f"  Navn: {item[3]}")
            elif item[0] == "org":
                click.echo(f"  Organisasjon: {item[3]}")
            elif item[0] == "email":
                click.echo(f"  E-post: {item[3]}")
            elif item[0] == "tel":
                click.echo(f"  Telefon: {item[3]}")
            elif item[0] == "adr":
                # Adresse er en liste
                if isinstance(item[3], list) and len(item[3]) > 3:
                    city = item[3][3] if len(item[3]) > 3 else ""
                    country = item[3][6] if len(item[3]) > 6 else ""
                    if city or country:
                        click.echo(f"  Sted: {city}, {country}")
    
    # Hendelser
    events = data.get("events", [])
    for event in events:
        action = event.get("eventAction", "")
        date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
        
        if action == "registration":
            click.echo(f"  Registrert: {date}")
        elif action == "last changed":
            click.echo(f"  Sist endret: {date}")
    
    click.echo()


def format_nameserver_info(data: Dict) -> None:
    """Formater og vis navneserverinfo"""
    click.echo()
    click.echo(click.style("=" * 60, fg="blue"))
    
    name = data.get("ldhName", "Ukjent")
    click.echo(click.style(f"  Navneserver: {name}", fg="green", bold=True))
    click.echo(click.style("=" * 60, fg="blue"))
    
    handle = data.get("handle", "")
    if handle:
        click.echo(f"\n  Handle: {handle}")
    
    # Status
    statuses = data.get("status", [])
    if statuses:
        click.echo(f"  Status: {', '.join(statuses)}")
    
    # IP-adresser
    ip_addresses = data.get("ipAddresses", {})
    v4 = ip_addresses.get("v4", [])
    v6 = ip_addresses.get("v6", [])
    
    if v4:
        click.echo(f"\n  IPv4:")
        for ip in v4:
            click.echo(f"    - {ip}")
    
    if v6:
        click.echo(f"\n  IPv6:")
        for ip in v6:
            click.echo(f"    - {ip}")
    
    # Hendelser
    events = data.get("events", [])
    for event in events:
        action = event.get("eventAction", "")
        date = event.get("eventDate", "")[:10] if event.get("eventDate") else ""
        
        if action == "registration":
            click.echo(f"\n  Registrert: {date}")
        elif action == "last changed":
            click.echo(f"  Sist endret: {date}")
    
    click.echo()


def format_nameserver_search_results(data: Dict) -> None:
    """Formater og vis søkeresultater for navneservere"""
    results = data.get("nameserverSearchResults", [])
    
    if not results:
        click.echo("Ingen navneservere funnet.")
        return
    
    click.echo(f"\nFant {len(results)} navneserver(e):\n")
    
    headers = ["Handle", "Navn", "IPv4", "IPv6"]
    rows = []
    
    for ns in results:
        handle = ns.get("handle", "")
        name = ns.get("ldhName", "")
        ips = ns.get("ipAddresses", {})
        v4 = ", ".join(ips.get("v4", []))
        v6 = ", ".join(ips.get("v6", []))[:30] + "..." if len(", ".join(ips.get("v6", []))) > 30 else ", ".join(ips.get("v6", []))
        rows.append([handle, name, v4, v6])
    
    click.echo(tabulate(rows, headers=headers, tablefmt="simple"))
    click.echo()


def format_das_result(response: str, domain: str) -> None:
    """Formater og vis DAS-resultat"""
    click.echo()
    
    response_lower = response.lower()
    
    if "available" in response_lower and "not available" not in response_lower:
        click.echo(click.style(f"✓ {domain} er LEDIG", fg="green", bold=True))
    elif "not registered" in response_lower:
        click.echo(click.style(f"✓ {domain} er LEDIG", fg="green", bold=True))
    elif "registered" in response_lower or "delegated" in response_lower:
        click.echo(click.style(f"✗ {domain} er OPPTATT", fg="red", bold=True))
    elif "invalid" in response_lower:
        click.echo(click.style(f"✗ {domain} er UGYLDIG", fg="yellow", bold=True))
    else:
        click.echo(click.style(f"? {domain} - ukjent status", fg="yellow"))
        click.echo(f"\nRå respons:\n{response}")
    
    click.echo()


# CLI-grupper og kommandoer
@click.group()
@click.option("--test", "-t", is_flag=True, help="Bruk testmiljø")
@click.version_option(version="1.0.0", prog_name="norid")
@click.pass_context
def cli(ctx, test: bool):
    """Norid CLI - Slå opp .no-domener uten autentisering.
    
    Tjenester som støttes:
    
    \b
      - RDAP: REST API for domenedata
      - DAS: Sjekk om domene er ledig
      - Whois: Tradisjonelt domeneoppslag
    """
    ctx.ensure_object(dict)
    ctx.obj["client"] = NoridClient(use_test=test)
    ctx.obj["test"] = test


# === DOMAIN ===
@cli.command()
@click.argument("domain")
@click.option("--available", "-a", is_flag=True, help="Kun sjekk om domene eksisterer (HEAD)")
@click.option("--json", "as_json", is_flag=True, help="Output som JSON")
@click.pass_context
def domain(ctx, domain: str, available: bool, as_json: bool):
    """Slå opp domene via RDAP
    
    \b
    Eksempler:
      norid domain norid.no
      norid domain norid.no --json
      norid domain example.no --available
    """
    client = ctx.obj["client"]
    
    if available:
        exists = client.rdap_domain_exists(domain)
        if exists:
            click.echo(click.style(f"✗ {domain} er registrert", fg="red"))
        else:
            click.echo(click.style(f"✓ {domain} er ikke registrert", fg="green"))
        return
    
    data = client.rdap_domain(domain)
    
    if not data:
        click.echo(click.style(f"Domene ikke funnet: {domain}", fg="yellow"))
        return
    
    if as_json:
        click.echo(format_json(data))
    else:
        format_domain_info(data)


# === ENTITY ===
@cli.command()
@click.argument("handle")
@click.option("--json", "as_json", is_flag=True, help="Output som JSON")
@click.pass_context
def entity(ctx, handle: str, as_json: bool):
    """Slå opp entitet (kontakt/registrar) via RDAP
    
    \b
    Eksempler:
      norid entity reg1-NORID
      norid entity NH55R-NORID
    """
    client = ctx.obj["client"]
    data = client.rdap_entity(handle)
    
    if not data:
        click.echo(click.style(f"Entitet ikke funnet: {handle}", fg="yellow"))
        return
    
    if as_json:
        click.echo(format_json(data))
    else:
        format_entity_info(data)


# === NAMESERVER ===
@cli.command()
@click.argument("handle")
@click.option("--json", "as_json", is_flag=True, help="Output som JSON")
@click.pass_context
def nameserver(ctx, handle: str, as_json: bool):
    """Slå opp navneserver via handle
    
    \b
    Eksempler:
      norid nameserver X11H-NORID
    """
    client = ctx.obj["client"]
    data = client.rdap_nameserver_handle(handle)
    
    if not data:
        click.echo(click.style(f"Navneserver ikke funnet: {handle}", fg="yellow"))
        return
    
    if as_json:
        click.echo(format_json(data))
    else:
        format_nameserver_info(data)


# === SEARCH ===
@cli.group()
def search():
    """Søk etter objekter"""
    pass


@search.command("nameservers")
@click.argument("pattern")
@click.option("--json", "as_json", is_flag=True, help="Output som JSON")
@click.pass_context
def search_nameservers(ctx, pattern: str, as_json: bool):
    """Søk etter navneservere med hostname
    
    \b
    Eksempler:
      norid search nameservers x.nic.no
      norid search nameservers "*.nic.no"
    """
    client = ctx.obj["client"]
    data = client.rdap_nameserver_search(pattern)
    
    if not data:
        click.echo("Ingen navneservere funnet.")
        return
    
    if as_json:
        click.echo(format_json(data))
    else:
        format_nameserver_search_results(data)


# === WHOIS ===
@cli.command()
@click.argument("domain")
@click.pass_context
def whois(ctx, domain: str):
    """Tradisjonelt whois-oppslag
    
    \b
    Eksempler:
      norid whois norid.no
      norid whois --test draupne.no
    """
    client = ctx.obj["client"]
    env = "test" if ctx.obj["test"] else "prod"
    
    click.echo(click.style(f"\nWhois-oppslag for {domain} ({env}):\n", fg="blue"))
    
    response = client.whois(domain)
    click.echo(response)


# === DAS ===
@cli.command()
@click.argument("domain")
@click.option("--raw", "-r", is_flag=True, help="Vis rå respons")
@click.pass_context
def das(ctx, domain: str, raw: bool):
    """Sjekk om domene er ledig (DAS)
    
    \b
    Eksempler:
      norid das example.no
      norid das --test domain.no
    """
    client = ctx.obj["client"]
    response = client.das(domain)
    
    if raw:
        click.echo(response)
    else:
        format_das_result(response, domain)


if __name__ == "__main__":
    cli()
