"""
Monkey-patch pyflp for Python 3.11 compatibility.

Python 3.11 added a pre-_missing_() guard in enum.__new__ that raises
TypeError when the enum class has no direct members, before _missing_ is
called. EventEnum has no direct members (they live in subclasses), so
EventEnum(value) always raises on Python 3.11.

Apply this module's patch() before any call to pyflp.parse() or pyflp.save().
"""
import sys


def patch():
    if sys.version_info < (3, 11):
        return

    import pyflp
    import pyflp._events as _ev
    from pyflp._events import EventEnum

    _orig_parse = pyflp.parse

    def _patched_parse(file):
        import io, os, struct
        import construct as c
        from pyflp._events import (
            DATA, DWORD, NEW_TEXT_IDS, TEXT, WORD,
            AsciiEvent, UnicodeEvent, U8Event, U16Event, U32Event,
            UnknownDataEvent, EventTree, IndexedEvent,
        )
        from pyflp.exceptions import HeaderCorrupted, VersionNotDetected
        from pyflp.plugin import PluginID, get_event_by_internal_name
        from pyflp.project import VALID_PPQS, FileFormat, Project

        FLP_HEADER = struct.Struct("4sIh2H")

        with open(file, "rb") as flp:
            stream = io.BytesIO(flp.read())

        events = []
        header = stream.read(FLP_HEADER.size)
        try:
            hdr_magic, hdr_size, fmt, channel_count, ppq = FLP_HEADER.unpack(header)
        except struct.error as exc:
            raise HeaderCorrupted("Couldn't read the header entirely") from exc

        if hdr_magic != b"FLhd":
            raise HeaderCorrupted("Unexpected header chunk magic; expected 'FLhd'")
        if hdr_size != 6:
            raise HeaderCorrupted("Unexpected header chunk size; expected 6")
        try:
            file_format = FileFormat(fmt)
        except ValueError as exc:
            raise HeaderCorrupted("Unsupported project file format") from exc
        if ppq not in VALID_PPQS:
            raise HeaderCorrupted("Invalid PPQ")
        if stream.read(4) != b"FLdt":
            raise HeaderCorrupted("Unexpected data chunk magic; expected 'FLdt'")

        events_size = int.from_bytes(stream.read(4), "little")
        if not events_size:
            raise HeaderCorrupted("Data chunk size couldn't be read")

        stream.seek(0, os.SEEK_END)
        file_size = stream.tell()
        if file_size != events_size + 22:
            raise HeaderCorrupted("Data chunk size corrupted")

        plug_name = None
        str_type = None
        stream.seek(22)
        while stream.tell() < file_size:
            event_type = None
            # Use _missing_ to bypass Python 3.11's "no members" guard
            id = EventEnum._missing_(int.from_bytes(stream.read(1), "little"))

            if id < WORD:
                value = stream.read(1)
            elif id < DWORD:
                value = stream.read(2)
            elif id < TEXT:
                value = stream.read(4)
            else:
                size = c.VarInt.parse_stream(stream)
                value = stream.read(size)

            from pyflp.project import ProjectID
            if id == ProjectID.FLVersion:
                parts = value.decode("ascii").rstrip("\0").split(".")
                if [int(p) for p in parts][0:2] >= [11, 5]:
                    str_type = UnicodeEvent
                else:
                    str_type = AsciiEvent

            for enum_ in EventEnum.__subclasses__():
                if id in enum_:
                    event_type = getattr(enum_(id), "type")
                    break

            if event_type is None:
                if id < WORD:
                    event_type = U8Event
                elif id < DWORD:
                    event_type = U16Event
                elif id < TEXT:
                    event_type = U32Event
                elif id < DATA or id.value in NEW_TEXT_IDS:
                    if str_type is None:
                        raise VersionNotDetected
                    event_type = str_type
                    if id == PluginID.InternalName:
                        plug_name = event_type(id, value).value
                elif id == PluginID.Data and plug_name is not None:
                    event_type = get_event_by_internal_name(plug_name)
                else:
                    event_type = UnknownDataEvent

            events.append(event_type(id, value))

        return Project(
            EventTree(init=(IndexedEvent(r, e) for r, e in enumerate(events))),
            channel_count=channel_count,
            format=file_format,
            ppq=ppq,
        )

    pyflp.parse = _patched_parse
