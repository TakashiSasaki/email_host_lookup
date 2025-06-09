# email_host_lookup_screen.py
# Provides EmailHostLookupScreen for use in Textual apps and also runs as a standalone TUI if executed directly.

from typing import Optional, TYPE_CHECKING
import asyncio
import sys

if TYPE_CHECKING:
    from textual.screen import Screen

_instance: Optional["Screen"] = None

# THIS IS THE CRUCIAL PART TO GET RIGHT - FULL ORIGINAL SCREEN LOGIC
def get_email_host_lookup_screen() -> Optional["Screen"]:
    global _instance
    try:
        # Ensure all necessary imports for the screen are here
        from textual.screen import Screen
        from textual.widgets import Input, Button, Static, RichLog
        from textual.containers import Vertical
        # import dns.resolver # No longer directly used here, moved to email_host_lookup.py
        from .email_host_lookup import get_email_host_info # Import the core logic

        class EmailHostLookupScreen(Screen):
            """Screen to input an email address and display its hosting provider."""

            BINDINGS = [("ctrl+w", "app.quit", "Quit")] # Correct binding

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
                    # Use the imported function from email_host_lookup.py
                    _, mx_hosts, provider = await get_email_host_info(domain)
                    output.write(f"[green]MX Records:[/green] {', '.join(mx_hosts)}")
                    output.write(f"[cyan]Likely mail provider:[/cyan] {provider}")
                except Exception as e:
                    output.write(f"[red]Failed to resolve: {e}[/red]") # Simplified error message
                    return

        if _instance is None:
            _instance = EmailHostLookupScreen()
        return _instance
    except ImportError:
        # Textual or dependencies not installed
        return None

# def detect_provider(mx_hosts: list[str]) -> str: # MOVED to email_host_lookup.py
#     """Detects the email provider from a list of MX host strings."""
#     for host in mx_hosts:
#         if "google.com" in host:
#             return "Google Workspace"
#         elif "outlook.com" in host or "protection.outlook.com" in host:
#             return "Microsoft 365"
#         elif "yahoodns.net" in host:
#             return "Yahoo Mail"
#         elif "zoho.com" in host:
#             return "Zoho Mail"
#         elif "protonmail" in host:
#             return "ProtonMail"
#         elif "fastmail" in host:
#             return "Fastmail"
#     return "Unknown or Custom Provider"

# The _run_key_binding_tests function has been removed as its functionality
# is covered by tests in tests/test_key_bindings.py, invoked via pytest.

# ==== Main entry point ====
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer # Added import

class EmailHostLookupApp(App): # Moved class definition
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
            from textual.widgets import Static
            yield Static(
                "Failed to create EmailHostLookupScreen. Check dependencies like 'dnspython'.",
                id="error_message" # This Static widget does not have "#prompt"
            )
        yield Footer()

if __name__ == "__main__":
    try:
        EmailHostLookupApp().run()
    except ImportError as e:
        # This error handling is important for users trying to run the app directly
        # without having installed dependencies.
        missing_deps = []
        if "textual" in str(e).lower():
            missing_deps.append("textual")
        if "dns" in str(e).lower(): # Catches dnspython
            missing_deps.append("dnspython")

        if missing_deps:
            print(f"This script requires: {', '.join(missing_deps)}.\nInstall them with:\n  pip install {' '.join(missing_deps)}")
        else:
            print("An import error occurred. Ensure all dependencies are installed.")
        print(f"Original error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while trying to run the EmailHostLookupApp: {e}")
        sys.exit(1)
