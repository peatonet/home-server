#!/usr/bin/env python3

import sys
import argparse
from uptime_kuma_api import UptimeKumaApi, UptimeKumaException

# ---- Config section ----
KUMA_URL = "<UPTIME_KUMA_IP/URL>"
KUMA_USERNAME = "admin"
KUMA_PASSWORD = "<UPTIMA_ADMIN_PASSWORD>"
# ------------------------

USAGE = """\
Usage:
  ./downtimes.py pause [--tag TAG ...] [--name NAME ...]
  ./downtimes.py resume [--tag TAG ...] [--name NAME ...]

Examples:
  ./downtimes.py pause
  ./downtimes.py resume -t prod -t staging
  ./downtimes.py pause -n "API Health" -n "DB Ping"
"""

def parse_args():
    p = argparse.ArgumentParser(
        description="Pause/Resume Uptime Kuma monitors, optionally filtered by tags and/or names."
    )
    p.add_argument("action", choices=["pause", "resume"], help="Action to perform.")
    p.add_argument(
        "-t", "--tag", dest="tags", action="append", default=[],
        help="Filter by tag name. Can be used multiple times."
    )
    p.add_argument(
        "-n", "--name", dest="names", action="append", default=[],
        help='Filter by monitor friendly name (exact, case-insensitive). Can be used multiple times.'
    )
    return p.parse_args()

def get_monitor_tags(api, monitor_id):
    try:
        return api.get_tags_for_monitor(monitor_id) or []
    except Exception:
        return []

def name_matches(m, wanted_names_lower):
    if not wanted_names_lower:
        return False
    return m.get("name", "").lower() in wanted_names_lower

def tags_match(api, m, wanted_tags_lower):
    if not wanted_tags_lower:
        return False
    tags = get_monitor_tags(api, m["id"])
    return any((t.get("name", "").lower() in wanted_tags_lower) for t in tags)

def resume_monitor_compat(api, monitor):
    """Try resume_monitor(); if unavailable, force active=1 via edit_monitor()."""
    try:
        # Preferred if available
        api.resume_monitor(monitor["id"])
        return
    except AttributeError:
        pass  # fall back below

    # Fallback: fetch current config and set active=1
    # Many lib versions expose edit_monitor with a dict or discrete params; we’ll use dict form if present.
    try:
        # Get the full monitor object (some versions return enough fields from get_monitors())
        # If not, we still try to set minimal fields.
        payload = dict(monitor)
        payload["active"] = 1
        # Some versions require explicit fields; keep name/type/url as-is if present
        api.edit_monitor(payload)
    except Exception:
        # As a last resort, try the simple toggle (pause_monitor) twice (pause->resume)
        # Only do this if the monitor is currently paused; we won’t know without extra calls,
        # so we skip risky toggling here.
        raise

def main():
    args = parse_args()
    action = args.action
    names_lower = {s.lower() for s in args.names}
    tags_lower = {s.lower() for s in args.tags}

    api = UptimeKumaApi(KUMA_URL)

    try:
        api.login(KUMA_USERNAME, KUMA_PASSWORD)
        monitors = api.get_monitors()

        # Build target set
        if not names_lower and not tags_lower:
            target = monitors[:]  # all
            filter_desc = "all monitors"
        else:
            target = []
            for m in monitors:
                if name_matches(m, names_lower) or tags_match(api, m, tags_lower):
                    target.append(m)

            parts = []
            if names_lower:
                parts.append(f'names: {", ".join(sorted(args.names))}')
            if tags_lower:
                parts.append(f'tags: {", ".join(sorted(args.tags))}')
            filter_desc = " | ".join(parts) if parts else "all monitors"

        if not target:
            print(f"No monitors matched ({filter_desc}).")
            return

        changed = 0
        for m in target:
            if action == "pause":
                # Some versions accept pause_monitor(id) or pause_monitor(id, True); use the simple, widely supported one.
                api.pause_monitor(m["id"])
            else:
                try:
                    resume_monitor_compat(api, m)
                except Exception as e:
                    print(f'⚠️  Could not resume "{m.get("name", m["id"])}": {e}')
                    continue
            changed += 1

        print(f'{action.capitalize()}d {changed} monitor(s) '
              f'({filter_desc})')

    except UptimeKumaException as e:
        print("API error:", e)
        sys.exit(3)
    finally:
        api.disconnect()

if __name__ == "__main__":
    main()
