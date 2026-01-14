<div align="center">

# Norid CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

Et kommandolinjeverktøy for [Norid](https://www.norid.no/) sine offentlige tjenester.

Slå opp .no-domener uten autentisering.

[Funksjoner](#funksjoner) • [Hurtigstart](#hurtigstart) • [Installasjon](#installasjon) • [Bruk](#bruk) • [Referanser](#referanser)

</div>

---

## Funksjoner

| Funksjon | Beskrivelse |
|----------|-------------|
| **RDAP** | REST API for domenedata (JSON-format) |
| **DAS** | Sjekk om domene er ledig (Domain Availability Service) |
| **Whois** | Tradisjonelt domeneoppslag |
| **Entiteter** | Slå opp registrarer og kontaktpersoner |
| **Navneservere** | Slå opp og søk etter navneservere |
| **GUI** | Grafisk grensesnitt med moderne utseende |
| **Web GUI** | Webbasert grensesnitt (Flask) |

> **Note**  
> Ingen autentisering kreves. Alle tjenester er offentlig tilgjengelige.

## Hurtigstart

<table>
<tr>
<td width="33%">

### macOS
```bash
./norid.command
```

</td>
<td width="33%">

### Linux
```bash
./norid.sh
```

</td>
<td width="33%">

### Windows
```batch
norid.bat
```

</td>
</tr>
</table>

> **Note**  
> Første gang opprettes virtuelt miljø og avhengigheter installeres automatisk.

### GUI-versjon

Start det grafiske grensesnittet:

```bash
# Via Python
python norid_gui.py

# Eller via pip-installasjon
norid-gui
```

![Norid GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)

GUI-versjonen har:
- Moderne mørkt tema
- Faner for alle funksjoner
- Bytt mellom test- og produksjonsmiljø
- JSON-visning for alle oppslag

### Web GUI

Start webgrensesnittet:

```bash
# Via Python
python norid_web.py

# Eller via pip-installasjon
norid-web
```

Åpne deretter http://localhost:5000 i nettleseren.

![Norid Web](https://img.shields.io/badge/Web-Flask-green)

Web GUI har:
- Mørkt utviklervennlig tema
- Alle 5 tjenester i faner (DAS, Domene, Entitet, Navneserver, Whois)
- Bytt mellom test- og produksjonsmiljø
- Responsivt design for mobil og desktop
- JSON-toggle for alle oppslag

### Interaktivt menysystem (CLI)

Når du starter programmet får du en brukervennlig meny:

```
  _   _            _     _    ____ _     ___ 
 | \ | | ___  _ __(_) __| |  / ___| |   |_ _|
 |  \| |/ _ \| '__| |/ _` | | |   | |    | | 
 | |\  | (_) | |  | | (_| | | |___| |___ | | 
 |_| \_|\___/|_|  |_|\__,_|  \____|_____|___|

──────────────────────────────────────────────────
  Slå opp .no-domener uten autentisering
──────────────────────────────────────────────────

HOVEDMENY [Produksjon]

  1) 🔍 Domeneoppslag (RDAP)
  2) ✓  Sjekk om ledig (DAS)
  3) 📋 Whois-oppslag
  4) 👤 Entitetsoppslag
  5) 🖥️  Navneserveroppslag

  8) ⚙️  Innstillinger
  9) 📖 Avansert modus
  0) 🚪 Avslutt

Valg: 
```

<details>
<summary><strong>Vis alle menyvalg</strong></summary>

| Meny | Funksjoner |
|------|------------|
| **1) Domeneoppslag** | RDAP-oppslag, sjekk eksistens, JSON-visning |
| **2) Sjekk om ledig** | DAS-sjekk for å se om domene er ledig |
| **3) Whois-oppslag** | Tradisjonelt whois-oppslag |
| **4) Entitetsoppslag** | Slå opp registrar eller kontaktperson |
| **5) Navneserveroppslag** | Slå opp eller søk etter navneservere |
| **8) Innstillinger** | Bytt mellom test- og produksjonsmiljø |
| **9) Avansert modus** | Skriv kommandoer direkte |

</details>

## Installasjon

### Via pip (anbefalt)

```bash
git clone https://github.com/OfficialLexthor/Norid-CLI.git
cd Norid-CLI
pip install -e .
```

### Manuelt

```bash
git clone https://github.com/OfficialLexthor/Norid-CLI.git
cd Norid-CLI
pip install -r requirements.txt
```

### Krav

- Python 3.9 eller nyere
- Internettilgang
- Tkinter (for GUI-versjonen)

## Bruk

### Sjekk om domene er ledig (DAS)

```bash
norid das example.no
```

Output:
```
✓ example.no er LEDIG
```
eller
```
✗ norid.no er OPPTATT
```

### RDAP-oppslag på domene

```bash
norid domain norid.no
```

Output:
```
============================================================
  Domene: norid.no
============================================================

  Registrert: 1999-11-14
  Sist endret: 2025-11-15

  Navneservere:
    - y.nic.no
    - z.nic.no
    - auth03.svg.ns.norid.no
    - auth01.trd.ns.norid.no
    - auth02.osl.ns.norid.no

  Registrar: reg1103-NORID
    Navn: SIKT - KUNNSKAPSSEKTORENS TJENESTELEVERANDØR
```

### JSON-output for scripting

```bash
norid domain norid.no --json
```

### Oppslag i testmiljø

```bash
norid domain draupne.no --test
# eller
norid -t domain draupne.no
```

### Entitet (kontakt/registrar)

```bash
norid entity reg1-NORID          # Registrar
norid entity reg1103-NORID       # Registrar
```

Output:
```
============================================================
  Entitet: reg1-NORID
============================================================

  Navn: Norid
  Sted: Trondheim, NORWAY
  Telefon: tel:+47.73557355
  E-post: info@norid.no
  Registrert: 2010-10-01
  Sist endret: 2025-12-29
```

### Navneserver

```bash
norid nameserver X11H-NORID
```

### Søk etter navneservere

```bash
norid search nameservers "*.nic.no"
norid search nameservers x.nic.no
```

Output:
```
Fant 1 navneserver(e):

Handle      Navn      IPv4    IPv6
----------  --------  ------  ------
X11H-NORID  x.nic.no
```

### Tradisjonelt whois-oppslag

```bash
norid whois norid.no
```

## Alle kommandoer

| Kommando | Beskrivelse |
|----------|-------------|
| `norid das <domene>` | Sjekk om domene er ledig |
| `norid domain <domene>` | RDAP-oppslag på domene |
| `norid domain <domene> --available` | Sjekk om domene eksisterer (HEAD) |
| `norid domain <domene> --json` | Vis domenedata som JSON |
| `norid entity <handle>` | Oppslag på kontakt/registrar |
| `norid nameserver <handle>` | Oppslag på navneserver |
| `norid search nameservers <mønster>` | Søk etter navneservere |
| `norid whois <domene>` | Tradisjonelt whois-oppslag |

## Globale alternativer

| Alternativ | Beskrivelse |
|------------|-------------|
| `--test`, `-t` | Bruk testmiljø |
| `--json` | Output som JSON |
| `--help` | Vis hjelp |
| `--version` | Vis versjon |

## Tjenester og endepunkter

| Tjeneste | Produksjon | Test |
|----------|------------|------|
| RDAP | rdap.norid.no | rdap.test.norid.no |
| Whois | whois.norid.no:43 | whois.test.norid.no:43 |
| DAS | finger.norid.no:79 | finger.test.norid.no:79 |

## Rate-limiting

RDAP-tjenesten har følgende begrensninger per IP-adresse:

- Maks 300 GET-forespørsler per 24 timer
- Maks 3000 HEAD-forespørsler per 24 timer
- Maks 10 forespørsler per minutt

Ved overskridelse returneres HTTP 429 (Too Many Requests).

## Avanserte eksempler

<details>
<summary><strong>Batch-sjekk av domener</strong></summary>

```bash
for domain in example1.no example2.no example3.no; do
    norid das $domain
done
```

</details>

<details>
<summary><strong>Eksporter domeneinfo som JSON</strong></summary>

```bash
norid domain norid.no --json > norid-info.json
```

</details>

<details>
<summary><strong>Hent navneservere med jq</strong></summary>

```bash
norid domain norid.no --json | jq '.nameservers[].ldhName'
```

</details>

<details>
<summary><strong>Sjekk om domene eksisterer (HEAD-request)</strong></summary>

```bash
norid domain example.no --available
```

Dette bruker HEAD-request som teller mindre mot rate-limiting.

</details>

## Feilsøking

| Problem | Løsning |
|---------|---------|
| Rate-limit overskredet | Vent noen minutter eller bruk `--available` (HEAD-requests) |
| Timeout | Sjekk nettverkstilkobling |
| Domene ikke funnet | Verifiser at domenet er under .no |
| Entitet ikke funnet | Kun offentlige roller kan slås opp uten autentisering |

## Referanser

- [Norid RDAP-dokumentasjon](https://teknisk.norid.no/en/integrere-mot-norid/rdap/)
- [Norid Whois/DAS-dokumentasjon](https://teknisk.norid.no/en/integrere-mot-norid/whois/)
- [RDAP RFC 9082](https://tools.ietf.org/html/rfc9082)
- [RDAP RFC 9083](https://tools.ietf.org/html/rfc9083)

## Ansvarsfraskrivelse

> **Warning**  
> Dette er et **uoffisielt** prosjekt og er ikke tilknyttet Norid AS.  
> Prosjektet bruker Norid sine offentlige tjenester.

## Lisens

Distribuert under MIT-lisensen. Se [`LICENSE`](LICENSE) for mer informasjon.

---

<div align="center">

**[Norid](https://www.norid.no)** • **[Teknisk dokumentasjon](https://teknisk.norid.no)**

Utviklet av [Martin Clausen](https://github.com/OfficialLexthor)

</div>
