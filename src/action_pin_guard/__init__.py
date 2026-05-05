"""Public package interface for action-pin-guard."""

from action_pin_guard.scanner import Finding, Summary, scan_paths

__all__ = ["Finding", "Summary", "scan_paths"]
