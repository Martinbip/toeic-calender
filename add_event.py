#!/usr/bin/env python3
"""Thêm / cập nhật sự kiện vào toeic.ics (lịch đăng ký trên iPhone).

Dùng:
  python3 add_event.py event.json
event.json:
  {"uid": "toeic-2026-10-30-sang",          # cùng uid = ghi đè sự kiện cũ
   "start": "2026-10-30T07:45:00",           # giờ Asia/Ho_Chi_Minh
   "end":   "2026-10-30T08:30:00",
   "summary": "📚 TOEIC — Lô #22–#42 + 📐 G1",
   "description": "nội dung nhiều dòng...",
   "alarm_minutes": 0}                       # nhắc trước N phút (tùy chọn)

Sự kiện cũ hơn 45 ngày tự bị xóa để file gọn.
"""
import json, sys, re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ICS = Path(__file__).with_name("toeic.ics")
EVENTS = Path(__file__).with_name("events.json")
TZ = "Asia/Ho_Chi_Minh"
KEEP_DAYS = 45

HEADER = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Martin//TOEIC Calendar//VI",
    "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:TOEIC 800",
    f"X-WR-TIMEZONE:{TZ}", "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
    "X-PUBLISHED-TTL:PT1H",
    "BEGIN:VTIMEZONE", f"TZID:{TZ}", "BEGIN:STANDARD", "DTSTART:19700101T000000",
    "TZOFFSETFROM:+0700", "TZOFFSETTO:+0700", "TZNAME:+07", "END:STANDARD", "END:VTIMEZONE",
]


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def fold(line: str) -> list[str]:
    # RFC 5545: tối đa 75 octet mỗi dòng
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode()) > 75:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return out


def ics_dt(s: str) -> str:
    return re.sub(r"[-:]", "", s)[:15]


def build(events: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = list(HEADER)
    for e in sorted(events, key=lambda x: x["start"]):
        lines += ["BEGIN:VEVENT", f"UID:{e['uid']}@toeic-calender", f"DTSTAMP:{now}",
                  f"DTSTART;TZID={TZ}:{ics_dt(e['start'])}", f"DTEND;TZID={TZ}:{ics_dt(e['end'])}",
                  f"SUMMARY:{esc(e['summary'])}", f"DESCRIPTION:{esc(e.get('description', ''))}"]
        if e.get("alarm_minutes") is not None:
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(e['summary'])}",
                      f"TRIGGER:-PT{int(e['alarm_minutes'])}M", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(l for line in lines for l in fold(line)) + "\r\n"


def main():
    events = json.loads(EVENTS.read_text()) if EVENTS.exists() else []
    if len(sys.argv) > 1:
        new = json.loads(Path(sys.argv[1]).read_text())
        new = new if isinstance(new, list) else [new]
        uids = {n["uid"] for n in new}
        events = [e for e in events if e["uid"] not in uids] + new
    cutoff = (datetime.now() - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    events = [e for e in events if e["start"][:10] >= cutoff]
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=1))
    ICS.write_text(build(events), encoding="utf-8", newline="")
    print(f"{len(events)} sự kiện trong {ICS.name}")


if __name__ == "__main__":
    main()
