import datetime

from faprint import faprint


def georgian_to_hijri(year, month, day):
    from datetime import date as datetime_date

    weekdays = [
        "دو شنبه",
        "سه شنبه",
        "چهار شنبه",
        "پنج شنبه",
        "جمعه",
        "شنبه",
        "یکشنبه",
    ]
    months = [
        "فروردین",
        "اردیبهشت",
        "خرداد",
        "تیر",
        "مرداد",
        "شهریور",
        "مهر",
        "آبان",
        "آذر",
        "دی",
        "بهمن",
        "اسفند",
    ]
    jy, jm, jd = gregorian_to_jalali(year, month, day)
    weekday_index = datetime_date(year, month, day).weekday()
    weekday = weekdays[weekday_index]
    return f"{weekday}  {to_persian_digits(str(jd))}  {months[jm - 1]}  {to_persian_digits(str(jy))}"


def to_persian_digits(s):
    from string import digits as string_digits

    return s.translate(str.maketrans(string_digits, "۰۱۲۳۴۵۶۷۸۹"))


def gregorian_to_jalali(gy, gm, gd):
    g_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_day_no += g_days[gm2] + gd2
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = 1 + j_day_no // 31
        jd = 1 + j_day_no % 31
    else:
        j_day_no -= 186
        jm = 7 + j_day_no // 30
        jd = 1 + j_day_no % 30
    return jy, jm, jd


def get_current_ymd():
    today = datetime.date.today()
    return today.year, today.month, today.day


if __name__ == "__main__":
    y, m, d = get_current_ymd()
    faprint(georgian_to_hijri(y, m, d))
