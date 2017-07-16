# coding=utf-8

from __future__ import print_function, division, unicode_literals
import re
from numbers import Number
from .formatbase import FormatBase
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle


class TXTGenericFormat(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if "[Script Info]" in text or "[V4+ Styles]" in text:
            # disambiguation vs. SSA/ASS
            return None

        for line in text.splitlines():
            if len(TIMESTAMP.findall(line)) == 2:
                return "srt"

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        timestamps = [] # (start, end)
        following_lines = [] # contains lists of lines following each timestamp

        for line in fp:
            stamps = TIMESTAMP.findall(line)
            if len(stamps) == 2: # timestamp line
                start, end = map(timestamp_to_ms, stamps)
                timestamps.append((start, end))
                following_lines.append([])
            else:
                if timestamps:
                    following_lines[-1].append(line)

        def prepare_text(lines):
            s = "".join(lines).strip()
            s = re.sub(r"\n+ *\d+ *$", "", s) # strip number of next subtitle
            s = re.sub(r"< *i *>", r"{\i1}", s)
            s = re.sub(r"< */ *i *>", r"{\i0}", s)
            s = re.sub(r"< *s *>", r"{\s1}", s)
            s = re.sub(r"< */ *s *>", r"{\s0}", s)
            s = re.sub(r"< *u *>", "{\\u1}", s) # not r" for Python 2.7 compat, triggers unicodeescape
            s = re.sub(r"< */ *u *>", "{\\u0}", s)
            s = re.sub(r"< */? *[a-zA-Z][^>]*>", "", s) # strip other HTML tags
            s = re.sub(r"\n", r"\N", s) # convert newlines
            return s

        subs.events = [SSAEvent(start=start, end=end, text=prepare_text(lines))
                       for (start, end), lines in zip(timestamps, following_lines)]

    @classmethod
    def to_file(cls, subs, fp, format_, **kwargs):
        def prepare_text(text, style):
            body = []
            for fragment, sty in parse_tags(text, style, subs.styles):
                fragment = fragment.replace(r"\h", " ")
                fragment = fragment.replace(r"\n", "\n")
                fragment = fragment.replace(r"\N", "\n")
                if sty.italic: fragment = "<i>%s</i>" % fragment
                if sty.underline: fragment = "<u>%s</u>" % fragment
                if sty.strikeout: fragment = "<s>%s</s>" % fragment
                body.append(fragment)

            return re.sub("\n+", "\n", "".join(body).strip())

        visible_lines = (line for line in subs if not line.is_comment)

        for i, line in enumerate(visible_lines, 1):
            start = ms_to_timestamp(line.start)
            end = ms_to_timestamp(line.end)
            text = prepare_text(line.text, subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            print("%d" % i, file=fp) # Python 2.7 compat
            print(start, "-->", end, file=fp)
            print(text, end="\n\n", file=fp)
