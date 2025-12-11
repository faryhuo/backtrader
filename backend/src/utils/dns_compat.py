"""
Compatibility shims for aiodns/pycares.

pycares 5.0 removed the legacy `ares_*` result classes and changed Channel
method signatures, while aiodns 3.x still expects the older API. This module
restores the missing classes and wraps Channel methods so aiodns can operate
with newer pycares releases without import or runtime errors.
"""

from __future__ import annotations

import socket
from collections import namedtuple
from typing import Any, Dict, Iterable, Tuple


def _parse_version(version: str) -> Tuple[int, ...]:
    """Convert a semantic version string to a comparable tuple."""
    parts: Iterable[str] = version.split(".")
    parsed = []
    for part in parts:
        try:
            parsed.append(int(part))
        except ValueError:
            parsed.append(0)
    return tuple(parsed)


def ensure_aiodns_pycares_compat() -> None:
    """
    Backfill pycares 5.x API changes for aiodns 3.x consumers.

    - Reintroduces legacy `ares_*` result classes used in type hints/returns.
    - Wraps Channel methods to accept positional callbacks and convert
      DNSResult records into the expected legacy result shapes.
    """
    try:
        import pycares
    except ImportError:
        return

    if _parse_version(getattr(pycares, "__version__", "0")) < (5, 0):
        return

    # Define legacy result containers if missing.
    def _define(name: str, fields: str):
        if not hasattr(pycares, name):
            setattr(pycares, name, namedtuple(name, fields))
        return getattr(pycares, name)

    # Query result classes
    AResult = _define("ares_query_a_result", "host ttl type")
    AAAAResult = _define("ares_query_aaaa_result", "host ttl type")
    CAAResult = _define("ares_query_caa_result", "flags tag value ttl type")
    CNameResult = _define("ares_query_cname_result", "cname ttl type")
    MXResult = _define("ares_query_mx_result", "host priority ttl type")
    NAPTRResult = _define(
        "ares_query_naptr_result",
        "order preference flags service regexp replacement ttl type",
    )
    NSResult = _define("ares_query_ns_result", "host ttl type")
    PTRResult = _define("ares_query_ptr_result", "host ttl type")
    SOAResult = _define(
        "ares_query_soa_result",
        "nsname hostmaster serial refresh retry expires minttl ttl type",
    )
    SRVResult = _define("ares_query_srv_result", "host port priority weight ttl type")
    TXTResult = _define("ares_query_txt_result", "text ttl type")

    # gethostbyname/getaddrinfo helpers
    HostResult = _define("ares_host_result", "name aliases addresses")
    AddrInfoNode = _define(
        "ares_addrinfo_node_result", "ttl flags family socktype protocol addr"
    )
    AddrInfoResult = _define("ares_addrinfo_result", "cnames nodes")
    NameInfoResult = _define("ares_nameinfo_result", "name service")

    def _record_to_legacy(record: Any) -> Any:
        """Convert pycares.DNSRecord to legacy ares_query_* result."""
        rtype = getattr(record, "type", None)
        data = getattr(record, "data", None)
        ttl = getattr(record, "ttl", 0)

        if data is None or rtype is None:
            return record

        if rtype == getattr(pycares, "QUERY_TYPE_A", None):
            return AResult(host=getattr(data, "addr", None), ttl=ttl, type=rtype)
        if rtype == getattr(pycares, "QUERY_TYPE_AAAA", None):
            return AAAAResult(host=getattr(data, "addr", None), ttl=ttl, type=rtype)
        if rtype == getattr(pycares, "QUERY_TYPE_CAA", None):
            return CAAResult(
                flags=getattr(data, "flags", None),
                tag=getattr(data, "tag", None),
                value=getattr(data, "value", None),
                ttl=ttl,
                type=rtype,
            )
        if rtype == getattr(pycares, "QUERY_TYPE_CNAME", None):
            return CNameResult(
                cname=getattr(data, "cname", None), ttl=ttl, type=rtype
            )
        if rtype == getattr(pycares, "QUERY_TYPE_MX", None):
            return MXResult(
                host=getattr(data, "exchange", None),
                priority=getattr(data, "priority", None),
                ttl=ttl,
                type=rtype,
            )
        if rtype == getattr(pycares, "QUERY_TYPE_NAPTR", None):
            return NAPTRResult(
                order=getattr(data, "order", None),
                preference=getattr(data, "preference", None),
                flags=getattr(data, "flags", None),
                service=getattr(data, "service", None),
                regexp=getattr(data, "regexp", None),
                replacement=getattr(data, "replacement", None),
                ttl=ttl,
                type=rtype,
            )
        if rtype == getattr(pycares, "QUERY_TYPE_NS", None):
            host = getattr(data, "nsdname", None) or getattr(data, "nsname", None)
            return NSResult(host=host, ttl=ttl, type=rtype)
        if rtype == getattr(pycares, "QUERY_TYPE_PTR", None):
            host = getattr(data, "ptrdname", None) or getattr(data, "dname", None)
            return PTRResult(host=host, ttl=ttl, type=rtype)
        if rtype == getattr(pycares, "QUERY_TYPE_SOA", None):
            return SOAResult(
                nsname=getattr(data, "mname", None),
                hostmaster=getattr(data, "rname", None),
                serial=getattr(data, "serial", None),
                refresh=getattr(data, "refresh", None),
                retry=getattr(data, "retry", None),
                expires=getattr(data, "expire", None),
                minttl=getattr(data, "minimum", None),
                ttl=ttl,
                type=rtype,
            )
        if rtype == getattr(pycares, "QUERY_TYPE_SRV", None):
            return SRVResult(
                host=getattr(data, "target", None),
                port=getattr(data, "port", None),
                priority=getattr(data, "priority", None),
                weight=getattr(data, "weight", None),
                ttl=ttl,
                type=rtype,
            )
        if rtype == getattr(pycares, "QUERY_TYPE_TXT", None):
            raw_text = getattr(data, "data", None)
            if raw_text is None:
                texts = []
            elif isinstance(raw_text, (list, tuple)):
                texts = [
                    t.decode(errors="ignore") if isinstance(t, (bytes, bytearray)) else str(t)
                    for t in raw_text
                ]
            else:
                texts = [
                    raw_text.decode(errors="ignore")
                    if isinstance(raw_text, (bytes, bytearray))
                    else str(raw_text)
                ]
            return TXTResult(text=texts, ttl=ttl, type=rtype)

        return record

    def _addresses_from_dnsresult(result: Any, port: int) -> list:
        """Extract address tuples from DNSResult answers."""
        addresses = []
        answers = getattr(result, "answer", []) or []
        for rec in answers:
            addr = getattr(getattr(rec, "data", None), "addr", None)
            if not addr:
                continue
            if ":" in addr:
                addresses.append((addr, port, 0, 0))
            else:
                addresses.append((addr, port))
        return addresses

    OriginalChannel = pycares.Channel

    class CompatChannel(OriginalChannel):  # type: ignore[misc]
        """Adapt pycares 5.x Channel to the API shape aiodns 3.x expects."""

        def query(
            self,
            name: str,
            query_type: int,
            callback,
            query_class: int | None = None,
        ) -> None:
            def _cb(result: Any, err: int | None) -> None:
                if err is None and isinstance(result, pycares.DNSResult):
                    legacy = [_record_to_legacy(rec) for rec in result.answer]
                    callback(legacy, err)
                else:
                    callback(result, err)

            return super().query(
                name,
                query_type,
                query_class=query_class or getattr(pycares, "QUERY_CLASS_IN", 1),
                callback=_cb,
            )

        def getaddrinfo(
            self,
            host: str,
            port: int,
            callback,
            family: socket.AddressFamily = socket.AF_UNSPEC,
            type: int = 0,
            proto: int = 0,
            flags: int = 0,
        ) -> None:
            def _cb(result: Any, err: int | None) -> None:
                if err is None and isinstance(result, pycares.DNSResult):
                    nodes = []
                    for addr in _addresses_from_dnsresult(result, port):
                        nodes.append(
                            AddrInfoNode(
                                ttl=getattr(result, "ttl", 0),
                                flags=flags,
                                family=family,
                                socktype=type,
                                protocol=proto,
                                addr=addr,
                            )
                        )
                    callback(AddrInfoResult(cnames=[], nodes=nodes), err)
                else:
                    callback(result, err)

            return super().getaddrinfo(
                host,
                port,
                family=family,
                type=type,
                proto=proto,
                flags=flags,
                callback=_cb,
            )

        def gethostbyname(self, name: str, family: socket.AddressFamily, callback) -> None:
            def _cb(result: Any, err: int | None) -> None:
                if err is None and isinstance(result, pycares.DNSResult):
                    addresses = [
                        addr[0] if isinstance(addr, tuple) else addr
                        for addr in _addresses_from_dnsresult(result, port=0)
                    ]
                    callback(HostResult(name=name, aliases=[], addresses=addresses), err)
                else:
                    callback(result, err)

            return self.getaddrinfo(
                name,
                0,
                _cb,
                family=family,
                type=0,
                proto=0,
                flags=0,
            )

        def getnameinfo(self, sockaddr: Any, flags: int, callback) -> None:
            return super().getnameinfo(sockaddr, flags, callback=callback)

        def gethostbyaddr(self, name: str, callback) -> None:
            return super().gethostbyaddr(name, callback=callback)

    pycares.Channel = CompatChannel  # type: ignore[assignment]


__all__: Tuple[str, ...] = ("ensure_aiodns_pycares_compat",)
