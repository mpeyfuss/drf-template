import vcr.stubs.httpx_stubs
from vcr.request import Request as VcrRequest

#
# Unit testing monkey patches go here
#


def _make_vcr_request(httpx_request, **kwargs):
    """
    Fix httpx binary upload vcr recordings.
    https://github.com/kevin1024/vcrpy/pull/657
    """
    # Try to parse to string otherwise leave as binary format
    try:
        body = httpx_request.read().decode("utf-8")
    except UnicodeDecodeError:
        body = httpx_request.read()

    uri = str(httpx_request.url)
    headers = dict(httpx_request.headers)
    return VcrRequest(httpx_request.method, uri, body, headers)


vcr.stubs.httpx_stubs._make_vcr_request = _make_vcr_request
