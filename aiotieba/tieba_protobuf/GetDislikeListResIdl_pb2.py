# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: GetDislikeListResIdl.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import Error_pb2 as Error__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1aGetDislikeListResIdl.proto\x1a\x0b\x45rror.proto\"\xa4\x02\n\x14GetDislikeListResIdl\x12\x15\n\x05\x65rror\x18\x01 \x01(\x0b\x32\x06.Error\x12+\n\x04\x64\x61ta\x18\x02 \x01(\x0b\x32\x1d.GetDislikeListResIdl.DataRes\x1a\xc7\x01\n\x07\x44\x61taRes\x12;\n\nforum_list\x18\x01 \x03(\x0b\x32\'.GetDislikeListResIdl.DataRes.ForumList\x12\x10\n\x08has_more\x18\x02 \x01(\x05\x1am\n\tForumList\x12\x10\n\x08\x66orum_id\x18\x01 \x01(\x03\x12\x12\n\nforum_name\x18\x02 \x01(\t\x12\x14\n\x0cmember_count\x18\x04 \x01(\r\x12\x10\n\x08post_num\x18\x07 \x01(\x03\x12\x12\n\nthread_num\x18\x08 \x01(\x03\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'GetDislikeListResIdl_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GETDISLIKELISTRESIDL._serialized_start=44
  _GETDISLIKELISTRESIDL._serialized_end=336
  _GETDISLIKELISTRESIDL_DATARES._serialized_start=137
  _GETDISLIKELISTRESIDL_DATARES._serialized_end=336
  _GETDISLIKELISTRESIDL_DATARES_FORUMLIST._serialized_start=227
  _GETDISLIKELISTRESIDL_DATARES_FORUMLIST._serialized_end=336
# @@protoc_insertion_point(module_scope)
