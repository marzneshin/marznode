# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: marznode/backends/singbox/sb_stats.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(marznode/backends/singbox/sb_stats.proto\x12\x1cv2ray.core.app.stats.command\".\n\x0fGetStatsRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05reset\x18\x02 \x01(\x08\"#\n\x04Stat\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x03\"D\n\x10GetStatsResponse\x12\x30\n\x04stat\x18\x01 \x01(\x0b\x32\".v2ray.core.app.stats.command.Stat\"U\n\x11QueryStatsRequest\x12\x0f\n\x07pattern\x18\x01 \x01(\t\x12\r\n\x05reset\x18\x02 \x01(\x08\x12\x10\n\x08patterns\x18\x03 \x03(\t\x12\x0e\n\x06regexp\x18\x04 \x01(\x08\"F\n\x12QueryStatsResponse\x12\x30\n\x04stat\x18\x01 \x03(\x0b\x32\".v2ray.core.app.stats.command.Stat\"\x11\n\x0fSysStatsRequest\"\xc2\x01\n\x10SysStatsResponse\x12\x14\n\x0cNumGoroutine\x18\x01 \x01(\r\x12\r\n\x05NumGC\x18\x02 \x01(\r\x12\r\n\x05\x41lloc\x18\x03 \x01(\x04\x12\x12\n\nTotalAlloc\x18\x04 \x01(\x04\x12\x0b\n\x03Sys\x18\x05 \x01(\x04\x12\x0f\n\x07Mallocs\x18\x06 \x01(\x04\x12\r\n\x05\x46rees\x18\x07 \x01(\x04\x12\x13\n\x0bLiveObjects\x18\x08 \x01(\x04\x12\x14\n\x0cPauseTotalNs\x18\t \x01(\x04\x12\x0e\n\x06Uptime\x18\n \x01(\r2\xde\x02\n\x0cStatsService\x12k\n\x08GetStats\x12-.v2ray.core.app.stats.command.GetStatsRequest\x1a..v2ray.core.app.stats.command.GetStatsResponse\"\x00\x12q\n\nQueryStats\x12/.v2ray.core.app.stats.command.QueryStatsRequest\x1a\x30.v2ray.core.app.stats.command.QueryStatsResponse\"\x00\x12n\n\x0bGetSysStats\x12-.v2ray.core.app.stats.command.SysStatsRequest\x1a..v2ray.core.app.stats.command.SysStatsResponse\"\x00\x42u\n com.v2ray.core.app.stats.commandP\x01Z0github.com/v2fly/v2ray-core/v5/app/stats/command\xaa\x02\x1cV2Ray.Core.App.Stats.Commandb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'marznode.backends.singbox.sb_stats_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n com.v2ray.core.app.stats.commandP\001Z0github.com/v2fly/v2ray-core/v5/app/stats/command\252\002\034V2Ray.Core.App.Stats.Command'
  _globals['_GETSTATSREQUEST']._serialized_start=74
  _globals['_GETSTATSREQUEST']._serialized_end=120
  _globals['_STAT']._serialized_start=122
  _globals['_STAT']._serialized_end=157
  _globals['_GETSTATSRESPONSE']._serialized_start=159
  _globals['_GETSTATSRESPONSE']._serialized_end=227
  _globals['_QUERYSTATSREQUEST']._serialized_start=229
  _globals['_QUERYSTATSREQUEST']._serialized_end=314
  _globals['_QUERYSTATSRESPONSE']._serialized_start=316
  _globals['_QUERYSTATSRESPONSE']._serialized_end=386
  _globals['_SYSSTATSREQUEST']._serialized_start=388
  _globals['_SYSSTATSREQUEST']._serialized_end=405
  _globals['_SYSSTATSRESPONSE']._serialized_start=408
  _globals['_SYSSTATSRESPONSE']._serialized_end=602
  _globals['_STATSSERVICE']._serialized_start=605
  _globals['_STATSSERVICE']._serialized_end=955
# @@protoc_insertion_point(module_scope)
