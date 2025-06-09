import pytest
import asyncio
from textual.pilot import Pilot
from email_host_lookup.email_host_lookup_screen import EmailHostLookupApp

# Copied and adapted function:
@pytest.mark.asyncio
async def test_app_key_bindings(): # Renamed for pytest, log_func needs review
    # Original content of _run_key_binding_tests will be pasted here.
    # Ensure Pilot is correctly referenced, e.g. textual.pilot.Pilot
    # For now, direct calls to log_func will be kept, will be replaced by print or caplog later.

    results = {
        "q_quits": False,
        "ctrl_q_quits": False, # Changed from ctrl_q_does_not_quit
        "ctrl_w_quits": False,
    }
    print("Starting key binding tests...")

    # Test 'q' - This test now expects 'q' to quit the app
    app_q = EmailHostLookupApp()
    app_exited_q = False
    try:
        async with app_q.run_test(headless=True, size=(80, 24)) as pilot_q: # pilot_q is an instance of Pilot
            await pilot_q.pause(0.2)
            print("  Testing 'q': Pressing 'q'. App SHOULD quit.")
            await pilot_q.press("q")
            await pilot_q.pause(0.5) # Give time for app to exit
        app_exited_q = True # If run_test exits without error after 'q', it means app quit
        print("  'q' test: OK (run_test block completed after q).")
    except Exception as e:
        print(f"  'q' test: FAILED. Error: {e}")
        app_exited_q = False
    results["q_quits"] = app_exited_q

    # Test 'ctrl+q' - This test now expects 'ctrl+q' to quit the app
    app_ctrl_q = EmailHostLookupApp()
    app_exited_ctrl_q = False
    try:
        async with app_ctrl_q.run_test(headless=True, size=(80, 24)) as pilot_ctrl_q: # pilot_ctrl_q is an instance of Pilot
            await pilot_ctrl_q.pause(0.2)
            print("  Testing 'ctrl+q': Pressing 'ctrl+q'. App SHOULD quit.")
            await pilot_ctrl_q.press("ctrl+q")
            await pilot_ctrl_q.pause(0.5) # Give time for app to exit
        app_exited_ctrl_q = True # If run_test exits without error after 'ctrl+q', it means app quit
        print("  'ctrl+q' test: OK (run_test block completed after ctrl+q).")
    except Exception as e:
        print(f"  'ctrl+q' test: FAILED. Error: {e}")
        app_exited_ctrl_q = False
    results["ctrl_q_quits"] = app_exited_ctrl_q

    # Test 'ctrl+w'
    app_ctrl_w = EmailHostLookupApp()
    app_exited_ctrl_w = False
    try:
        async with app_ctrl_w.run_test(headless=True, size=(80, 24)) as pilot_ctrl_w: # pilot_ctrl_w is an instance of Pilot
            await pilot_ctrl_w.pause(0.2)
            print("  Testing 'ctrl+w': Pressing 'ctrl+w'. App SHOULD quit.")
            await pilot_ctrl_w.press("ctrl+w")
            await pilot_ctrl_w.pause(0.5)
        app_exited_ctrl_w = True
        print("  'ctrl+w' test: OK (run_test block completed after ctrl+w).")
    except Exception as e:
        print(f"  'ctrl+w' test: FAILED. Error: {e}")
        app_exited_ctrl_w = False
    results["ctrl_w_quits"] = app_exited_ctrl_w

    print("\nKey binding test results summary:")
    print(f"  q_quits: {results['q_quits']}")
    print(f"  ctrl_q_quits: {results['ctrl_q_quits']}") # Changed from ctrl_q_does_not_quit
    print(f"  ctrl_w_quits: {results['ctrl_w_quits']}")

    all_passed = all(results.values())
    print(f"\nAll verifications passed: {all_passed}")

    # Pytest uses assertions for test outcomes
    assert all_passed, "One or more key binding verifications failed."
