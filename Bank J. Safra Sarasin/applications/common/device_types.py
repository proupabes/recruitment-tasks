from __future__ import annotations
from enum import Enum

class DeviceType(str, Enum):
    Android = "Android"
    iOS = "iOS"
    Windows = "Windows"
    macOS = "macOS"
    Linux = "Linux"
    BSD = "BSD"
    Desktop = "Desktop"
    Laptop = "Laptop"
    Tablet = "Tablet"
    Phone = "Phone"
    SmartTV = "SmartTV"
    Wearable = "Wearable"
    Bot = "Bot"
    Unknown = "Unknown"

def _normalize_key(raw: str) -> str:
    """
    Make a device-type key suitable for lookup:
    - trim, lowercase
    - remove spaces, dashes, underscores, dots, slashes
    """
    k = (raw or "").strip().lower()
    # unify separators and known punctuation
    for ch in (" ", "-", "_", ".", "/"):
        k = k.replace(ch, "")
    return k

# Synonyms map to canonical DeviceType values (keys are after _normalize_key)
_CANON_MAP = {
    # --- Android ---
    "android": DeviceType.Android,

    # --- iOS / Apple mobile ---
    "ios": DeviceType.iOS,
    "iphone": DeviceType.iOS,
    "ipad": DeviceType.iOS,
    "ipados": DeviceType.iOS,

    # --- Windows ---
    "windows": DeviceType.Windows,
    "win": DeviceType.Windows,
    "win10": DeviceType.Windows,
    "win11": DeviceType.Windows,

    # --- macOS ---
    "macos": DeviceType.macOS,
    "osx": DeviceType.macOS,
    "mac": DeviceType.macOS,

    # --- Linux (common distros) ---
    "linux": DeviceType.Linux,
    "ubuntu": DeviceType.Linux,
    "debian": DeviceType.Linux,
    "fedora": DeviceType.Linux,
    "arch": DeviceType.Linux,
    "manjaro": DeviceType.Linux,
    "centos": DeviceType.Linux,
    "rhel": DeviceType.Linux,
    "gentoo": DeviceType.Linux,
    "opensuse": DeviceType.Linux,
    "suse": DeviceType.Linux,
    "mint": DeviceType.Linux,
    "elementary": DeviceType.Linux,
    "popos": DeviceType.Linux,
    # https://www.alpinelinux.org/
    "alpine": DeviceType.Linux,
    "alpinelinux": DeviceType.Linux,
    "void": DeviceType.Linux,
    "voidlinux": DeviceType.Linux,

    # --- BSD family (canonical -> BSD) ---
    "bsd": DeviceType.BSD,
    "freebsd": DeviceType.BSD,
    "openbsd": DeviceType.BSD,
    "netbsd": DeviceType.BSD,
    "dragonflybsd": DeviceType.BSD,
    "dragonfly": DeviceType.BSD,
    # https://hardenedbsd.org/
    "hardenedbsd": DeviceType.BSD,
    # downstreams/appliances based on FreeBSD:
    "truenas": DeviceType.BSD,
    "pfsense": DeviceType.BSD,
    "opnsense": DeviceType.BSD,
    # popular desktop-focused BSDs:
    "ghostbsd": DeviceType.BSD,
    "midnightbsd": DeviceType.BSD,
    "nomadbsd": DeviceType.BSD,

    # --- Form factors ---
    "desktop": DeviceType.Desktop,
    "pc": DeviceType.Desktop,
    "workstation": DeviceType.Desktop,
    "laptop": DeviceType.Laptop,
    "notebook": DeviceType.Laptop,
    "ultrabook": DeviceType.Laptop,
    "tablet": DeviceType.Tablet,
    "phone": DeviceType.Phone,
    "mobile": DeviceType.Phone,

    # --- TV / wearables ---
    "smarttv": DeviceType.SmartTV,
    "tv": DeviceType.SmartTV,
    "wearable": DeviceType.Wearable,
    "watch": DeviceType.Wearable,

    # --- Bots / crawlers ---
    "bot": DeviceType.Bot,
    "crawler": DeviceType.Bot,
    "spider": DeviceType.Bot,
}

# Allow exact canonical strings to pass through too
for _dt in DeviceType:
    _CANON_MAP[_normalize_key(_dt.value)] = _dt

def normalize_device_type(raw: str) -> DeviceType:
    """
    Returns a canonical DeviceType for any input string.
    Never raises; falls back to DeviceType.Unknown.
    """
    key = _normalize_key(raw)
    return _CANON_MAP.get(key, DeviceType.Unknown)
