import ipaddress
import re
import socket

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)    # Creates a IP address object
        return True
    except ValueError:
        return False


def is_valid_hostname(value: str) -> bool:
    return bool(_HOSTNAME_RE.match(value))


def is_valid_target(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    return is_valid_ip(value) or is_valid_hostname(value)


def resolve_to_ip(value: str) -> str | None:
    if is_valid_ip(value):
        return value
    try:
        return socket.gethostbyname(value)   # Translating the hostname into IP address string.
    except (socket.gaierror, UnicodeError):
        return None


def is_private_or_reserved(value: str) -> bool:
    ip_str = resolve_to_ip(value)
    if ip_str is None:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_multicast
    )