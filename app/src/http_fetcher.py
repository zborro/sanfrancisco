import httpx
from urllib.parse import urlparse

_UNKNOWN_CONTENT_TYPE = "application/octet-stream"


class FetchError(Exception):
    def __init__(self, reason):
        self.reason = reason


class InvalidHttpUrlError(Exception):
    reason = "invalid url"


class HttpFetcher:
    def __init__(self, config):
        self.config = config

    def validate_http_url(self, url):
        # Could also try to convert UTF letters into punycodes.
        parsed_url = urlparse(str(url))
        if parsed_url.scheme not in ("http", "https") or not len(
            parsed_url.netloc.encode("ascii", "ignore").strip()
        ):
            raise InvalidHttpUrlError

    def is_binary_mime_type(self, mimetype):
        # based on:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
        type_, subtype = mimetype.split("/")
        subtype = subtype.split(";")[0]
        return (
            type_ != "text"
            or type_ == "application"
            or subtype
            in (
                "x-httpd-php",
                "xml",
                "xhtml+xml",
                "x-sh",
                "x-csh",
                "json",
                "ld+json",
            )
        )

    async def fetch_http_body(self, url):
        payload = b""

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": self.config["ua_string"]},
                max_redirects=self.config["max_redirects"],
                follow_redirects=True,
                timeout=httpx.Timeout(
                    self.config["timeout_read_seconds"],
                    connect=self.config["timeout_connect_seconds"],
                ),
            ) as client:
                async with client.stream("GET", url) as stream:
                    if stream.status_code != 200:
                        raise FetchError(reason="non-200 HTTP status_code")
                    if not self.config["allow_binary_mime_types"] and self.is_binary_mime_type(
                        stream.headers.get("content-type", _UNKNOWN_CONTENT_TYPE)
                    ):
                        raise FetchError(reason="non-textual response")

                    # In theory Content-Length header check should be sufficient,
                    # but that header is not always present.
                    async for chunk in stream.aiter_bytes():
                        payload += chunk
                        if len(payload) > self.config["max_payload_size_bytes"]:
                            raise FetchError(reason="exceeded max payload size")
        except httpx.ConnectError as exc:
            raise FetchError("connection timed out") from exc
        except httpx.ReadTimeout as exc:
            raise FetchError("read timed out") from exc
        except httpx.TooManyRedirects as exc:
            raise FetchError("too many HTTP redirects") from exc

        return payload.decode("utf-8", errors="replace")
