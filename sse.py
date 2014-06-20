# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 Andrey Antukh <niwi@niwi.be>

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
    #notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
    #notice, this list of conditions and the following disclaimer in the
    #documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
    #derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import unicode_literals

import functools
import re
import sys


class Sse(object):
    _retry = None
    _buffer = None

    _rx_event = re.compile(r'^add_event_([\w\d\_]+)$', flags=re.U)

    def __init__(self, default_retry=2000):
        self._buffer = []
        self.set_retry(default_retry)

    def set_retry(self, num):
        """
        Set distinct retry timeout instead the default
        value.
        """
        self._retry = num
        self._buffer.append("retry: {0}\n\n".format(self._retry))

    def set_event_id(self, event_id):
        if event_id:
            self._buffer.append("id: {0}\n\n".format(event_id))
        else:
            # Reset event id
            self._buffer.append("id\n\n")

    def reset_event_id(self):
        """
        Send a reset event id.
        """
        self.set_event_id(None)

    def _parse_text(self, text, encoding):
        # parse text if is list, tuple or set instance
        if isinstance(text, (list, tuple, set)):
            for item in text:
                if isinstance(item, bytes):
                    item = item.decode(encoding)

                for subitem in item.splitlines():
                    yield subitem

        else:
            if isinstance(text, bytes):
                text = text.decode(encoding)

            for item in text.splitlines():
                yield item

    def add_message(self, event, text, encoding='utf-8'):
        """
        Add messaget with eventname to the buffer.

        :param str event: event name
        :param str/list text: event content. Must be a str or list of str
        :param bool split: splits str content by lines. default(true)
        """

        self._buffer.append("event: {0}\n".format(event))

        for text_item in self._parse_text(text, encoding):
            self._buffer.append("data: {0}\n".format(text_item))

        self._buffer.append("\n")

    def __getattr__(self, attr):
        """
        Make a dynamic method for add messages to specific events
        like add_event_<eventname>(text="Hello")

        Examples:
            response.add_foo(text="bar")

        This sets event to "foo" and put "bar" as content.
        """

        res = self._rx_event.search(attr)
        if not res:
            return super(Sse, self).__getattr__(attr)
        return functools.partial(self.add_message, event=res.group(1))

    def __str__(self):
        if sys.version_info[0] >= 3: # Python 3
            return self.__unicode__()
        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        return "".join(self._buffer)

    def flush(self):
        """
        Reset the internal buffer to initial state.
        """
        self._buffer = []

    def __iter__(self):
        for item in self._buffer:
            yield item

        self.flush()
