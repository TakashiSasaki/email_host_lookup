# tests/test_email_host_lookup_screen.py
import pytest
from unittest import mock
from textual.widgets import Input, RichLog # Reverted to RichLog
from email_host_lookup.email_host_lookup_screen import EmailHostLookupApp, EmailHostLookupScreen
import email_host_lookup.email_host_lookup_screen # For resetting _instance
from email_host_lookup.email_host_lookup import detect_provider # Updated import

def test_detect_google_workspace():
    mx_records = ["aspmx.l.google.com", "alt1.aspmx.l.google.com"]
    assert detect_provider(mx_records) == "Google Workspace"

def test_detect_microsoft_365():
    mx_records = ["yourdomain-com.mail.protection.outlook.com"]
    assert detect_provider(mx_records) == "Microsoft 365"
    mx_records_alt = ["example.mail.onmicrosoft.com"] # Alternative pattern
    # This alternative isn't explicitly in the original code,
    # but good to consider for robustness if we were to expand.
    # For now, sticking to what's in the original function.
    # assert detect_provider(mx_records_alt) == "Microsoft 365"


def test_detect_yahoo_mail():
    mx_records = ["mta5.am0.yahoodns.net"]
    assert detect_provider(mx_records) == "Yahoo Mail"

def test_detect_zoho_mail():
    mx_records = ["mx.zoho.com", "mx2.zoho.com"]
    assert detect_provider(mx_records) == "Zoho Mail"

def test_detect_protonmail():
    mx_records = ["mail.protonmail.ch", "mailsec.protonmail.ch"]
    assert detect_provider(mx_records) == "ProtonMail"

def test_detect_fastmail():
    mx_records = ["in1-smtp.messagingengine.com", "in2-smtp.messagingengine.com"]
    # The detect_provider function in email_host_lookup.py now recognizes "messagingengine.com"
    assert detect_provider(mx_records) == "Fastmail"

    # Test with actual "fastmail" in domain
    mx_records_with_fastmail = ["mx.example.fastmail.com"]
    assert detect_provider(mx_records_with_fastmail) == "Fastmail"


def test_detect_unknown_provider():
    mx_records = ["mail.someotherprovider.com"]
    assert detect_provider(mx_records) == "Unknown or Custom Provider"

def test_detect_empty_mx_records():
    mx_records = []
    assert detect_provider(mx_records) == "Unknown or Custom Provider"

def test_detect_mixed_providers_first_match():
    # Google is first in the function's logic
    mx_records = ["mail.someotherprovider.com", "aspmx.l.google.com"]
    assert detect_provider(mx_records) == "Google Workspace"

@pytest.mark.asyncio
async def test_screen_initial_composition():
    email_host_lookup.email_host_lookup_screen._instance = None
    async with EmailHostLookupApp().run_test() as pilot:
        actual_screen = pilot.app.query_one(EmailHostLookupScreen)
        assert actual_screen.query_one("#prompt") is not None
        email_input = actual_screen.query_one("#email_input", Input)
        assert email_input is not None
        assert email_input.placeholder == "user@example.com"
        assert actual_screen.query_one("#lookup_button") is not None
        log_widget_initial = actual_screen.query_one("#output_log", RichLog) # Reverted to RichLog
        assert log_widget_initial is not None
        # Check that the log is initially empty
        initial_log_content = "".join(segment.text for strip_line in log_widget_initial.lines for segment in strip_line._segments if strip_line._segments is not None) # Reverted extraction
        assert initial_log_content == ""

@pytest.mark.asyncio
async def test_lookup_button_invalid_email_format():
    email_host_lookup.email_host_lookup_screen._instance = None
    async with EmailHostLookupApp().run_test() as pilot:
        actual_screen = pilot.app.query_one(EmailHostLookupScreen)
        input_widget = actual_screen.query_one("#email_input", Input)
        input_widget.value = "invalidemail"
        await pilot.click("#lookup_button") # No pause after this in the test

        # Query for log_widget *after* waiting, ensuring it's from the correct screen instance
        log_widget = actual_screen.query_one("#output_log", RichLog) # Reverted to RichLog
        log_content = "".join(segment.text for strip_line in log_widget.lines for segment in strip_line._segments if strip_line._segments is not None) # Reverted extraction

        print(f"Log content for invalid_email: '{log_content}'") # Temporary print for debugging
        # LAD_AFTER_CLEAR should be written, then "[red]Invalid email address[/red]"
        # Assertions based on the final expected state of the log for this path:
        assert "LAD_AFTER_CLEAR" in log_content
        assert "[red]Invalid email address[/red]" in log_content # Reverted to Rich formatting

@pytest.mark.asyncio
async def test_lookup_button_successful_lookup_mocked():
    # Path to mock is where it's *looked up*, not where it's defined.
    # It's looked up in email_host_lookup_screen.py
    email_host_lookup.email_host_lookup_screen._instance = None
    with mock.patch("email_host_lookup.email_host_lookup_screen.get_email_host_info") as mock_lookup:
        mock_lookup.return_value = ("example.com", ["mx.example.com"], "Mocked Provider")
        async with EmailHostLookupApp().run_test() as pilot:
            actual_screen = pilot.app.query_one(EmailHostLookupScreen)
            input_widget = actual_screen.query_one("#email_input", Input)
            input_widget.value = "user@example.com"
            await pilot.click("#lookup_button") # No pause after this

            mock_lookup.assert_called_once() # Crucial check

            # Query for log_widget *after* waiting, ensuring it's from the correct screen instance
            log_widget = actual_screen.query_one("#output_log", RichLog) # Reverted to RichLog
            log_content = "".join(segment.text for strip_line in log_widget.lines for segment in strip_line._segments if strip_line._segments is not None) # Reverted extraction

            print(f"Log content for successful_lookup: '{log_content}'") # Temporary print for debugging
            assert "LAD_AFTER_CLEAR" in log_content
            assert "[bold]Looking up MX records for:[/bold] example.com" in log_content # Reverted to Rich formatting
            assert "[green]MX Records:[/green] mx.example.com" in log_content # Reverted to Rich formatting
            assert "[cyan]Likely mail provider:[/cyan] Mocked Provider" in log_content # Reverted to Rich formatting

@pytest.mark.asyncio
async def test_lookup_button_dns_failure_mocked():
    # Using a generic Exception for simplicity in test, could be dns.resolver.NXDOMAIN
    email_host_lookup.email_host_lookup_screen._instance = None
    with mock.patch("email_host_lookup.email_host_lookup_screen.get_email_host_info") as mock_lookup:
        mock_lookup.side_effect = Exception("Mocked DNS resolution failed")
        async with EmailHostLookupApp().run_test() as pilot:
            actual_screen = pilot.app.query_one(EmailHostLookupScreen)
            input_widget = actual_screen.query_one("#email_input", Input)
            input_widget.value = "user@faildomain.com"
            await pilot.click("#lookup_button") # No pause after this

            mock_lookup.assert_called_once()

            # Query for log_widget *after* waiting, ensuring it's from the correct screen instance
            log_widget = actual_screen.query_one("#output_log", RichLog) # Reverted to RichLog
            log_content = "".join(segment.text for strip_line in log_widget.lines for segment in strip_line._segments if strip_line._segments is not None) # Reverted extraction

            print(f"Log content for dns_failure: '{log_content}'") # Temporary print for debugging
            assert "LAD_AFTER_CLEAR" in log_content
            assert "[bold]Looking up MX records for:[/bold] faildomain.com" in log_content # Reverted to Rich formatting
            assert "[red]Failed to resolve: Mocked DNS resolution failed[/red]" in log_content # Reverted to Rich formatting
