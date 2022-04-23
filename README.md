# hello San FranCisco

> far from perfect, but is IMO good starting point

## Running

### Docker

```shell
docker-compose up -d
```

After running the service is available at `http://localhost:8080/`. Under `http://localhost:8080/docs`
API documentation can be found with possibility to try it out.


Testing from command line:

```
curl -XPOST localhost:8080/ping -H "Content-Type: application/json" -d '{"url": "https://cisco.com/"}'
```

## Running tests

```shell
cd app/
tox

```

Coverage HTML files are generated in `htmlcov` directory.

## Design

Service is written in Python 3.10 with `FastAPI` framework and `httpx` library. Requests are
handled asynchronously in an ad-hoc manner.


Docker-Compose is used for deployment, but there's no obstacle to create e.g. Helm chart.


SSL is ignored in the implementation.

## Alternative designs

Depending on real use case other design could be proposed. E.g. service could utilize HTTP long
poll with Celery/Rabbit at the backend.

## Implementation details, trade-offs, and technical considerations

#### Error reporting

Payload is not returned as-is, because it would be cumbersome to inform about encountered errrors.
JSON is used by the service, so the client must unwrap the payload after checking that the status
field is set to `ok`.

#### DNS resolution

Service that performs HTTP fetch is probably deployed in the environment, where custom DNS
servers are set in the OS. This poses a danger. Attacker, knowing internal domain names
from other sources can exploit the service to fetch data from resource that should not be
exposed. Therefore in this implementation DNS resolution takes place before actual HTTP
GET request is executed. DNS servers can be configured in config (e.g. `1.1.1.1` or `8.8.8.8`
can be provided, so only public services can be fetched).

Please take note, that the implementation is not ideal. There might be a discrepancy between
OS-set nameservers and what is set in the config. Solution to this problem is to replace
`httpx` (`httpcore`) transport class with a custom one that uses customized DNS resolution.
Unfortunately, `httpx` is not as mature as e.g. `requests`. But `requests` are not asynchronous.

#### Forbidden IP networks

Potential attacker can try to exploit the service by letting it fetch local resources. E.g.
if there are some servers running in `10.0.0.0/8` network, fetching from them should be disabled.
Same for other networks like `192.168.0.0/16` etc. Since different deployments may require different
networks to be disabled, there's an option in the config to specify forbidden IP networks.

#### HTTP 3xx redirections

Common danger for all HTTP crawlers and services such as this one is that target resource may
cause infinite HTTP redirection loop. That would render one of the workers unavailable and is
exemplary (D)DoS vector. On the other hand many links are shortened nowadays, so maximum number
of HTTP redirections is introduced and can be configured.

#### Information leak

The service retrieves data from external servers and therefore leaks some information. At the
TCP/IP layer this is e.g. IP address. At the HTTP layer all the headers are leaked to potential
attacker. In order not to reveal information about libraries used and their versions, User Agent
string is replaced and configurable.

#### MIME types (Content-Type) / encoding

Attacker can try to mislead the service into believing that it's dealing with textual data by
manipulating `Content-Type` header. In order to prevent errors the service encodes everything with
UTF-8. Invalid sequences are replaced with `?` symbol.

It is also assumed that encoding is always compatible with UTF-8.

### Possible improvements

Following sections describe subset of improvements only. Depending on requirements any part of the
design or implementation could be subject of changes.

#### IPv6

IPv6 case was not carefully implemented. This is something that should be taken into account
in the production version of the service.

#### Caching

Caching can be used for two cases:

  1. "hot links" - links that are requested frequently
  2. "dead links" - links that aren't working or time out

Since load balancing is normally used for such services, cache should run somewhere else, like
for instance, some Redis deployment (with sentinel).

For dead links, if there are many of them, Bloom filters can be used.

#### Rate limiting

Solution like `fail2ban` or equivalent should be used for production version of the service.
Otherwise the service may be used by attackers to perform massive scans.

#### URL equivalence

URLs can contain information that isn't actually passed to the server - e.g. `http://example.com/resource#spa-param`.
These client-only URL parameters should be removed before doing actual fetch.

#### Allowlist/blocklist for specific domains

Some domains should never be fetched. For example, sites with adult content and banned sites. The list
of such domains is perhaps long, so storing them in separate file would be probably better than bloating
config file.

#### Network interface used for fetching

It should be possible to configure the service to use specific network interface to access Internet.

#### Encoding

UTF-8 is the only encoding taken into account in the implementation. It was not tested how the service
responds to encoding problems. All non-UTF-8-encodable characters are replaced with `?` symbol`.

#### Verifying client

SSL can be used to make sure that only allowed clients can contact the service. Other possibility
is to block access based on client's user agent (e.g. internet bots).
