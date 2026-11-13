#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사주 만세력 계산기 (의존성 없음, Python 3.8+).

예)
  python3 saju_calc.py --date 2000-01-01 --time 12:00 --gender f
  python3 saju_calc.py --date 1999-11-25 --lunar --time 08:10 --gender m
  python3 saju_calc.py --date 2000-01-01 --gender f            # 시간 모름
  python3 saju_calc.py --date 2000-01-01 --time 13:30 --gender f --lon 126.98

결과는 JSON. 절기 시각은 약 ±15분, 음력 변환은 천문 계산(1900~2100년 대부분 일치).
"""
import argparse
import datetime as dt
import json
import math
import sys

S = "甲乙丙丁戊己庚辛壬癸"
B = "子丑寅卯辰巳午未申酉戌亥"
SK = "갑을병정무기경신임계"
BK = "자축인묘진사오미신유술해"
EL = "木火土金水"
ELK = ["나무", "불", "흙", "쇠", "물"]
BR_EL = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
HIDDEN = {  # 여기 · 중기 · 정기(마지막이 본기)
    "子": "壬癸", "丑": "癸辛己", "寅": "戊丙甲", "卯": "甲乙", "辰": "乙癸戊", "巳": "戊庚丙",
    "午": "丙己丁", "未": "丁乙己", "申": "戊壬庚", "酉": "庚辛", "戌": "辛丁戊", "亥": "戊甲壬",
}
TWELVE = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]
BIRTH_BR = {"甲": 11, "丙": 2, "戊": 2, "庚": 5, "壬": 8, "乙": 6, "丁": 9, "己": 9, "辛": 0, "癸": 3}
NAEUM = ["해중금", "노중화", "대림목", "노방토", "검봉금", "산두화", "간하수", "성두토", "백랍금", "양류목",
         "천중수", "옥상토", "벽력화", "송백목", "장류수", "사중금", "산하화", "평지목", "벽상토", "금박금",
         "복등화", "천하수", "대역토", "차천금", "상자목", "대계수", "사중토", "천상화", "석류목", "대해수"]
JEOLGI = {315: "입춘", 330: "우수", 345: "경칩", 0: "춘분", 15: "청명", 30: "곡우", 45: "입하", 60: "소만",
          75: "망종", 90: "하지", 105: "소서", 120: "대서", 135: "입추", 150: "처서", 165: "백로", 180: "추분",
          195: "한로", 210: "상강", 225: "입동", 240: "소설", 255: "대설", 270: "동지", 285: "소한", 300: "대한"}
TEN = [["비견", "겁재"], ["식신", "상관"], ["편재", "정재"], ["편관", "정관"], ["편인", "정인"]]


def gz(i):
    return S[i % 10] + B[i % 12]


def gzk(i):
    return SK[i % 10] + BK[i % 12]


def jdn(y, m, d):
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045


def delta_t(year):
    if year < 1950:
        return 29.0
    if year < 2000:
        return 29.0 + (year - 1950) * 0.7
    return 64.0 + (year - 2000) * 0.3


EPOCH = dt.datetime(2000, 1, 1, 12)


def jd_tt(utc):
    return 2451545.0 + (utc - EPOCH).total_seconds() / 86400 + delta_t(utc.year) / 86400


def utc_from_jd_tt(jd):
    t = EPOCH + dt.timedelta(days=jd - 2451545.0)
    return t - dt.timedelta(seconds=delta_t(t.year))


def sunlon(jd):
    T = (jd - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M) + 0.000289 * math.sin(3 * M))
    om = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(om)) % 360


def cross(target, guess):
    jd = guess
    for _ in range(8):
        jd += ((target - sunlon(jd) + 180) % 360 - 180) / 0.985647
    return jd


def new_moon(k):
    T = k / 1236.85
    jde = 2451550.09766 + 29.530588861 * k + 0.00015437 * T * T - 0.000000150 * T ** 3
    E = 1 - 0.002516 * T - 0.0000074 * T * T
    M = math.radians(2.5534 + 29.10535670 * k - 0.0000014 * T * T)
    Mp = math.radians(201.5643 + 385.81693528 * k + 0.0107582 * T * T)
    F = math.radians(160.7108 + 390.67050284 * k - 0.0016118 * T * T)
    Om = math.radians(124.7746 - 1.56375588 * k + 0.0020672 * T * T)
    s = math.sin
    jde += (-0.40720 * s(Mp) + 0.17241 * E * s(M) + 0.01608 * s(2 * Mp) + 0.01039 * s(2 * F)
            + 0.00739 * E * s(Mp - M) - 0.00514 * E * s(Mp + M) + 0.00208 * E * E * s(2 * M)
            - 0.00111 * s(Mp - 2 * F) - 0.00057 * s(Mp + 2 * F) + 0.00056 * E * s(2 * Mp + M)
            - 0.00042 * s(3 * Mp) + 0.00042 * E * s(M + 2 * F) + 0.00038 * E * s(M - 2 * F)
            - 0.00024 * E * s(2 * Mp - M) - 0.00017 * s(Om))
    return jde


KST = dt.timedelta(hours=9)


def nm_date(k):
    return (utc_from_jd_tt(new_moon(k)) + KST).date()


def lon_at_midnight(d):
    return sunlon(jd_tt(dt.datetime(d.year, d.month, d.day) - KST))


def has_zhongqi(k):
    """k번째 삭으로 시작하는 달에 중기(中氣)가 드는지. 날짜(한국 자정) 기준."""
    s, e = nm_date(k), nm_date(k + 1)
    return int(lon_at_midnight(s) // 30) != int(lon_at_midnight(e) // 30)


def dongji_k(year):
    """그 해 동지가 드는 음력 달(= 음력 11월)의 삭 번호."""
    jd = cross(270.0, jdn(year, 12, 21) + 0.5)
    d = (utc_from_jd_tt(jd) + KST).date()
    k0 = int(math.floor((jdn(d.year, d.month, d.day) - 2451550.1) / 29.530588861))
    return max(kk for kk in range(k0 - 2, k0 + 3) if nm_date(kk) <= d)


def lunar_from_solar(d):
    """양력 날짜 -> (음력 년, 월, 일, 윤달 여부). 동지를 11월로 고정하고,
    두 동지 사이가 13달이면 중기 없는 첫 달을 윤달로 둔다."""
    jd = jdn(d.year, d.month, d.day)
    k0 = int(math.floor((jd - 2451550.1) / 29.530588861))
    k = max(kk for kk in range(k0 - 2, k0 + 3) if nm_date(kk) <= d)
    Y = d.year
    if k >= dongji_k(Y):
        Y += 1
    ka, kb = dongji_k(Y - 1), dongji_k(Y)
    i = k - ka
    leap_at = None
    if kb - ka == 13:
        for j in range(1, 13):
            if not has_zhongqi(ka + j):
                leap_at = j
                break
    if leap_at is None or i < leap_at:
        m, leap = (10 + i) % 12 + 1, False
    elif i == leap_at:
        m, leap = (10 + i - 1) % 12 + 1, True
    else:
        m, leap = (10 + i - 1) % 12 + 1, False
    y = Y - 1 if (m >= 11 and i <= 2) else Y
    return y, m, (d - nm_date(k)).days + 1, leap


def solar_from_lunar(y, m, day, leap):
    d = dt.date(y, 1, 1)
    end = dt.date(y + 1, 3, 15)
    while d <= end:
        if lunar_from_solar(d) == (y, m, day, leap):
            return d
        d += dt.timedelta(days=1)
    raise SystemExit("해당 음력 날짜를 찾지 못했습니다: %d-%d-%d%s" % (y, m, day, " 윤달" if leap else ""))


def ten_god(dm, s):
    rel = (s // 2 - dm // 2) % 5
    return TEN[rel][0 if dm % 2 == s % 2 else 1]


def twelve(stem, br):
    start = BIRTH_BR[S[stem]]
    step = (br - start) % 12 if stem % 2 == 0 else (start - br) % 12
    return TWELVE[step]


def eot_minutes(d):
    n = d.timetuple().tm_yday
    b = math.radians(360 / 365 * (n - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def clock_rules(t):
    """(UTC 오프셋 시간, 표준 자오선, 서머타임 여부, 경고)"""
    warn = []
    off, mer, dst = 9.0, 135.0, False
    d = t.date()
    if dt.date(1954, 3, 21) <= d <= dt.date(1961, 8, 9):
        off, mer = 8.5, 127.5
        warn.append("1954~1961년은 한국 표준시가 UTC+8:30(동경 127.5도)이던 시기입니다. 그에 맞춰 계산했습니다.")
    if d.year < 1912:
        warn.append("1912년 이전 출생은 당시 표준시가 달라 시주가 틀릴 수 있습니다.")
    for a, b in ((dt.date(1987, 5, 10), dt.date(1987, 10, 11)), (dt.date(1988, 5, 8), dt.date(1988, 10, 9))):
        if a <= d < b:
            dst = True
            warn.append("서머타임 기간(1987~1988년 여름) 출생이라 시계 시각에서 1시간을 뺐습니다.")
    if d.year in (1948, 1949, 1950, 1951, 1955, 1956, 1957, 1958, 1959, 1960) and 5 <= d.month <= 9:
        warn.append("이 해 여름에는 서머타임이 시행된 기간이 있습니다. 해당되면 시각에서 1시간을 빼고 다시 계산하세요.")
    return off, mer, dst, warn


def hour_calc(t, mode, lon, mer, dst):
    """시주용 기준 시각. kr30: 표준 자오선이 135도일 때 30분 보정. solar: 진태양시."""
    base = t - dt.timedelta(hours=1) if dst else t
    if mode == "solar":
        eff = base + dt.timedelta(minutes=4 * (lon - mer) + eot_minutes(base.date()))
    else:
        eff = base - dt.timedelta(minutes=30 if mer == 135.0 else 0)
    br = ((eff.hour + 1) // 2) % 12
    day = eff.date() + dt.timedelta(days=1 if eff.hour >= 23 else 0)
    m = eff.hour * 60 + eff.minute + eff.second / 60
    dist = min(abs(m - b) for b in [60 * h for h in range(-1, 26, 2)])
    return br, day, eff, dist


SAMHAP = {"申子辰": ("酉", "寅", "辰"), "寅午戌": ("卯", "申", "戌"), "巳酉丑": ("午", "亥", "丑"), "亥卯未": ("子", "巳", "未")}
CHEONEUL = {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申", "丙": "亥酉", "丁": "亥酉", "辛": "午寅", "壬": "巳卯", "癸": "巳卯"}
MUNCHANG = dict(zip(S, "巳午申酉申酉亥子寅卯"))
AMROK = dict(zip(S, "亥戌申未申未巳辰寅丑"))
HONGYEOM = dict(zip(S, "午午寅未辰辰戌酉子申"))
YANGIN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
GEONROK = dict(zip(S, "寅卯巳午巳午申酉亥子"))
CHEONDEOK = dict(zip("寅卯辰巳午未申酉戌亥子丑", "丁申壬辛亥甲癸寅丙乙巳庚"))
WOLDEOK = {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬", "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}
BAEKHO = {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}
GOEGANG = {"庚辰", "庚戌", "壬辰", "壬戌", "戊戌"}
PAIRS = {
    "육합": ["子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"],
    "충": ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"],
    "형": ["寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未", "子卯"],
    "파": ["子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌"],
    "해": ["子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌"],
    "원진": ["子未", "丑午", "寅酉", "卯申", "辰亥", "巳戌"],
    "귀문": ["子酉", "丑午", "寅未", "卯申", "辰亥", "巳戌"],
}
STEM_PAIRS = {"합": ["甲己", "乙庚", "丙辛", "丁壬", "戊癸"], "충": ["甲庚", "乙辛", "丙壬", "丁癸"]}


def group_of(br):
    for g in SAMHAP:
        if br in g:
            return g
    return None


def analyze(pillars, names):
    """pillars: [(stem_idx, branch_idx)] 년·월·일·(시) 순서."""
    dm = pillars[2][0]
    dms = S[dm]
    stems = [S[p[0]] for p in pillars]
    brs = [B[p[1]] for p in pillars]
    sinsal, rel = [], []

    def add(name, where, note=""):
        sinsal.append({"name": name, "where": where, "note": note})

    for i, b in enumerate(brs):
        if b in CHEONEUL[dms]:
            add("천을귀인", names[i] + "지 " + b)
        if b == MUNCHANG[dms]:
            add("문창귀인", names[i] + "지 " + b)
        if b == B[BIRTH_BR[dms]]:
            add("학당귀인", names[i] + "지 " + b)
        if b == AMROK[dms]:
            add("암록", names[i] + "지 " + b)
        if b == HONGYEOM[dms]:
            add("홍염", names[i] + "지 " + b)
        if b == YANGIN.get(dms):
            add("양인", names[i] + "지 " + b)
        if b == GEONROK[dms]:
            add("건록", names[i] + "지 " + b)
    mb = brs[1]
    for i, s in enumerate(stems):
        if s == CHEONDEOK[mb]:
            add("천덕귀인", names[i] + "간 " + s)
        if s == WOLDEOK[mb]:
            add("월덕귀인", names[i] + "간 " + s)
    for i, b in enumerate(brs):
        if b == CHEONDEOK[mb] and i != 1:
            add("천덕귀인", names[i] + "지 " + b)
    for i, p in enumerate(pillars):
        g = S[p[0]] + B[p[1]]
        if g in BAEKHO:
            add("백호대살", names[i] + "주 " + g)
        if g in GOEGANG:
            add("괴강살", names[i] + "주 " + g)
    hy = [names[i] + "간 " + s for i, s in enumerate(stems) if s in "甲辛"] + [names[i] + "지 " + b for i, b in enumerate(brs) if b in "卯午未申"]
    if hy:
        add("현침", ", ".join(hy), "글자 수가 많을수록 뚜렷")
    for base_i, base_name in ((0, "년지"), (2, "일지")):
        dohwa, yeokma, hwagae = SAMHAP[group_of(brs[base_i])]
        for i, b in enumerate(brs):
            if i == base_i and b != hwagae:
                continue
            if b == dohwa:
                add("도화", names[i] + "지 " + b, base_name + " 기준")
            if b == yeokma:
                add("역마", names[i] + "지 " + b, base_name + " 기준")
            if b == hwagae:
                add("화개", names[i] + "지 " + b, base_name + " 기준")
    # 순(旬)에 따른 공망
    void = [B[(pillars[2][1] - pillars[2][0] + 10) % 12], B[(pillars[2][1] - pillars[2][0] + 11) % 12]]
    void_hit = [names[i] + "지 " + b for i, b in enumerate(brs) if b in void and i != 2]

    for i in range(len(brs)):
        for j in range(i + 1, len(brs)):
            a, b = brs[i], brs[j]
            where = "%s지 %s – %s지 %s" % (names[i], a, names[j], b)
            adj = "인접" if j - i == 1 else "떨어짐"
            for kind, lst in PAIRS.items():
                if a + b in lst or b + a in lst:
                    rel.append({"type": kind, "where": where, "adjacent": adj})
            if a == b and a in "辰午酉亥":
                rel.append({"type": "자형", "where": where, "adjacent": adj})
            g = group_of(a)
            if a != b and g == group_of(b):
                rel.append({"type": "삼합 반합(%s국)" % EL[{"申子辰": 4, "寅午戌": 1, "巳酉丑": 3, "亥卯未": 0}[g]], "where": where, "adjacent": adj})
    for g, e in (("申子辰", "水"), ("寅午戌", "火"), ("巳酉丑", "金"), ("亥卯未", "木")):
        if all(c in brs for c in g):
            rel.append({"type": "삼합 완성(%s국)" % e, "where": g, "adjacent": ""})
    for g, e in (("寅卯辰", "木"), ("巳午未", "火"), ("申酉戌", "金"), ("亥子丑", "水")):
        if all(c in brs for c in g):
            rel.append({"type": "방합 완성(%s)" % e, "where": g, "adjacent": ""})
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            a, b = stems[i], stems[j]
            for kind, lst in STEM_PAIRS.items():
                if a + b in lst or b + a in lst:
                    rel.append({"type": "천간 " + kind, "where": "%s간 %s – %s간 %s" % (names[i], a, names[j], b), "adjacent": "인접" if j - i == 1 else "떨어짐"})
    return sinsal, rel, void, void_hit


def pillar_dict(name, st, br, dm):
    hid = HIDDEN[B[br]]
    main = S.index(hid[-1])
    return {
        "name": name, "ganzhi": S[st] + B[br], "reading": SK[st] + BK[br],
        "stem": S[st], "stem_element": EL[st // 2], "stem_yinyang": "양" if st % 2 == 0 else "음",
        "branch": B[br], "branch_element": EL[BR_EL[br]], "branch_yinyang": "양" if br % 2 == 0 else "음",
        "stem_ten_god": "일간" if name == "일" else ten_god(dm, st),
        "branch_ten_god": ten_god(dm, main),
        "hidden_stems": [{"stem": h, "ten_god": ten_god(dm, S.index(h))} for h in hid],
        "twelve_stage": twelve(dm, br),
        "naeum": NAEUM[_idx60(st, br) // 2],
    }


def _idx60(st, br):
    for i in range(60):
        if i % 10 == st and i % 12 == br:
            return i
    raise ValueError


def main():
    ap = argparse.ArgumentParser(description="사주 만세력 계산기")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (양력, --lunar를 주면 음력)")
    ap.add_argument("--time", help="HH:MM 24시간제. 모르면 생략")
    ap.add_argument("--gender", required=True, choices=["m", "f"], help="m 남자 / f 여자")
    ap.add_argument("--lunar", action="store_true", help="--date가 음력일 때")
    ap.add_argument("--leap", action="store_true", help="음력 윤달일 때")
    ap.add_argument("--lon", type=float, help="출생지 경도(동경). 주면 진태양시로 시주 계산. 서울 126.98 부산 129.08 대전 127.38 광주 126.85 대구 128.60 제주 126.53")
    ap.add_argument("--from-year", type=int, default=dt.date.today().year, help="세운 시작 연도")
    ap.add_argument("--years", type=int, default=7, help="세운을 몇 해 보여줄지")
    a = ap.parse_args()

    y, m, d = [int(x) for x in a.date.split("-")]
    warnings = []
    if a.lunar:
        sd = solar_from_lunar(y, m, d, a.leap)
    else:
        sd = dt.date(y, m, d)
    ly, lm, ld, lleap = lunar_from_solar(sd)

    has_time = bool(a.time)
    hh, mm = [int(x) for x in a.time.split(":")] if has_time else (12, 0)
    clock = dt.datetime(sd.year, sd.month, sd.day, hh, mm)
    off, mer, dst, w = clock_rules(clock)
    warnings += w
    utc = clock - dt.timedelta(hours=off + (1 if dst else 0))
    jb = jd_tt(utc)
    lon_b = sunlon(jb)

    # 일주·시주
    hour = None
    day_date = sd
    if has_time:
        mode = "solar" if a.lon is not None else "kr30"
        br, day_date, eff, dist = hour_calc(clock, mode, a.lon or 0, mer, dst)
        alt_mode = "kr30" if mode == "solar" else "solar"
        abr, aday, aeff, adist = hour_calc(clock, alt_mode, a.lon if a.lon is not None else 126.98, mer, dst)
        hour = {"branch_idx": br, "basis": "진태양시(경도 %.2f)" % a.lon if mode == "solar" else "한국 만세력 기준(30분 보정)",
                "effective_time": eff.strftime("%H:%M"), "minutes_to_boundary": round(dist, 1)}
        if dist < 20:
            warnings.append("태어난 시각이 시(時)의 경계에서 %.0f분 떨어져 있습니다. 실제 시각이 조금만 달라도 시주가 바뀝니다." % dist)
        if abr != br or aday != day_date:
            other = "진태양시(서울 경도 가정)" if alt_mode == "solar" and a.lon is None else ("진태양시" if alt_mode == "solar" else "한국 만세력 기준(30분 보정)")
            hour["alternative"] = {"basis": other, "branch": B[abr], "effective_time": aeff.strftime("%H:%M")}
            warnings.append("기준에 따라 시주가 달라집니다: %s로는 %s시. 출생 지역을 확인하고 두 경우의 차이를 함께 적으세요." % (other, B[abr]))
        if eff.hour >= 23 or (eff.hour == 0):
            warnings.append("자시(子時) 출생입니다. 밤 11시대 출생은 일주를 다음 날로 넘기는 방식(여기서 사용)과 당일로 두는 야자시 방식이 있습니다. 야자시로 볼 때의 일주는 yajasi_alternative에 있습니다(0시대 출생이면 해당 없음).")
    else:
        warnings.append("태어난 시간을 몰라 시주 없이 세 기둥으로 계산했습니다. 대운 시작 시점은 정오 기준 근사값입니다.")

    di = (jdn(day_date.year, day_date.month, day_date.day) + 49) % 60
    dm = di % 10

    # 년주·월주
    sy = sd.year - 1 if (sd.month <= 2 and 270 <= lon_b < 315) else sd.year
    yi = (sy - 4) % 60
    midx = int(((lon_b - 315) % 360) // 30)
    m_st = ((yi % 10) % 5 * 2 + 2 + midx) % 10
    m_br = (2 + midx) % 12
    mi = _idx60(m_st, m_br)
    prev_t = (315 + 30 * midx) % 360
    next_t = (prev_t + 30) % 360
    jp = cross(prev_t, jb - ((lon_b - prev_t) % 360) / 0.985647)
    jn = cross(next_t, jb + ((next_t - lon_b) % 360) / 0.985647)

    def kst(jd):
        return utc_from_jd_tt(jd) + KST

    for nm_, jj in ((JEOLGI[prev_t], jp), (JEOLGI[next_t], jn)):
        gap = abs(jj - jb) * 1440
        if gap < 30:
            warnings.append("출생 시각이 절기 %s에서 %.0f분 이내입니다. 절기 계산 오차(약 ±15분) 때문에 월주(입춘이면 년주도)가 바뀔 수 있으니 반드시 알리세요." % (nm_, gap))

    names = ["년", "월", "일"] + (["시"] if has_time else [])
    pil = [(yi % 10, yi % 12), (m_st, m_br), (di % 10, di % 12)]
    if has_time:
        hb = hour["branch_idx"]
        pil.append(((dm % 5 * 2 + hb) % 10, hb))
    pillars = [pillar_dict(n, p[0], p[1], dm) for n, p in zip(names, pil)]

    # 오행·음양
    counts = [0] * 5
    yang = 0
    for st, br in pil:
        counts[st // 2] += 1
        counts[BR_EL[br]] += 1
        yang += (st % 2 == 0) + (br % 2 == 0)
    ten_counts = {}
    for p in pillars:
        for t in (p["stem_ten_god"], p["branch_ten_god"]):
            if t != "일간":
                ten_counts[t] = ten_counts.get(t, 0) + 1

    sinsal, rel, void, void_hit = analyze(pil, names)

    # 대운
    forward = ((yi % 10) % 2 == 0) == (a.gender == "m")
    days = (jn - jb) if forward else (jb - jp)
    num = max(1, int(round(days / 3)))
    start = clock + dt.timedelta(days=days / 3 * 365.2422)
    daeun = []
    for k in range(1, 9):
        idx = (mi + k) % 60 if forward else (mi - k) % 60
        st_y = start.year + 10 * (k - 1)
        daeun.append({"ganzhi": gz(idx), "reading": gzk(idx), "stem_ten_god": ten_god(dm, idx % 10),
                      "branch_ten_god": ten_god(dm, S.index(HIDDEN[B[idx % 12]][-1])),
                      "twelve_stage": twelve(dm, idx % 12),
                      "start_year": st_y, "end_year": st_y + 9,
                      "korean_age_start": st_y - sd.year + 1, "korean_age_end": st_y - sd.year + 10})
    seun = []
    for yy in range(a.from_year, a.from_year + a.years):
        idx = (yy - 4) % 60
        seun.append({"year": yy, "ganzhi": gz(idx), "reading": gzk(idx), "korean_age": yy - sd.year + 1,
                     "stem_ten_god": ten_god(dm, idx % 10),
                     "branch_ten_god": ten_god(dm, S.index(HIDDEN[B[idx % 12]][-1])),
                     "twelve_stage": twelve(dm, idx % 12)})

    out = {
        "input": {"date": a.date, "calendar": "음력" + (" 윤달" if a.leap else "") if a.lunar else "양력",
                  "time": a.time or "모름", "gender": "남" if a.gender == "m" else "여"},
        "solar_date": sd.isoformat(), "weekday": "월화수목금토일"[sd.weekday()] + "요일",
        "lunar_date": "%d년 %s%d월 %d일" % (ly, "윤" if lleap else "", lm, ld),
        "zodiac": ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"][yi % 12] + "띠",
        "day_master": {"stem": S[dm], "reading": SK[dm], "element": EL[dm // 2], "element_ko": ELK[dm // 2],
                       "yinyang": "양" if dm % 2 == 0 else "음"},
        "pillars": pillars,
        "hour_basis": {k: v for k, v in hour.items() if k != "branch_idx"} if hour else None,
        "yajasi_alternative": ({"day": gz(di - 1), "day_reading": gzk(di - 1), "hour": pillars[3]["ganzhi"],
                                "note": "야자시 방식: 일주는 당일 그대로, 시주는 같다. 일간이 바뀌므로 십성과 대운 해석이 전부 달라진다."}
                               if has_time and eff.hour >= 23 else None),
        "elements": {EL[i]: counts[i] for i in range(5)},
        "yinyang": {"양": yang, "음": len(pil) * 2 - yang},
        "ten_god_counts": ten_counts,
        "void": {"branches": void, "in_chart": void_hit},
        "sinsal": sinsal,
        "relations": rel,
        "jeolgi": {"prev": {"name": JEOLGI[prev_t], "kst": kst(jp).strftime("%Y-%m-%d %H:%M")},
                   "next": {"name": JEOLGI[next_t], "kst": kst(jn).strftime("%Y-%m-%d %H:%M")},
                   "days_since_prev": round(jb - jp, 2), "days_to_next": round(jn - jb, 2),
                   "note": "절기 시각 오차 약 ±15분"},
        "daeun": {"direction": "순행" if forward else "역행", "number": num, "years_exact": round(days / 3, 2),
                  "first_start": start.strftime("%Y-%m"), "list": daeun,
                  "note": "korean_age는 양력 출생 연도 기준 세는 나이. 사용자가 말한 나이·학년이 있으면 그것을 따른다."},
        "seun": seun,
        "warnings": warnings,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
