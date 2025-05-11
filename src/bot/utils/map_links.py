"""
Utility functions for generating map links for multiple office locations.
"""

from typing import Sequence, Any


def generate_google_maps_multi_pin_url(offices: Sequence[Any]) -> str:
    """Generate a Google Maps URL with multiple pins for the given offices."""
    if not offices:
        return "https://maps.google.com/"
    base = "https://www.google.com/maps/dir/"
    waypoints = "/".join(f"{o.lat:.4f},{o.lng:.4f}" for o in offices)
    return f"{base}{waypoints}"


def generate_apple_maps_multi_pin_url(offices: Sequence[Any]) -> str:
    """Generate an Apple Maps URL with multiple pins for the given offices."""
    if not offices:
        return "http://maps.apple.com/"
    pins = "&".join(f"q={o.lat:.4f},{o.lng:.4f}" for o in offices)
    return f"http://maps.apple.com/?{pins}"
