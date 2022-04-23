import httpx
import pytest
from pytest_httpx import HTTPXMock
from http_fetcher import HttpFetcher, FetchError, InvalidHttpUrlError
from config_utils import _DEFAULT_CONFIG

test_config = _DEFAULT_CONFIG["http"]
http_fetcher = HttpFetcher(test_config)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",
        "http://www.example.com/",
        "https://www.example.com/",
        "https://www.example.com/resource?param1=1&param2=2",
    ],
)
def test_validate_http_url_valid_url(url):
    http_fetcher.validate_http_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://",
        "no.schema/resource",
        "ftp://example.com",
        "http:// /resource",
        "http://żółć/resource",
    ],
)
def test_validate_http_url_invalid_url(url):
    with pytest.raises(InvalidHttpUrlError):
        http_fetcher.validate_http_url(url)


def add_httpx_mock_response(httpx_mock, content_type="text/plain", **kwargs):
    headers = {**kwargs.pop("headers", {}), **{"content-type": content_type}}
    httpx_mock.add_response(headers=headers, **kwargs)


@pytest.mark.parametrize(
    "body",
    [
        "",
        "This is just an example",
        "Let's see <html> tags in action </html>",
    ],
)
async def test_fetch_works(httpx_mock, body):
    httpx_mock.add_response(text=body)
    assert await http_fetcher.fetch_http_body("http://some_url") == body


def construct_redirection_path(httpx_mock, redirects, final_url, final_body):
    for url_from, url_to in zip(redirects, redirects[1:]):
        add_httpx_mock_response(
            httpx_mock, url=url_from, status_code=303, headers={"Location": url_to}
        )
    add_httpx_mock_response(
        httpx_mock, url=redirects[-1], status_code=303, headers={"Location": final_url}
    )
    if final_body is not None:
        add_httpx_mock_response(httpx_mock, url=final_url, text=final_body)


async def test_fetch_single_redirection(httpx_mock):
    final_body = "example"
    construct_redirection_path(httpx_mock, ["http://sh.rt"], "http://example.com", final_body)
    assert await http_fetcher.fetch_http_body("http://sh.rt") == final_body


async def test_fetch_max_redirections(httpx_mock):
    final_body = "Finally arrived here"
    redirects = ["http://shortener", "http://www.shortener", "http://resource"]
    construct_redirection_path(httpx_mock, redirects, "http://www.resource", final_body)
    assert await http_fetcher.fetch_http_body("http://shortener") == final_body


async def test_fetch_too_many_redirections(httpx_mock):
    redirects = ["http://a", "http://b", "http://c", "http://d"]
    construct_redirection_path(httpx_mock, redirects, "http://e", None)
    with pytest.raises(FetchError):
        await http_fetcher.fetch_http_body("http://a")


async def test_ua_string(httpx_mock):
    add_httpx_mock_response(httpx_mock)
    await http_fetcher.fetch_http_body("http://example")
    assert httpx_mock.get_request().headers["user-agent"] == test_config["ua_string"]


async def test_max_payload_actual(httpx_mock):
    max_payload_size_bytes = test_config["max_payload_size_bytes"]
    add_httpx_mock_response(httpx_mock, url="http://good", text=" " * (max_payload_size_bytes))
    add_httpx_mock_response(
        httpx_mock, url="http://badbadnotgood", text=" " * (max_payload_size_bytes + 1)
    )
    await http_fetcher.fetch_http_body("http://good")
    with pytest.raises(FetchError):
        await http_fetcher.fetch_http_body("http://badbadnotgood")


async def test_binary_payload(httpx_mock):
    add_httpx_mock_response(httpx_mock, content_type="application/octet-stream")
    with pytest.raises(FetchError):
        await http_fetcher.fetch_http_body("http://example.com/resource")


async def test_non_200_status_code(httpx_mock):
    add_httpx_mock_response(httpx_mock, status_code=404)
    with pytest.raises(FetchError):
        await http_fetcher.fetch_http_body("http://example.com/resource")


async def test_connect_timeout(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Unable to connect within timeout"))

    with pytest.raises(FetchError) as e:
        await http_fetcher.fetch_http_body("http://example.com/resource")


async def test_read_timeout(httpx_mock):
    httpx_mock.add_exception(httpx.ReadTimeout("Unable to read within timeout"))

    with pytest.raises(FetchError) as e:
        await http_fetcher.fetch_http_body("http://example.com/resource")
