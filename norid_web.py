#!/usr/bin/env python3
"""
Norid Web GUI - Webbasert grensesnitt for Norid sine offentlige tjenester

Kjør med: python norid_web.py
Åpne: http://localhost:5000

Tjenester:
  - RDAP: REST API for domenedata
  - DAS: Domain Availability Service  
  - Whois: Tradisjonelt domeneoppslag
"""

import json
import socket
from flask import Flask, render_template_string, jsonify, request
import requests

app = Flask(__name__)

# API-konfigurasjon
RDAP_BASE_URL = "https://rdap.norid.no"
RDAP_TEST_URL = "https://rdap.test.norid.no"
WHOIS_HOST = "whois.norid.no"
WHOIS_TEST_HOST = "whois.test.norid.no"
WHOIS_PORT = 43
DAS_HOST = "finger.norid.no"
DAS_TEST_HOST = "finger.test.norid.no"
DAS_PORT = 79


def rdap_request(endpoint: str, use_test: bool = False):
    """Utfør RDAP-forespørsel"""
    base_url = RDAP_TEST_URL if use_test else RDAP_BASE_URL
    url = f"{base_url}/{endpoint}"
    
    try:
        response = requests.get(url, timeout=30, headers={
            "Accept": "application/rdap+json, application/json",
            "User-Agent": "Norid-Web/1.0.0"
        })
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 404:
            return {"success": False, "error": "Ikke funnet"}
        elif response.status_code == 429:
            return {"success": False, "error": "Rate-limit overskredet"}
        else:
            return {"success": False, "error": f"Feil ({response.status_code})"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Kunne ikke koble til"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def socket_request(host: str, port: int, query: str):
    """Utfør socket-forespørsel"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((host, port))
            sock.sendall(f"{query}\r\n".encode("utf-8"))
            
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            
            return {"success": True, "data": response.decode("utf-8", errors="replace")}
    except socket.timeout:
        return {"success": False, "error": "Timeout"}
    except socket.error:
        return {"success": False, "error": "socket_error"}


def rdap_check_available(domain: str, use_test: bool = False):
    """Sjekk om domene er ledig via RDAP HEAD-request"""
    base_url = RDAP_TEST_URL if use_test else RDAP_BASE_URL
    url = f"{base_url}/domain/{domain}"
    
    try:
        response = requests.head(url, timeout=10, headers={
            "User-Agent": "Norid-Web/1.0.0"
        })
        
        if response.status_code == 200:
            return {"success": True, "data": "registered"}
        elif response.status_code == 404:
            return {"success": True, "data": "available"}
        else:
            return {"success": False, "error": f"Feil ({response.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Norid - Domeneoppslag for .no</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0a0a0f;
            --bg-card: #12121a;
            --bg-input: #1a1a24;
            --bg-hover: #22222e;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --primary-glow: rgba(59, 130, 246, 0.15);
            --success: #22c55e;
            --success-glow: rgba(34, 197, 94, 0.15);
            --error: #ef4444;
            --error-glow: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
            --text: #f1f5f9;
            --text-muted: #64748b;
            --text-dim: #475569;
            --border: #2d2d3a;
            --border-light: #3d3d4a;
            --accent: #818cf8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Subtle grid background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: -1;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }

        /* Header */
        header {
            text-align: center;
            margin-bottom: 3rem;
            padding-top: 2rem;
        }

        .logo {
            display: inline-flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }

        .logo h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .logo .tag {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--primary);
            background: var(--primary-glow);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        header p {
            color: var(--text-muted);
            font-size: 1rem;
        }

        /* Environment Toggle */
        .env-toggle {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
        }

        .env-btn {
            padding: 0.5rem 1rem;
            font-size: 0.813rem;
            font-weight: 500;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text-muted);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .env-btn:hover {
            background: var(--bg-hover);
            border-color: var(--border-light);
        }

        .env-btn.active {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 0.25rem;
            background: var(--bg-card);
            padding: 0.25rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border);
        }

        .tab {
            flex: 1;
            padding: 0.75rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-muted);
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab:hover {
            color: var(--text);
            background: var(--bg-hover);
        }

        .tab.active {
            background: var(--primary);
            color: white;
        }

        /* Tab Content */
        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .card-desc {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
        }

        /* Search Form */
        .search-form {
            display: flex;
            gap: 0.75rem;
        }

        .search-input {
            flex: 1;
            padding: 0.875rem 1rem;
            font-size: 1rem;
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            outline: none;
            transition: all 0.2s ease;
        }

        .search-input::placeholder {
            color: var(--text-dim);
        }

        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .search-btn {
            padding: 0.875rem 1.5rem;
            font-size: 0.938rem;
            font-weight: 600;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .search-btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .search-btn:active {
            transform: translateY(0);
        }

        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Options */
        .options {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }

        .option-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-muted);
            cursor: pointer;
        }

        .option-label input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
            cursor: pointer;
        }

        /* Radio buttons for nameserver */
        .radio-group {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
        }

        .radio-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-muted);
            cursor: pointer;
        }

        .radio-label input[type="radio"] {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
            cursor: pointer;
        }

        /* Result Box */
        .result-box {
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            margin-top: 1.5rem;
            min-height: 200px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            line-height: 1.7;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
        }

        .result-box.loading {
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
        }

        .result-box.loading::after {
            content: '';
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-left: 0.75rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* DAS Result Card */
        .das-result {
            text-align: center;
            padding: 3rem 2rem;
            margin-top: 1.5rem;
            border-radius: 12px;
            background: var(--bg-input);
            border: 2px solid var(--border);
            transition: all 0.3s ease;
        }

        .das-result.available {
            border-color: var(--success);
            background: var(--success-glow);
        }

        .das-result.taken {
            border-color: var(--error);
            background: var(--error-glow);
        }

        .das-result .icon {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .das-result.available .icon {
            color: var(--success);
        }

        .das-result.taken .icon {
            color: var(--error);
        }

        .das-result .domain {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .das-result .status {
            font-size: 1rem;
            color: var(--text-muted);
        }

        .das-result.available .status {
            color: var(--success);
        }

        .das-result.taken .status {
            color: var(--error);
        }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }

        .empty-state .icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* Error */
        .error {
            color: var(--error);
            padding: 1rem;
            background: var(--error-glow);
            border-radius: 8px;
            border: 1px solid var(--error);
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            border-top: 1px solid var(--border);
            color: var(--text-dim);
            font-size: 0.813rem;
        }

        footer a {
            color: var(--primary);
            text-decoration: none;
        }

        footer a:hover {
            text-decoration: underline;
        }

        /* Responsive */
        @media (max-width: 640px) {
            .container {
                padding: 1rem;
            }

            .logo h1 {
                font-size: 2rem;
            }

            .tabs {
                flex-wrap: wrap;
            }

            .tab {
                flex: 1 1 calc(50% - 0.25rem);
            }

            .search-form {
                flex-direction: column;
            }

            .search-btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <h1>Norid</h1>
                <span class="tag">CLI</span>
            </div>
            <p>Slå opp .no-domener uten autentisering</p>
            
            <div class="env-toggle">
                <button class="env-btn active" data-env="prod" onclick="setEnv('prod')">Produksjon</button>
                <button class="env-btn" data-env="test" onclick="setEnv('test')">Test</button>
            </div>
        </header>

        <main>
            <div class="tabs">
                <button class="tab active" data-tab="das">DAS</button>
                <button class="tab" data-tab="domain">Domene</button>
                <button class="tab" data-tab="entity">Entitet</button>
                <button class="tab" data-tab="nameserver">Navneserver</button>
                <button class="tab" data-tab="whois">Whois</button>
            </div>

            <!-- DAS Tab -->
            <div id="das" class="tab-content active">
                <div class="card">
                    <h2 class="card-title">Domain Availability Service</h2>
                    <p class="card-desc">Sjekk om et .no-domene er ledig for registrering</p>
                    
                    <form class="search-form" onsubmit="runDas(event)">
                        <input type="text" class="search-input" id="das-input" 
                               placeholder="domenenavn.no" autocomplete="off">
                        <button type="submit" class="search-btn" id="das-btn">Sjekk</button>
                    </form>
                </div>
                
                <div id="das-result" class="das-result" style="display: none;">
                    <div class="icon"></div>
                    <div class="domain"></div>
                    <div class="status"></div>
                </div>
            </div>

            <!-- Domain Tab -->
            <div id="domain" class="tab-content">
                <div class="card">
                    <h2 class="card-title">RDAP Domeneoppslag</h2>
                    <p class="card-desc">Hent detaljert informasjon om et .no-domene</p>
                    
                    <form class="search-form" onsubmit="runDomain(event)">
                        <input type="text" class="search-input" id="domain-input" 
                               placeholder="norid.no" autocomplete="off">
                        <button type="submit" class="search-btn" id="domain-btn">Slå opp</button>
                    </form>
                    
                    <div class="options">
                        <label class="option-label">
                            <input type="checkbox" id="domain-json">
                            Vis som JSON
                        </label>
                    </div>
                </div>
                
                <div id="domain-result" class="result-box">
                    <div class="empty-state">
                        <div class="icon">◎</div>
                        <p>Skriv inn et domenenavn for å se informasjon</p>
                    </div>
                </div>
            </div>

            <!-- Entity Tab -->
            <div id="entity" class="tab-content">
                <div class="card">
                    <h2 class="card-title">Entitetsoppslag</h2>
                    <p class="card-desc">Slå opp registrarer og kontaktpersoner</p>
                    
                    <form class="search-form" onsubmit="runEntity(event)">
                        <input type="text" class="search-input" id="entity-input" 
                               placeholder="reg1-NORID" autocomplete="off">
                        <button type="submit" class="search-btn" id="entity-btn">Slå opp</button>
                    </form>
                    
                    <div class="options">
                        <label class="option-label">
                            <input type="checkbox" id="entity-json">
                            Vis som JSON
                        </label>
                    </div>
                </div>
                
                <div id="entity-result" class="result-box">
                    <div class="empty-state">
                        <div class="icon">◎</div>
                        <p>Skriv inn en handle for å se informasjon</p>
                    </div>
                </div>
            </div>

            <!-- Nameserver Tab -->
            <div id="nameserver" class="tab-content">
                <div class="card">
                    <h2 class="card-title">Navneserveroppslag</h2>
                    <p class="card-desc">Slå opp eller søk etter navneservere</p>
                    
                    <div class="radio-group">
                        <label class="radio-label">
                            <input type="radio" name="ns-mode" value="handle" checked>
                            Oppslag via handle
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="ns-mode" value="search">
                            Søk via hostname
                        </label>
                    </div>
                    
                    <form class="search-form" onsubmit="runNameserver(event)">
                        <input type="text" class="search-input" id="ns-input" 
                               placeholder="X11H-NORID eller *.nic.no" autocomplete="off">
                        <button type="submit" class="search-btn" id="ns-btn">Søk</button>
                    </form>
                    
                    <div class="options">
                        <label class="option-label">
                            <input type="checkbox" id="ns-json">
                            Vis som JSON
                        </label>
                    </div>
                </div>
                
                <div id="ns-result" class="result-box">
                    <div class="empty-state">
                        <div class="icon">◎</div>
                        <p>Skriv inn en handle eller hostname</p>
                    </div>
                </div>
            </div>

            <!-- Whois Tab -->
            <div id="whois" class="tab-content">
                <div class="card">
                    <h2 class="card-title">Whois-oppslag</h2>
                    <p class="card-desc">Tradisjonelt whois-oppslag for .no-domener</p>
                    
                    <form class="search-form" onsubmit="runWhois(event)">
                        <input type="text" class="search-input" id="whois-input" 
                               placeholder="norid.no" autocomplete="off">
                        <button type="submit" class="search-btn" id="whois-btn">Slå opp</button>
                    </form>
                </div>
                
                <div id="whois-result" class="result-box">
                    <div class="empty-state">
                        <div class="icon">◎</div>
                        <p>Skriv inn et domenenavn</p>
                    </div>
                </div>
            </div>
        </main>

        <footer>
            <p>
                <a href="https://github.com/OfficialLexthor/Norid-CLI" target="_blank">GitHub</a> · 
                <a href="https://teknisk.norid.no" target="_blank">Norid Teknisk</a> · 
                Utviklet av Martin Clausen
            </p>
        </footer>
    </div>

    <script>
        let currentEnv = 'prod';

        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            });
        });

        // Environment toggle
        function setEnv(env) {
            currentEnv = env;
            document.querySelectorAll('.env-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.env === env);
            });
        }

        // API calls
        async function apiCall(endpoint, params = {}) {
            params.env = currentEnv;
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`/api/${endpoint}?${query}`);
            return response.json();
        }

        // DAS
        async function runDas(e) {
            e.preventDefault();
            let domain = document.getElementById('das-input').value.trim();
            if (!domain) return;
            
            if (!domain.endsWith('.no')) domain += '.no';
            document.getElementById('das-input').value = domain;
            
            const btn = document.getElementById('das-btn');
            const result = document.getElementById('das-result');
            
            btn.disabled = true;
            btn.textContent = '...';
            result.style.display = 'none';
            
            try {
                const data = await apiCall('das', { domain });
                
                result.style.display = 'block';
                result.querySelector('.domain').textContent = domain;
                
                if (data.success) {
                    const text = data.data.toLowerCase();
                    const isAvailable = (text.includes('available') && !text.includes('not available')) 
                                     || text.includes('not registered');
                    
                    if (isAvailable) {
                        result.className = 'das-result available';
                        result.querySelector('.icon').textContent = '✓';
                        result.querySelector('.status').textContent = 'Dette domenet er LEDIG';
                    } else {
                        result.className = 'das-result taken';
                        result.querySelector('.icon').textContent = '✗';
                        result.querySelector('.status').textContent = 'Dette domenet er OPPTATT';
                    }
                } else {
                    result.className = 'das-result taken';
                    result.querySelector('.icon').textContent = '!';
                    result.querySelector('.status').textContent = data.error;
                }
            } catch (err) {
                result.style.display = 'block';
                result.className = 'das-result taken';
                result.querySelector('.icon').textContent = '!';
                result.querySelector('.domain').textContent = 'Feil';
                result.querySelector('.status').textContent = err.message;
            }
            
            btn.disabled = false;
            btn.textContent = 'Sjekk';
        }

        // Domain
        async function runDomain(e) {
            e.preventDefault();
            const domain = document.getElementById('domain-input').value.trim();
            if (!domain) return;
            
            const btn = document.getElementById('domain-btn');
            const result = document.getElementById('domain-result');
            const showJson = document.getElementById('domain-json').checked;
            
            btn.disabled = true;
            btn.textContent = '...';
            result.innerHTML = '';
            result.classList.add('loading');
            
            try {
                const data = await apiCall('domain', { domain });
                result.classList.remove('loading');
                
                if (data.success) {
                    result.textContent = showJson 
                        ? JSON.stringify(data.data, null, 2)
                        : formatDomain(data.data);
                } else {
                    result.innerHTML = `<div class="error">${data.error}</div>`;
                }
            } catch (err) {
                result.classList.remove('loading');
                result.innerHTML = `<div class="error">${err.message}</div>`;
            }
            
            btn.disabled = false;
            btn.textContent = 'Slå opp';
        }

        function formatDomain(data) {
            let lines = [];
            const name = data.ldhName || data.unicodeName || 'Ukjent';
            
            lines.push('─'.repeat(56));
            lines.push(`  DOMENE: ${name}`);
            lines.push('─'.repeat(56));
            lines.push('');
            
            if (data.status) {
                lines.push(`  Status      │ ${data.status.join(', ')}`);
            }
            
            (data.events || []).forEach(e => {
                const date = e.eventDate ? e.eventDate.slice(0, 10) : '';
                if (e.eventAction === 'registration') lines.push(`  Registrert  │ ${date}`);
                if (e.eventAction === 'last changed') lines.push(`  Sist endret │ ${date}`);
                if (e.eventAction === 'expiration') lines.push(`  Utløper     │ ${date}`);
            });
            
            if (data.nameservers && data.nameservers.length) {
                lines.push('');
                lines.push('  NAVNESERVERE');
                lines.push('  ' + '─'.repeat(40));
                data.nameservers.forEach(ns => {
                    lines.push(`    • ${ns.ldhName || ''}`);
                });
            }
            
            (data.entities || []).forEach(entity => {
                if (entity.roles && entity.roles.includes('registrar')) {
                    lines.push('');
                    lines.push('  REGISTRAR');
                    lines.push('  ' + '─'.repeat(40));
                    lines.push(`    Handle: ${entity.handle || ''}`);
                    
                    if (entity.vcardArray && entity.vcardArray[1]) {
                        entity.vcardArray[1].forEach(item => {
                            if (item[0] === 'fn') lines.push(`    Navn:   ${item[3]}`);
                        });
                    }
                }
            });
            
            return lines.join('\\n');
        }

        // Entity
        async function runEntity(e) {
            e.preventDefault();
            const handle = document.getElementById('entity-input').value.trim();
            if (!handle) return;
            
            const btn = document.getElementById('entity-btn');
            const result = document.getElementById('entity-result');
            const showJson = document.getElementById('entity-json').checked;
            
            btn.disabled = true;
            btn.textContent = '...';
            result.innerHTML = '';
            result.classList.add('loading');
            
            try {
                const data = await apiCall('entity', { handle });
                result.classList.remove('loading');
                
                if (data.success) {
                    result.textContent = showJson 
                        ? JSON.stringify(data.data, null, 2)
                        : formatEntity(data.data);
                } else {
                    result.innerHTML = `<div class="error">${data.error}</div>`;
                }
            } catch (err) {
                result.classList.remove('loading');
                result.innerHTML = `<div class="error">${err.message}</div>`;
            }
            
            btn.disabled = false;
            btn.textContent = 'Slå opp';
        }

        function formatEntity(data) {
            let lines = [];
            
            lines.push('─'.repeat(56));
            lines.push(`  ENTITET: ${data.handle || 'Ukjent'}`);
            lines.push('─'.repeat(56));
            lines.push('');
            
            if (data.roles) lines.push(`  Roller      │ ${data.roles.join(', ')}`);
            if (data.status) lines.push(`  Status      │ ${data.status.join(', ')}`);
            
            if (data.vcardArray && data.vcardArray[1]) {
                lines.push('');
                lines.push('  KONTAKTINFO');
                lines.push('  ' + '─'.repeat(40));
                
                data.vcardArray[1].forEach(item => {
                    if (item[0] === 'fn') lines.push(`    Navn:     ${item[3]}`);
                    if (item[0] === 'org') lines.push(`    Org:      ${item[3]}`);
                    if (item[0] === 'email') lines.push(`    E-post:   ${item[3]}`);
                    if (item[0] === 'tel') lines.push(`    Telefon:  ${item[3]}`);
                    if (item[0] === 'adr' && Array.isArray(item[3])) {
                        const city = item[3][3] || '';
                        const country = item[3][6] || '';
                        if (city || country) lines.push(`    Sted:     ${city}, ${country}`);
                    }
                });
            }
            
            return lines.join('\\n');
        }

        // Nameserver
        async function runNameserver(e) {
            e.preventDefault();
            const query = document.getElementById('ns-input').value.trim();
            if (!query) return;
            
            const mode = document.querySelector('input[name="ns-mode"]:checked').value;
            const btn = document.getElementById('ns-btn');
            const result = document.getElementById('ns-result');
            const showJson = document.getElementById('ns-json').checked;
            
            btn.disabled = true;
            btn.textContent = '...';
            result.innerHTML = '';
            result.classList.add('loading');
            
            try {
                const endpoint = mode === 'handle' ? 'nameserver' : 'nameserver_search';
                const data = await apiCall(endpoint, { query });
                result.classList.remove('loading');
                
                if (data.success) {
                    if (showJson) {
                        result.textContent = JSON.stringify(data.data, null, 2);
                    } else {
                        result.textContent = mode === 'handle' 
                            ? formatNameserver(data.data)
                            : formatNsSearch(data.data);
                    }
                } else {
                    result.innerHTML = `<div class="error">${data.error}</div>`;
                }
            } catch (err) {
                result.classList.remove('loading');
                result.innerHTML = `<div class="error">${err.message}</div>`;
            }
            
            btn.disabled = false;
            btn.textContent = 'Søk';
        }

        function formatNameserver(data) {
            let lines = [];
            
            lines.push('─'.repeat(56));
            lines.push(`  NAVNESERVER: ${data.ldhName || 'Ukjent'}`);
            lines.push('─'.repeat(56));
            lines.push('');
            lines.push(`  Handle      │ ${data.handle || ''}`);
            if (data.status) lines.push(`  Status      │ ${data.status.join(', ')}`);
            
            const ips = data.ipAddresses || {};
            if (ips.v4 && ips.v4.length) {
                lines.push('');
                lines.push('  IPv4');
                lines.push('  ' + '─'.repeat(40));
                ips.v4.forEach(ip => lines.push(`    • ${ip}`));
            }
            if (ips.v6 && ips.v6.length) {
                lines.push('');
                lines.push('  IPv6');
                lines.push('  ' + '─'.repeat(40));
                ips.v6.forEach(ip => lines.push(`    • ${ip}`));
            }
            
            return lines.join('\\n');
        }

        function formatNsSearch(data) {
            const results = data.nameserverSearchResults || [];
            if (!results.length) return 'Ingen navneservere funnet.';
            
            let lines = [`Fant ${results.length} navneserver(e)`, ''];
            lines.push('  HANDLE           NAVN                          IPv4');
            lines.push('  ' + '─'.repeat(54));
            
            results.forEach(ns => {
                const handle = (ns.handle || '').padEnd(16).slice(0, 16);
                const name = (ns.ldhName || '').padEnd(28).slice(0, 28);
                const ips = ns.ipAddresses || {};
                const v4 = (ips.v4 || []).join(', ').slice(0, 20);
                lines.push(`  ${handle} ${name} ${v4}`);
            });
            
            return lines.join('\\n');
        }

        // Whois
        async function runWhois(e) {
            e.preventDefault();
            const domain = document.getElementById('whois-input').value.trim();
            if (!domain) return;
            
            const btn = document.getElementById('whois-btn');
            const result = document.getElementById('whois-result');
            
            btn.disabled = true;
            btn.textContent = '...';
            result.innerHTML = '';
            result.classList.add('loading');
            
            try {
                const data = await apiCall('whois', { domain });
                result.classList.remove('loading');
                
                if (data.success) {
                    result.textContent = data.data;
                } else {
                    result.innerHTML = `<div class="error">${data.error}</div>`;
                }
            } catch (err) {
                result.classList.remove('loading');
                result.innerHTML = `<div class="error">${err.message}</div>`;
            }
            
            btn.disabled = false;
            btn.textContent = 'Slå opp';
        }

        // Enter key support
        document.querySelectorAll('.search-input').forEach(input => {
            input.addEventListener('keypress', e => {
                if (e.key === 'Enter') {
                    e.target.closest('form').dispatchEvent(new Event('submit'));
                }
            });
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/das')
def api_das():
    domain = request.args.get('domain', '')
    env = request.args.get('env', 'prod')
    
    if not domain:
        return jsonify({"success": False, "error": "Mangler domene"})
    
    # Prøv socket først, fallback til RDAP
    host = DAS_TEST_HOST if env == 'test' else DAS_HOST
    result = socket_request(host, DAS_PORT, domain)
    
    if not result["success"] and result.get("error") == "socket_error":
        # Fallback til RDAP HEAD-request
        rdap_result = rdap_check_available(domain, env == 'test')
        return jsonify(rdap_result)
    
    return jsonify(result)


@app.route('/api/domain')
def api_domain():
    domain = request.args.get('domain', '')
    env = request.args.get('env', 'prod')
    
    if not domain:
        return jsonify({"success": False, "error": "Mangler domene"})
    
    return jsonify(rdap_request(f"domain/{domain}", env == 'test'))


@app.route('/api/entity')
def api_entity():
    handle = request.args.get('handle', '')
    env = request.args.get('env', 'prod')
    
    if not handle:
        return jsonify({"success": False, "error": "Mangler handle"})
    
    return jsonify(rdap_request(f"entity/{handle}", env == 'test'))


@app.route('/api/nameserver')
def api_nameserver():
    query = request.args.get('query', '')
    env = request.args.get('env', 'prod')
    
    if not query:
        return jsonify({"success": False, "error": "Mangler query"})
    
    return jsonify(rdap_request(f"nameserver_handle/{query}", env == 'test'))


@app.route('/api/nameserver_search')
def api_nameserver_search():
    query = request.args.get('query', '')
    env = request.args.get('env', 'prod')
    
    if not query:
        return jsonify({"success": False, "error": "Mangler query"})
    
    return jsonify(rdap_request(f"nameservers?name={query}", env == 'test'))


@app.route('/api/whois')
def api_whois():
    domain = request.args.get('domain', '')
    env = request.args.get('env', 'prod')
    
    if not domain:
        return jsonify({"success": False, "error": "Mangler domene"})
    
    # Prøv socket først, fallback til RDAP
    host = WHOIS_TEST_HOST if env == 'test' else WHOIS_HOST
    result = socket_request(host, WHOIS_PORT, domain)
    
    if not result["success"] and result.get("error") == "socket_error":
        # Fallback til RDAP og formater som whois-lignende output
        rdap_result = rdap_request(f"domain/{domain}", env == 'test')
        if rdap_result["success"]:
            data = rdap_result["data"]
            lines = []
            lines.append(f"Domain Name: {data.get('ldhName', domain)}")
            
            for event in data.get('events', []):
                if event.get('eventAction') == 'registration':
                    lines.append(f"Created: {event.get('eventDate', '')[:10]}")
                elif event.get('eventAction') == 'last changed':
                    lines.append(f"Updated: {event.get('eventDate', '')[:10]}")
            
            if data.get('status'):
                lines.append(f"Status: {', '.join(data['status'])}")
            
            for ns in data.get('nameservers', []):
                lines.append(f"Name Server: {ns.get('ldhName', '')}")
            
            for entity in data.get('entities', []):
                if 'registrar' in entity.get('roles', []):
                    lines.append(f"Registrar: {entity.get('handle', '')}")
            
            return jsonify({"success": True, "data": "\n".join(lines)})
        return jsonify(rdap_result)
    
    return jsonify(result)


def main():
    """Start web-serveren"""
    print("\n" + "="*50)
    print("  Norid Web GUI")
    print("  http://localhost:8080")
    print("="*50 + "\n")
    app.run(debug=True, port=8080)


if __name__ == '__main__':
    main()
