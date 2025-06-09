import dns.resolver
import sys
from typing import List, Tuple

def get_mx_records(domain: str) -> List[str]:
    """Fetches MX records for a given domain."""
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted(str(r.exchange).rstrip('.') for r in answers)
        return mx_hosts
    except Exception as e:
        raise Exception(f"Failed to resolve MX records for {domain}: {e}")

def detect_provider(mx_hosts: List[str]) -> str:
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
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        spf_records = []
        for r in answers:
            txt = b"".join(r.strings).decode("utf-8") if hasattr(r, "strings") else str(r)
            if txt.startswith("v=spf1"):
                spf_records.append(txt)
        return spf_records
    except Exception as e:
        return [f"Error: {e}"]

def detect_provider_by_spf(spf_records: List[str]) -> str:
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
    try:
        dmarc_domain = f"_dmarc.{domain}"
        answers = dns.resolver.resolve(dmarc_domain, "TXT")
        dmarc_records = []
        for r in answers:
            txt = b"".join(r.strings).decode("utf-8") if hasattr(r, "strings") else str(r)
            dmarc_records.append(txt)
        return dmarc_records
    except Exception as e:
        return [f"Error: {e}"]

def detect_provider_by_dmarc(dmarc_records: List[str]) -> str:
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

def get_email_host_info(domain: str) -> Tuple[str, List[str], str, List[str], str, List[str], str]:
    mx_records = get_mx_records(domain)
    provider_mx = detect_provider(mx_records)
    spf_records = get_spf_record(domain)
    provider_spf = detect_provider_by_spf(spf_records)
    dmarc_records = get_dmarc_record(domain)
    provider_dmarc = detect_provider_by_dmarc(dmarc_records)
    return (
        domain, mx_records, provider_mx,
        spf_records, provider_spf,
        dmarc_records, provider_dmarc
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
            resolved_domain, mx_records_list, provider_mx,
            spf_records_list, provider_spf,
            dmarc_records_list, provider_dmarc
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

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
