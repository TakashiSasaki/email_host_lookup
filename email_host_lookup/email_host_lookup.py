import dns.resolver
import sys
import asyncio # Required for async dns.resolver
from typing import List, Tuple # For type hinting

async def get_mx_records(domain: str) -> List[str]:
    """
    Fetches MX records for a given domain.
    Returns a list of MX host strings, sorted by preference (implicitly by resolver).
    Raises an exception if resolution fails.
    """
    try:
        answers = await dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted(str(r.exchange).rstrip('.') for r in answers)
        return mx_hosts
    except Exception as e:
        # Re-raise or handle as appropriate for CLI/library use
        raise Exception(f"Failed to resolve MX records for {domain}: {e}")

def detect_provider(mx_hosts: List[str]) -> str:
    """Detects the email provider from a list of MX host strings."""
    for host in mx_hosts:
        if "google.com" in host or "googlemail.com" in host: # Added googlemail.com for completeness
            return "Google Workspace"
        elif "outlook.com" in host or "protection.outlook.com" in host:
            return "Microsoft 365"
        elif "yahoodns.net" in host: # This might be too broad, but keeping as is for now
            return "Yahoo Mail"
        elif "zoho.com" in host:
            return "Zoho Mail"
        elif "protonmail" in host or "proton.ch" in host: # Added proton.ch
            return "ProtonMail"
        elif "fastmail" in host or "messagingengine.com" in host: # Added fastmail's underlying domain
            return "Fastmail"
        # Add more specific provider checks as needed
    return "Unknown or Custom Provider"

async def get_email_host_info(domain: str) -> Tuple[str, List[str], str]:
    """
    Orchestrates fetching MX records and detecting the email provider for a domain.
    Returns a tuple: (domain, mx_records, provider_name).
    """
    mx_records = await get_mx_records(domain)
    provider = detect_provider(mx_records)
    return domain, mx_records, provider

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m email_host_lookup.email_host_lookup <domain>")
        sys.exit(1)

    domain_to_lookup = sys.argv[1]

    # Basic validation for domain format (very simple)
    if "." not in domain_to_lookup or domain_to_lookup.startswith(".") or domain_to_lookup.endswith("."):
        print(f"Invalid domain format: {domain_to_lookup}")
        sys.exit(1)

    print(f"Looking up email hosting information for: {domain_to_lookup}...")

    try:
        # asyncio.run is suitable for simple script execution
        resolved_domain, mx_records_list, provider_name = asyncio.run(get_email_host_info(domain_to_lookup))

        print(f"\nDomain: {resolved_domain}")
        print(f"Likely Mail Provider: {provider_name}")
        if mx_records_list:
            print("MX Records:")
            for record in mx_records_list:
                print(f"  - {record}")
        else:
            print("No MX Records found.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
