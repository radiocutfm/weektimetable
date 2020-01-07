# -*- coding: utf-8 -*-
__version__ = "0.0.1"

import datetime
import unicodedata

import pytz
import six


class ParseException(Exception):
    pass


class InvalidScheduleFormat(ParseException):
    pass


class DayNotDefinedError(ParseException):
    pass


class InvalidTimeFormat(ParseException):
    pass


class WeekTimetable(object):
    """
    Represents a weekly timetable like 'Mon-Wed 8-10'
    """

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    textDaysByNumber = {
        'Lunes': MONDAY, 'Martes': TUESDAY, 'Miercoles': WEDNESDAY, 'Jueves': THURSDAY,
        'Viernes': FRIDAY, 'Sabado': SATURDAY, 'Domingo': SUNDAY,
        'Monday': MONDAY, 'Tuesday': TUESDAY, 'Wednesday': WEDNESDAY, 'Thursday': THURSDAY,
        'Friday': FRIDAY, 'Saturday': SATURDAY, 'Sunday': SUNDAY
    }

    def __init__(self, timeRanges, timezone=None):
        self._timeRanges = timeRanges
        self.timezone = timezone or pytz.UTC

    @classmethod
    def parse(cls, timetable, timezone=None):
        """Procesa un string con horarios, ej.: Lun-Vie 9-19 / Dom,Sab 8-20 / Lun 21-22
            Devuelve un dict con las horas de inicio y fin por dia de semnana
            {dia de semana: [(datetime.time, datetime.time), ...], ... }
        """
        timeranges = {cls.MONDAY: [],
                      cls.TUESDAY: [],
                      cls.WEDNESDAY: [],
                      cls.THURSDAY: [],
                      cls.FRIDAY: [],
                      cls.SATURDAY: [],
                      cls.SUNDAY: []}

        hoursPerDayOptions = timetable.split(' / ')

        for hoursPerDayOption in hoursPerDayOptions:
            hoursPerDayOption = hoursPerDayOption.split(' ')
            if len(hoursPerDayOption) > 1:
                rangesDays = hoursPerDayOption[0]
                rangesHours = hoursPerDayOption[1]
                rangesDays = cls._parseRangesDays(rangesDays)
                rangesHours = cls._parseRangesHours(rangesHours)
                for day in rangesDays:
                    if rangesHours not in timeranges[day]:
                        timeranges[day].append(rangesHours)
            else:
                raise InvalidScheduleFormat(
                    "Formato de horarios incorrecto. Esperado '<Dia(s)> <Horas>', recibido '{}'".format(
                        hoursPerDayOption
                    )
                )

        timezone = timezone or pytz.UTC
        if isinstance(timezone, six.string_types):
            timezone = pytz.timezone(timezone)
        return cls(timeranges, timezone)

    @classmethod
    def _parseRangesDays(cls, rangesDays):
        """Recibe un rango de días en texto y lo transforma en una tupla de días.
        ejemplo: Lun-Vie -> [0, 1, 2, 3, 4]
                 Dom, Sab -> [6, 5]
                 Lun -> [1]"""
        ret = []

        if '-' in rangesDays:
            # caso: "Lun-Vie", "Mar-Jue"
            rangesDays = rangesDays.split('-')
            firstWeekNumber = cls._getWeekNumber(rangesDays[0])
            secondWeekNumber = cls._getWeekNumber(rangesDays[1])
            if firstWeekNumber < secondWeekNumber:
                ret = range(firstWeekNumber, secondWeekNumber + 1)
            elif firstWeekNumber > secondWeekNumber:
                ret = range(firstWeekNumber, secondWeekNumber + 7 + 1)
                ret = map(lambda x: x if x - 7 < 0 else x - 7, ret)
            else:
                # "Lun-Lun" da todos los días
                ret = range(cls.MONDAY, cls.SUNDAY + 1)
            ret = list(ret)
        elif ',' in rangesDays:
            # caso: "Sab,Dom", "Lun,Mie"
            rangesDays = rangesDays.split(',')
            for textDay in rangesDays:
                weekNumber = cls._getWeekNumber(textDay)
                ret.append(weekNumber)
        else:
            # caso: "Lun", "Mie"
            textDay = rangesDays
            weekNumber = cls._getWeekNumber(textDay)
            ret.append(weekNumber)
        return ret

    @classmethod
    def _remove_accents(cls, cadena):
        # http://guimi.net/blogs/hiparco/funcion-para-eliminar-acentos-en-python/
        return u''.join(c for c in unicodedata.normalize(u'NFD', six.text_type(cadena))
                        if unicodedata.category(c) != u'Mn')

    @classmethod
    def _getWeekNumber(cls, textDay):
        textDay = cls._remove_accents(textDay)
        day = [day for day in cls.textDaysByNumber.keys()
               if day.lower() == textDay.lower() or day.lower()[:3] == textDay.lower()]
        if not day:
            raise DayNotDefinedError(u"El Día '%s' no está definido." % textDay)
        return cls.textDaysByNumber[day[0]]

    @classmethod
    def _parseRangesHours(cls, rangesHours):
        """Recibe un rango de horas en texto y devuelve una tupla con el rango de horas.
           Las horas serían objetos datetime.time
           Ejemplos: 9-19 -> (datetime.time(9,0), datetime.time(19, 0))
           9:30-12:30 -> (datetime.time(9,30), datetime.time(12,30))"""
        rangesHours = rangesHours.split('-')
        if len(rangesHours) != 2:
            raise InvalidTimeFormat("El formato de la hora es incorrecto, es <hora-desde>-<hora-hasta>")

        try:
            hourFrom = rangesHours[0].split(':')
            if len(hourFrom) > 1:
                hourFrom = datetime.time(int(hourFrom[0]), int(hourFrom[1]))
            elif len(hourFrom) > 0:
                hourFrom = datetime.time(int(hourFrom[0]))
            hourTo = rangesHours[1].split(':')
            if len(hourTo) > 1:
                hourTo = datetime.time(int(hourTo[0]), int(hourTo[1]))
            elif len(hourTo) > 0:
                hourTo = datetime.time(int(hourTo[0]))
            ret = (hourFrom, hourTo)
        except ValueError as e:
            raise InvalidTimeFormat("El formato de la hora es incorrecto. Descripción del Error: %s" % e)
        return ret

    def inTimeTable(self, now=None):
        if not now:
            now = datetime.datetime.now(self.timezone)
        else:
            if now.tzinfo:
                now = now.astimezone(self.timezone)
            else:
                now = self.timezone.localize(now)

        weekday = now.weekday()
        hour = now.time()
        timeRanges = self._timeRanges.get(weekday, [])
        prev_weekday = 6 if weekday - 1 < 0 else weekday - 1
        over_midnight_range = [x for x in self._timeRanges.get(prev_weekday, []) if x[0] > x[1]]

        # Search in current day
        for (f, t) in timeRanges:
            if f < t:
                if hour >= f and hour < t:
                    return True
            else:
                if hour >= f and hour > t:
                    return True

        # Search in previous day
        for (f, t) in over_midnight_range:
            if hour < f and hour <= t:
                return True

        return False

    def overlaps(self, other):
        """Checks for any intersection of the hours indicated by the schedules"""
        if self.timezone != other.timezone:
            raise RuntimeError("Only supported same timezone")

        schedules = self._timeRanges
        otherSchedules = other._timeRanges
        for k in schedules:
            for t in schedules[k]:
                for p in otherSchedules[k]:
                    if t == p:
                        return True
                    elif (t[0] > p[0] and t[0] < p[1]) or (t[1] > p[0] and t[1] < p[1]):
                        return True
                    elif (t[0] == p[1] and t[1] > p[0] and t[1] < p[1]) or \
                            (t[1] == p[0] and t[0] > p[0] and t[0] < p[1]):
                        return True
        return False
