import calendar
from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Trip


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, trips):
        trips_per_day = trips.filter(start_date__day=day)
        d = ''
        for trip in trips_per_day:
            d += f'<li> {trip.title}, Ends on: {trip.end_date.strftime('%d-%m-%Y')} </li>'

        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"

        return '<td></td>'

    def formatweek(self, theweek, trips):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, trips)
        return f'<tr> {week} </tr>'

    def formatmonthname(self, theyear, themonth, withyear=True):
        """Return a month's name."""
        s = f'<div class="calendar-navigation"><a href="?month={themonth - 1}&year={theyear}" class="btn btn-secondary float-left">&lt; Previous Month</a>'
        if withyear:
            s += f"{calendar.month_name[themonth]} {theyear}"
        else:
            s += calendar.month_name[themonth]
        # Add navigation buttons here
        s += f'<a href="?month={themonth + 1}&year={theyear}" class="btn btn-secondary float-right">Next Month &gt;</a></div>'
        return s

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        trips = Trip.objects.filter(start_date__year=self.year, start_date__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, trips)}\n'
        return cal