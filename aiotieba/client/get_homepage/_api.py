from typing import List, Tuple

import httpx

from .._classdef.core import TiebaCore
from .._exception import TiebaServerError
from .._helper import APP_BASE_HOST, pack_proto_request, raise_for_status, url
from ._classdef import Thread_home, UserInfo_home
from .protobuf import ProfileReqIdl_pb2, ProfileResIdl_pb2


def pack_proto(core: TiebaCore, portrait: str, with_threads: bool) -> bytes:
    req_proto = ProfileReqIdl_pb2.ProfileReqIdl()
    req_proto.data.common._client_version = core.main_version
    req_proto.data.common._client_type = 2
    req_proto.data.need_post_count = 1
    req_proto.data.friend_uid_portrait = portrait
    if not with_threads:
        req_proto.data.pn = 255  # not too large

    return req_proto.SerializeToString()


def pack_request(client: httpx.AsyncClient, core: TiebaCore, portrait: str, with_threads: bool) -> httpx.Request:
    request = pack_proto_request(
        client,
        url("http", APP_BASE_HOST, "/c/u/user/profile", "cmd=303012"),
        pack_proto(core, portrait, with_threads),
    )

    return request


def parse_proto(proto: bytes) -> Tuple[UserInfo_home, List[Thread_home]]:
    res_proto = ProfileResIdl_pb2.ProfileResIdl()
    res_proto.ParseFromString(proto)

    if code := res_proto.error.errorno:
        raise TiebaServerError(code, res_proto.error.errmsg)

    data_proto = res_proto.data
    user = UserInfo_home()._init(data_proto.user)

    anti_proto = data_proto.anti_stat
    if anti_proto.block_stat and anti_proto.hide_stat and anti_proto.days_tofree > 30:
        user._is_blocked = True
    else:
        user._is_blocked = False

    threads = [Thread_home()._init(p) for p in data_proto.post_list]

    for thread in threads:
        thread._user = user

    return user, threads


def parse_response(response: httpx.Response) -> Tuple[UserInfo_home, List[Thread_home]]:
    raise_for_status(response)

    return parse_proto(response.content)