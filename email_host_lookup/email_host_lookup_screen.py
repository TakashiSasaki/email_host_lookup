# email_host_lookup_screen.py
# Provides EmailHostLookupScreen for use in Textual apps and also runs as a standalone TUI if executed directly.

from typing import Optional, TYPE_CHECKING
import asyncio
import sys
from .email_host_lookup import get_email_host_info # Import the core logic

# Ensure all necessary imports for the screen are here at module level
from textual.screen import Screen
from textual.widgets import Input, Button, Static, RichLog # Reverted to RichLog
from textual.containers import Vertical # Added Vertical

if TYPE_CHECKING:
    pass # Screen was already imported above, TYPE_CHECKING block can be simplified or removed if not strictly needed for other types

_instance: Optional["EmailHostLookupScreen"] = None # Changed type hint

class EmailHostLookupScreen(Screen):
    """Screen to input an email address and display its hosting provider."""

    BINDINGS = [("ctrl+w", "app.quit", "Quit")] # Correct binding

    def compose(self): # Full original compose
        # Test write during compose
        output_log = RichLog(highlight=True, id="output_log", max_lines=20) # Reverted to RichLog
        # output_log.write("Compose time test message") # This might not work as expected if log isn't fully ready

        yield Vertical(
            Static("Enter an email address to lookup its mail host:", id="prompt"),
            Input(placeholder="user@example.com", id="email_input"),
            Button("Lookup", id="lookup_button"),
            output_log # use the instance
        )

    # def on_mount(self) -> None: # Removed test message
    #     # Test write after mount, RichLog should be ready
    #     # log = self.query_one(RichLog)
    #     # log.write("Mount time test message")


    async def on_button_pressed(self, event: Button.Pressed) -> None: # Make it async
        if event.button.id == "lookup_button":
            email_input = self.query_one("#email_input", Input).value
            self.set_focus(None) # Important original line
            await self.lookup_and_display(email_input) # Await the task
            # Add a small sleep *within the event handler* after the work is done.
            await asyncio.sleep(0.1)

    async def lookup_and_display(self, email: str) -> None: # Full original method
        output = self.query_one("#output_log", RichLog) # Reverted to RichLog
        output.clear()
        # output.write("LAD_AFTER_CLEAR") # DEBUG: Write *after* clear, before conditions - REMOVING for this revert.
        # The original debug write for LAD_AFTER_CLEAR should be removed if this is a full revert to previous state.
        # For now, keeping it to see if RichLog behaves differently after all.
        output.write("LAD_AFTER_CLEAR")


        if "@" not in email:
            output.write("[red]Invalid email address[/red]") # Reverted to RichLog formatting
            return

        domain = email.split("@")[-1]
        output.write(f"[bold]Looking up MX records for:[/bold] {domain}") # Reverted to RichLog formatting

        try:
            # Use the imported function from email_host_lookup.py
            _, mx_hosts, provider = await get_email_host_info(domain)
            output.write(f"[green]MX Records:[/green] {', '.join(mx_hosts)}") # Reverted to RichLog formatting
            output.write(f"[cyan]Likely mail provider:[/cyan] {provider}") # Reverted to RichLog formatting
        except Exception as e:
            output.write(f"[red]Failed to resolve: {e}[/red]") # Reverted to RichLog formatting
            return

# THIS IS THE CRUCIAL PART TO GET RIGHT - FULL ORIGINAL SCREEN LOGIC
def get_email_host_lookup_screen() -> Optional[EmailHostLookupScreen]: # Changed return type hint
    global _instance
    try:
        # Class EmailHostLookupScreen is now defined at module level
        if _instance is None:
            _instance = EmailHostLookupScreen()
        return _instance
    except ImportError: # Should primarily catch issues with textual itself if not installed
        # Textual or core dependencies not installed
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
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
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
