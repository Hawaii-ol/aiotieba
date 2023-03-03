import httpx

from .._exception import TiebaServerError
from .common.core import TiebaCore
from .common.helper import APP_BASE_HOST, jsonlib, pack_form_request, raise_for_status, sign, url


def pack_request(
    client: httpx.AsyncClient, core: TiebaCore, tbs: str, fname: str, fid: int, portrait: str, day: int, reason: str
) -> httpx.Request:

    data = [
        ('BDUSS', core.BDUSS),
        ('day', day),
        ('fid', fid),
        ('ntn', 'banid'),
        ('portrait', portrait),
        ('reason', reason),
        ('tbs', tbs),
        ('word', fname),
        ('z', '6'),
    ]

    request = pack_form_request(
        client,
        url("http", APP_BASE_HOST, "/c/c/bawu/commitprison"),
        sign(data),
    )

    return request


def parse_response(response: httpx.Response) -> None:
    raise_for_status(response)

    res_json = jsonlib.loads(response.content)
    if code := int(res_json['error_code']):
        raise TiebaServerError(code, res_json['error_msg'])