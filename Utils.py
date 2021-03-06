import datetime
import base64
from dateutil.relativedelta import relativedelta
from datetime import date
import pandas as pd


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_first_saturday_of_month(year, month):
    d = datetime.datetime(year, month, 1)
    return next_weekday(d, 5)  # 0 = Monday, 1=Tuesday, 2=Wednesday...


def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))


def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')


def get_dates_from_today():
    today = date.today()
    one_month_ago = today - relativedelta(months=1)
    three_month_ago = today - relativedelta(months=3)
    six_month_ago = today - relativedelta(months=6)
    nine_month_ago = today - relativedelta(months=9)
    one_year_ago = today - relativedelta(months=12)
    return today, one_month_ago, three_month_ago, six_month_ago, nine_month_ago, one_year_ago


def get_last_date_from_dataframe(data, col_name):
    return pd.to_datetime(data[col_name].iloc[len(data)-1])
