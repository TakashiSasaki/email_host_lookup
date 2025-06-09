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
        from textual.widgets import Input, Button, Static, RichLog # Changed TextLog to RichLog
        from textual.containers import Vertical
        import dns.resolver # Crucial for the screen's functionality

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



# ==== Standalone test runner code (from previous successful iteration for ctrl+w) ====
async def _run_key_binding_tests(app_class_to_test, log_func):
    from textual.pilot import Pilot

    results = {
        "q_does_not_quit": False,
        "ctrl_q_does_not_quit": False,
        "ctrl_w_quits": False,
    }
    log_func("Starting key binding tests...")

    # Test 'q'
    app_q = app_class_to_test()
    try:
        async with app_q.run_test(headless=True, size=(80, 24)) as pilot_q:
            await pilot_q.pause(0.2)
            log_func("  Testing 'q': Pressing 'q'. App should NOT quit.")
            await pilot_q.press("q")
            await pilot_q.pause(0.3)
            _ = pilot_q.app.query_one("#prompt") # Changed to app.query_one
            results["q_does_not_quit"] = True
            log_func("  'q' test: OK (app did not quit).")
    except Exception as e:
        log_func(f"  'q' test: FAILED. Error: {e}")
        results["q_does_not_quit"] = False

    # Test 'ctrl+q'
    app_ctrl_q = app_class_to_test()
    try:
        async with app_ctrl_q.run_test(headless=True, size=(80, 24)) as pilot_ctrl_q:
            await pilot_ctrl_q.pause(0.2)
            log_func("  Testing 'ctrl+q': Pressing 'ctrl+q'. App should NOT quit.")
            await pilot_ctrl_q.press("ctrl+q")
            await pilot_ctrl_q.pause(0.3)
            _ = pilot_ctrl_q.app.query_one("#prompt") # Changed to app.query_one
            results["ctrl_q_does_not_quit"] = True
            log_func("  'ctrl+q' test: OK (app did not quit).")
    except Exception as e:
        log_func(f"  'ctrl+q' test: FAILED. Error: {e}")
        results["ctrl_q_does_not_quit"] = False

    # Test 'ctrl+w'
    app_ctrl_w = app_class_to_test()
    app_exited_ctrl_w = False
    try:
        async with app_ctrl_w.run_test(headless=True, size=(80, 24)) as pilot_ctrl_w:
            await pilot_ctrl_w.pause(0.2)
            log_func("  Testing 'ctrl+w': Pressing 'ctrl+w'. App SHOULD quit.")
            await pilot_ctrl_w.press("ctrl+w")
            await pilot_ctrl_w.pause(0.5)
        app_exited_ctrl_w = True
        log_func("  'ctrl+w' test: OK (run_test block completed after ctrl+w).")
    except Exception as e:
        log_func(f"  'ctrl+w' test: FAILED. Error: {e}")
        app_exited_ctrl_w = False
    results["ctrl_w_quits"] = app_exited_ctrl_w

    log_func("\nKey binding test results summary:")
    log_func(f"  q_does_not_quit: {results['q_does_not_quit']}")
    log_func(f"  ctrl_q_does_not_quit: {results['ctrl_q_does_not_quit']}")
    log_func(f"  ctrl_w_quits: {results['ctrl_w_quits']}")

    all_passed = all(results.values())
    log_func(f"\nAll verifications passed: {all_passed}")
    return all_passed

# ==== Main entry point (from previous successful iteration) ====
if __name__ == "__main__":
    run_tests_flag = "--test-bindings" in sys.argv

    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Header, Footer

        class EmailHostLookupApp(App):
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

        if run_tests_flag:
            try:
                from textual.pilot import Pilot
            except ImportError:
                print("Could not import textual.pilot.Pilot. Testing framework requires full Textual install.")
                sys.exit(1)
            test_success = asyncio.run(_run_key_binding_tests(EmailHostLookupApp, print))
            if not test_success:
                sys.exit(1)
        else:
            EmailHostLookupApp().run()
    except ImportError as e:
        print("This script requires Textual and dnspython.\nInstall them with:\n  pip install textual dnspython")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
