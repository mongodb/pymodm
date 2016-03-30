# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#            this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#            notice, this list of conditions and the following disclaimer in the
#                   documentation and/or other materials provided with
#                           the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be
#            used to endorse or promote products derived from this software
#                   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import re

from bson.tz_util import utc, FixedOffset

DATETIME_PATTERN = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'  # YY-MM-DD
    r'(?:[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'  # Optional HH:mm
    r'(?::(?P<second>\d{1,2})'  # Optional seconds
    r'(?:\.(?P<microsecond>\d{1,6})0*)?)?)?'  # Optional microseconds
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?\Z'  # Optional timezone
)


# This section is largely taken from django.util.dateparse.parse_datetime.
def parse_datetime(string):
    """Try to parse a `datetime.datetime` out of a string.

    Return the parsed datetime, or ``None`` if unsuccessful.
    """
    match = re.match(DATETIME_PATTERN, string)
    if match:
        time_parts = match.groupdict()
        if time_parts['microsecond'] is not None:
            time_parts['microsecond'] = (
                time_parts['microsecond'].ljust(6, '0'))
        tzinfo = time_parts.pop('tzinfo')
        if 'Z' == tzinfo:
            tzinfo = utc
        elif tzinfo is not None:
            offset_hours = int(tzinfo[1:3])
            offset_minutes = int(tzinfo[4:]) if len(tzinfo) > 3 else 0
            offset_total = offset_hours * 60 + offset_minutes
            sign = '+'
            if '-' == tzinfo[0]:
                offset_total *= -1
                sign = '-'
            offset_name = '%s%02d:%02d' % (
                sign, offset_hours, offset_minutes)
            tzinfo = FixedOffset(offset_total, offset_name)
        time_parts = {k: int(time_parts[k]) for k in time_parts
                      if time_parts[k] is not None}
        time_parts['tzinfo'] = tzinfo
        return datetime.datetime(**time_parts)
