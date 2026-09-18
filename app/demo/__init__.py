"""Public demo mode.

Demo mode is a configuration flag, not a second code path. The demo accounts
are ordinary ``users`` rows with ordinary roles and ordinary hashed passwords,
so every service and authorization rule applies to them unchanged; the only
difference is that the sign-in page offers a one-click way in.

Nothing here is reachable when ``DEMO_MODE`` is false.
"""
