from fastapi import FastAPI, Response, status
import logging
from fastapi.responses import HTMLResponse
from models import PingBody, PingResponse, PingError
from host_resolver import HostResolver, ForbiddenIpError, DnsResolutionFailed
from http_fetcher import HttpFetcher, FetchError, InvalidHttpUrlError
from config_utils import read_config

logging.basicConfig(level=logging.INFO)
app = FastAPI()
CONFIG = read_config()


@app.get("/info")
async def get_info():
    return {"Receiver": "Cisco is the best!"}


@app.post("/ping", status_code=200, response_model=PingResponse)
async def post_ping(ping: PingBody, response: Response):
    host_resolver = HostResolver(CONFIG["net"])
    http_fetcher = HttpFetcher(CONFIG["http"])

    def error(reason):
        return PingResponse(status="error", status_details=PingError(reason=e.reason), payload=None)

    try:
        url = ping.url
        http_fetcher.validate_http_url(url)
        ip_list = await host_resolver.resolve_host(url)
        host_resolver.validate_ip_list(ip_list)
    except (InvalidHttpUrlError, DnsResolutionFailed, ForbiddenIpError) as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error(e.reason)
    except Exception as e:
        logging.exception("Encountered unknown exception")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return error("internal server error")

    try:
        payload = await http_fetcher.fetch_http_body(ping.url)
        return PingResponse(status="ok", payload=payload)
    except FetchError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return error(e.reason)
