# models.py
from dataclasses import dataclass, field
from typing import List
from constants import (
    KEY_TITLE, KEY_SUBTITLE, KEY_COMPOSER, KEY_LYRICIST, KEY_ARRANGER,
    KEY_NUMBER, KEY_CHORDS, KEY_MARKERS, KEY_SECTIONS, KEY_JUMPS,
    KEY_BARLINES, KEY_SYSTEM_TEXTS, KEY_VOLTA, KEY_LINE_BREAK, KEY_TIMESIG
)

@dataclass
class Header:
    title: str = ""
    subtitle: str = ""
    composer: str = ""
    lyricist: str = ""
    arranger: str = ""

    def to_dict(self) -> dict:
        d = {KEY_TITLE: self.title}
        if self.subtitle: d[KEY_SUBTITLE] = self.subtitle
        if self.composer: d[KEY_COMPOSER] = self.composer
        if self.lyricist: d[KEY_LYRICIST] = self.lyricist
        if self.arranger: d[KEY_ARRANGER] = self.arranger
        return d

@dataclass
class Bar:
    number: int
    chords: List[str] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    jumps: List[str] = field(default_factory=list)
    barlines: List[str] = field(default_factory=list)
    system_texts: List[str] = field(default_factory=list)
    volta: str = ""
    line_break: bool = False
    timesig: str = ""

    def to_dict(self) -> dict:
        d = {KEY_NUMBER: self.number}
        if self.chords: d[KEY_CHORDS] = self.chords
        if self.markers: d[KEY_MARKERS] = self.markers
        if self.sections: d[KEY_SECTIONS] = self.sections
        if self.jumps: d[KEY_JUMPS] = self.jumps
        if self.barlines: d[KEY_BARLINES] = self.barlines
        if self.system_texts: d[KEY_SYSTEM_TEXTS] = self.system_texts
        if self.volta: d[KEY_VOLTA] = self.volta
        if self.line_break: d[KEY_LINE_BREAK] = True
        if self.timesig: d[KEY_TIMESIG] = self.timesig
        return d