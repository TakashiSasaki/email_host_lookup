# email_host_lookup_screen.py
# Provides EmailHostLookupScreen for use in Textual apps and also runs as a standalone TUI if executed directly.

from typing import Optional, TYPE_CHECKING
import asyncio
import sys
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static # Added Static here
# Input, Button, RichLog will be imported inside get_email_host_lookup_screen for now.

if TYPE_CHECKING:
    from textual.screen import Screen

_instance: Optional["Screen"] = None

# THIS IS THE CRUCIAL PART TO GET RIGHT - FULL ORIGINAL SCREEN LOGIC
def get_email_host_lookup_screen() -> Optional["Screen"]:
    global _instance
    try:
        # Ensure all necessary imports for the screen are here
        from textual.screen import Screen
        # Static is now imported at module level
        from textual.widgets import Input, Button, RichLog
        from textual.containers import Vertical
        import dns.resolver # Crucial for the screen's functionality

        class EmailHostLookupScreen(Screen):
            """Screen to input an email address and display its hosting provider."""

            BINDINGS = [("ctrl+w", "app.quit", "Quit"), ("q", "app.quit", "Quit")] # Correct binding

            def compose(self): # Full original compose
                yield Vertical(
                    Static("Enter an email address to lookup its mail host:", id="prompt"),
                    Input(placeholder="user@example.com", id="email_input"),
                    Button("Lookup", id="lookup_button"),
                    RichLog(highlight=True, id="output_log", max_lines=20) # Changed TextLog to RichLog
                )

            def on_button_pressed(self, event: Button.Pressed) -> None: # Full original method
                if event.button.id == "lookup_button":
                    email_input = self.query_one("#email_input", Input).value
                    self.set_focus(None) # Important original line
                    asyncio.create_task(self.lookup_and_display(email_input))

            async def lookup_and_display(self, email: str) -> None: # Full original method
                output = self.query_one("#output_log", RichLog) # Changed TextLog to RichLog
                output.clear()

                if "@" not in email:
                    output.write("[red]Invalid email address[/red]")
                    return

                domain = email.split("@")[-1]
                output.write(f"[bold]Looking up MX records for:[/bold] {domain}")

                try:
                    answers = dns.resolver.resolve(domain, "MX")
                    mx_hosts = sorted(str(r.exchange).rstrip('.') for r in answers)
                    output.write(f"[green]MX Records:[/green] {', '.join(mx_hosts)}")
                except Exception as e:
                    output.write(f"[red]Failed to resolve MX records: {e}[/red]")
                    return

                provider = detect_provider(mx_hosts) # Uses detect_provider below
                output.write(f"[cyan]Likely mail provider:[/cyan] {provider}")

        if _instance is None: # Moved instantiation inside try
            _instance = EmailHostLookupScreen()
        return _instance # Moved return inside try
    except ImportError: # Correctly paired with the try block
        # Textual or dependencies not installed
        return None

def detect_provider(mx_hosts: list[str]) -> str: # Full original method
    """Detects the email provider from a list of MX host strings."""
    for host in mx_hosts:
        if "google.com" in host:
            return "Google Workspace"
        elif "outlook.com" in host or "protection.outlook.com" in host:
            return "Microsoft 365"
        elif "yahoodns.net" in host:
            return "Yahoo Mail"
        elif "zoho.com" in host:
            return "Zoho Mail"
        elif "protonmail" in host:
            return "ProtonMail"
        elif "fastmail" in host:
            return "Fastmail"
    return "Unknown or Custom Provider"


class EmailHostLookupApp(App):
    DEFAULT_BINDINGS = [] # Override to remove all default App bindings

    CSS = """
    #prompt { margin-bottom: 1; }
    #output_log { height: 7; }
    """
    def compose(self) -> ComposeResult:
        yield Header()
        screen = get_email_host_lookup_screen()
        if screen is not None: # This condition is important
            yield screen
        else: # This is what happens if get_email_host_lookup_screen() returns None
            # Static is imported at the module level
            yield Static(
                "Failed to create EmailHostLookupScreen. Check dependencies like 'dnspython'.",
                id="error_message" # This Static widget does not have "#prompt"
            )
        yield Footer()

    # def action_do_nothing(self) -> None: # No longer needed with DEFAULT_BINDINGS approach
    #     """Does nothing."""
    #     pass

# ==== Main entry point ====
if __name__ == "__main__":
    try:
        # EmailHostLookupApp is now defined at module level
        # Imports for App, ComposeResult, Header, Footer, Static are at module level
        EmailHostLookupApp().run()
    # ImportError for App, ComposeResult, Header, Footer, Static is now less likely here
    # as they are imported at the top. However, dns.resolver or other screen-specific
    # imports could still fail.
    except ImportError as e:
        print("This script requires Textual and dnspython.\nInstall them with:\n  pip install textual dnspython")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
