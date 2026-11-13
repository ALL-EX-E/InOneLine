"""Pure validation for provider-supplied emoji image URLs."""

from urllib.parse import urlsplit


IMAGE_HOSTS = frozenset({"yt3.ggpht.com", "yt4.ggpht.com", "yt3.googleusercontent.com",
                         "fonts.gstatic.com", "www.gstatic.com", "i.ytimg.com", "www.youtube.com"})


def safe_emoji_url(value):
    if not isinstance(value, str) or len(value) > 4096:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    try:
        url = urlsplit(value)
        if (url.scheme != "https" or url.hostname not in IMAGE_HOSTS
                or url.username or url.password or url.port not in {None, 443}
                or url.fragment or any(ord(c) < 32 for c in value)):
            return ""
        if url.hostname == "www.youtube.com" and not url.path.startswith("/s/"):
            return ""
    except ValueError:
        return ""
    return value


def safe_avatar_url(value):
    """Validate a provider avatar using the same HTTPS image policy."""
    return safe_emoji_url(value)
