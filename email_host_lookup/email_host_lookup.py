#!/usr/bin/env python3
"""
email_host_lookup.py
A CLI tool to detect an email hosting provider via multiple DNS and HTTP-based methods.
"""

import dns.resolver
import sys
import ssl
import urllib.request
from typing import List, Tuple


def get_mx_records(domain: str) -> List[str]:
    """Fetch MX records for the given domain."""
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return sorted(str(r.exchange).rstrip('.') for r in answers)
    except Exception as e:
        raise Exception(f"Failed to resolve MX records for {domain}: {e}")


def detect_provider(mx_hosts: List[str]) -> str:
    """Detect provider based on MX hostnames."""
    for host in mx_hosts:
        if "google.com" in host or "googlemail.com" in host:
            return "Google Workspace"
        elif "outlook.com" in host or "protection.outlook.com" in host:
            return "Microsoft 365"
        elif "yahoodns.net" in host:
            return "Yahoo Mail"
        elif "zoho.com" in host:
            return "Zoho Mail"
        elif "protonmail" in host or "proton.ch" in host:
            return "ProtonMail"
        elif "fastmail" in host or "messagingengine.com" in host:
            return "Fastmail"
    return "Unknown or Custom Provider"


def get_spf_record(domain: str) -> List[str]:
    """Fetch SPF (TXT) records for the given domain."""
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        spf_records: List[str] = []
        for r in answers:
            txt = b"".join(r.strings).decode("utf-8") if hasattr(r, "strings") else str(r)
            if txt.startswith("v=spf1"):
                spf_records.append(txt)
        return spf_records
    except Exception as e:
        return [f"Error: {e}"]


def detect_provider_by_spf(spf_records: List[str]) -> str:
    """Detect provider by analyzing SPF record contents."""
    for txt in spf_records:
        if "include:_spf.google.com" in txt:
            return "Google Workspace (SPF)"
        elif "include:spf.protection.outlook.com" in txt:
            return "Microsoft 365 (SPF)"
        elif "include:zoho.com" in txt:
            return "Zoho Mail (SPF)"
        elif "include:spf.mail.yahoo.com" in txt:
            return "Yahoo Mail (SPF)"
        elif "include:_spf.protonmail.ch" in txt:
            return "ProtonMail (SPF)"
        elif "include:spf.messagingengine.com" in txt:
            return "Fastmail (SPF)"
    return "Unknown or Custom Provider (SPF)"


def get_dmarc_record(domain: str) -> List[str]:
    """Fetch DMARC (TXT) records for the given domain."""
    try:
        dmarc_domain = f"_dmarc.{domain}"
        answers = dns.resolver.resolve(dmarc_domain, "TXT")
        dmarc_records: List[str] = []
        for r in answers:
            txt = b"".join(r.strings).decode("utf-8") if hasattr(r, "strings") else str(r)
            dmarc_records.append(txt)
        return dmarc_records
    except Exception as e:
        return [f"Error: {e}"]


def detect_provider_by_dmarc(dmarc_records: List[str]) -> str:
    """Detect provider by analyzing DMARC record contents."""
    for txt in dmarc_records:
        if "google.com" in txt:
            return "Google Workspace (DMARC)"
        elif "outlook.com" in txt:
            return "Microsoft 365 (DMARC)"
        elif "zoho.com" in txt:
            return "Zoho Mail (DMARC)"
        elif "yahoo.com" in txt:
            return "Yahoo Mail (DMARC)"
        elif "protonmail" in txt:
            return "ProtonMail (DMARC)"
        elif "fastmail" in txt:
            return "Fastmail (DMARC)"
    return "Unknown or Custom Provider (DMARC)"


def detect_provider_by_autoconfig(domain: str) -> str:
    """
    Try Mozilla Autoconfig or Microsoft Autodiscover endpoints.
    Returns a provider hint or status if none respond.
    """
    urls = [
        f"https://autoconfig.{domain}/mail/config-v1.1.xml",
        f"https://{domain}/.well-known/autoconfig/mail/config-v1.1.xml",
        f"https://autodiscover.{domain}/autodiscover/autodiscover.xml",
    ]
    ctx = ssl.create_default_context()
    for url in urls:
        try:
            with urllib.request.urlopen(url, context=ctx, timeout=5) as resp:
                content = resp.read(4096).decode("utf-8", errors="ignore").lower()
                if "google.com" in content:
                    return f"Google Workspace (autoconfig: {url})"
                elif "outlook.com" in content or "office365.com" in content:
                    return f"Microsoft 365 (autodiscover: {url})"
                elif "zoho.com" in content:
                    return f"Zoho Mail (autoconfig: {url})"
                elif "fastmail.com" in content or "messagingengine.com" in content:
                    return f"Fastmail (autoconfig: {url})"
                elif "protonmail" in content or "proton.ch" in content:
                    return f"ProtonMail (autoconfig: {url})"
                else:
                    return f"Autoconfig present but provider unknown: {url}"
        except Exception:
            continue
    return "No response from autoconfig/autodiscover endpoints"


def detect_provider_by_srv(domain: str) -> str:
    """
    Check common mail-related SRV records for service discovery.
    """
    srv_names = [
        f"_autodiscover._tcp.{domain}",
        f"_imaps._tcp.{domain}",
        f"_submission._tcp.{domain}",
    ]
    found: List[str] = []
    for srv in srv_names:
        try:
            answers = dns.resolver.resolve(srv, "SRV")
            for r in answers:
                target = str(r.target).rstrip('.').lower()
                found.append(f"{srv} → {target}")
        except Exception:
            continue
    if not found:
        return "No mail-related SRV records found"
    # Heuristic based on discovered targets
    for entry in found:
        if "google.com" in entry:
            return f"Google Workspace (SRV: {entry})"
        elif "outlook.com" in entry or "office365.com" in entry:
            return f"Microsoft 365 (SRV: {entry})"
        elif "zoho.com" in entry:
            return f"Zoho Mail (SRV: {entry})"
    return "Mail-related SRV record(s) found, provider unknown:\n  " + "\n  ".join(found)


def detect_provider_by_webfinger(domain: str) -> str:
    """
    Attempt a WebFinger lookup to discover account metadata.
    """
    url = f"https://{domain}/.well-known/webfinger?resource=acct:user@{domain}"
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=5) as resp:
            content = resp.read(4096).decode("utf-8", errors="ignore").lower()
            if "google" in content:
                return "Google (WebFinger)"
            elif "microsoft" in content or "outlook" in content:
                return "Microsoft (WebFinger)"
            elif "zoho" in content:
                return "Zoho (WebFinger)"
            return "WebFinger present but provider unknown"
    except Exception as e:
        return f"No response from WebFinger endpoint: {e}"


def get_email_host_info(domain: str) -> Tuple[
    str,
    List[str],
    str,
    List[str],
    str,
    List[str],
    str
]:
    """
    Aggregate detection results from MX, SPF, DMARC methods.
    """
    mx_records = get_mx_records(domain)
    provider_mx = detect_provider(mx_records)

    spf_records = get_spf_record(domain)
    provider_spf = detect_provider_by_spf(spf_records)

    dmarc_records = get_dmarc_record(domain)
    provider_dmarc = detect_provider_by_dmarc(dmarc_records)

    return (
        domain,
        mx_records,
        provider_mx,
        spf_records,
        provider_spf,
        dmarc_records,
        provider_dmarc
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python email_host_lookup.py <email-address>")
        sys.exit(1)

    email_input = sys.argv[1]
    if "@" not in email_input or email_input.startswith("@") or email_input.endswith("@"):
        print(f"Invalid email address: {email_input}")
        sys.exit(1)

    domain_to_lookup = email_input.split("@")[-1]
    print(f"Looking up email hosting information for: {email_input} (domain: {domain_to_lookup})...")

    try:
        (
            resolved_domain,
            mx_records_list,
            provider_mx,
            spf_records_list,
            provider_spf,
            dmarc_records_list,
            provider_dmarc
        ) = get_email_host_info(domain_to_lookup)

        print(f"\nDomain: {resolved_domain}")

        print(f"\n[MX Record Based]\n  Likely Mail Provider: {provider_mx}")
        if mx_records_list:
            print("  MX Records:")
            for record in mx_records_list:
                print(f"    - {record}")
        else:
            print("  No MX Records found.")

        print(f"\n[SPF Record Based]\n  Likely Mail Provider: {provider_spf}")
        if spf_records_list:
            print("  SPF Records:")
            for record in spf_records_list:
                print(f"    - {record}")
        else:
            print("  No SPF Records found.")

        print(f"\n[DMARC Record Based]\n  Likely Mail Provider: {provider_dmarc}")
        if dmarc_records_list:
            print("  DMARC Records:")
            for record in dmarc_records_list:
                print(f"    - {record}")
        else:
            print("  No DMARC Records found.")

        print(f"\n[Autoconfig/Autodiscover Based]\n  {detect_provider_by_autoconfig(domain_to_lookup)}")
        print(f"\n[SRV Record Based]\n  {detect_provider_by_srv(domain_to_lookup)}")
        print(f"\n[WebFinger Based]\n  {detect_provider_by_webfinger(domain_to_lookup)}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
