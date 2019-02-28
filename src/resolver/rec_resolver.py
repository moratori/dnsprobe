#!/usr/bin/env python

import dns.resolver
from logging import getLogger

LOGGER = getLogger(__name__)


class FullResolver(object):

    """
    指定されたフルリゾルバのいずれかを用いて名前解決を行う
    解決したいRTYPE毎にメソッドを実装する

    """

    def __init__(self, resolvers):
        """
        コンストラクタ

        Parameters
        ----------
        resolvers : list
            フルリゾルバのIPアドレスを表らす文字列のリスト
        """

        self.resolvers = resolvers
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = self.resolvers
        LOGGER.debug("resolver initialized for %s" % (self.resolvers))

    def resolve_a(self, domain):
        """
        ドメイン名のIPv4アドレスを解決して返す

        Returns
        -------
        ipv4addresses : list
            IPv4アドレスの文字列リスト
        """

        ipv4addresses = []

        try:
            LOGGER.debug("trying resolve A record for %s" % (domain))
            answer = self.resolver.query(domain, "A")
            for rr in answer:
                ipv4addresses.append(rr.to_text())
            return ipv4addresses
        except Exception as ex:
            LOGGER.warning("exception occurred while resolve A record: %s" %
                           (str(ex)))

        return ipv4addresses

    def resolve_aaaa(self, domain):
        """
        ドメイン名のIPv6アドレスを解決して返す

        Returns
        -------
        ipv6addresses : list
            IPv6アドレスの文字列リスト
        """

        ipv6addresses = []

        try:
            LOGGER.debug("trying resolve AAAA record for %s" % (domain))
            answer = self.resolver.query(domain, "AAAA")
            for rr in answer:
                ipv6addresses.append(rr.to_text())
            return ipv6addresses
        except Exception as ex:
            LOGGER.warning("exception occurred while resolve AAAA record: %s" %
                           (str(ex)))

        return ipv6addresses
