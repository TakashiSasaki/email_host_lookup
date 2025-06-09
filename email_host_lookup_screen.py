# email_host_lookup_screen.py
# Provides EmailHostLookupScreen for use in Textual apps and also runs as a standalone TUI if executed directly.

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from textual.screen import Screen

_instance: Optional["Screen"] = None

def get_email_host_lookup_screen() -> Optional["Screen"]:
    """
    Factory function to get the singleton EmailHostLookupScreen.

    Returns:
        EmailHostLookupScreen if Textual is installed and available,
        otherwise None.
    """
    global _instance
    try:
        from textual.screen import Screen
        from textual.widgets import Input, Button, Static, TextLog
        from textual.containers import Vertical
        import asyncio
        import dns.resolver

        class EmailHostLookupScreen(Screen):
            """Screen to input an email address and display its hosting provider."""

            BINDINGS = [("q", "app.quit", "Quit")]

            def compose(self):
                yield Vertical(
                    Static("Enter an email address to lookup its mail host:", id="prompt"),
                    Input(placeholder="user@example.com", id="email_input"),
                    Button("Lookup", id="lookup_button"),
                    TextLog(highlight=True, id="output_log", max_lines=20)
                )

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "lookup_button":
                    email_input = self.query_one("#email_input", Input).value
                    self.set_focus(None)
                    asyncio.create_task(self.lookup_and_display(email_input))

            async def lookup_and_display(self, email: str) -> None:
                output = self.query_one("#output_log", TextLog)
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

                provider = detect_provider(mx_hosts)
                output.write(f"[cyan]Likely mail provider:[/cyan] {provider}")

        def detect_provider(mx_hosts: list[str]) -> str:
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

        if _instance is None:
            _instance = EmailHostLookupScreen()
        return _instance
    except ImportError:
        # Textual or dependencies not installed
        return None

# ==== 単体起動用メインエントリポイント ====
if __name__ == "__main__":
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Header, Footer

        class EmailHostLookupApp(App):
            """Standalone TUI app for email host lookup."""

            CSS = """
            #prompt { margin-bottom: 1; }
            #output_log { height: 7; }
            """

            def compose(self) -> ComposeResult:
                yield Header()
                screen = get_email_host_lookup_screen()
                if screen is not None:
                    yield screen
                else:
                    from textual.widgets import Static
                    yield Static(
                        "Textual or required modules not installed.\n\nInstall with: pip install textual dnspython",
                        id="error_message"
                    )
                yield Footer()

        EmailHostLookupApp().run()
    except ImportError as e:
        print("This script requires Textual and dnspython.\nInstall them with:\n  pip install textual dnspython")
        print("Error:", e)
