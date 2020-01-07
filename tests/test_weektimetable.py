# -*- coding: utf-8 -*-
import weektimetable
from weektimetable import WeekTimetable
import unittest
import datetime
import pytz


class TestParser(unittest.TestCase):
    def test_remove_accents(self):
        self.assertEqual("Sab", WeekTimetable._remove_accents(u"Sáb"))

    def test_get_week_number(self):
        self.assertEqual(0, WeekTimetable._getWeekNumber("Mon"))
        self.assertEqual(2, WeekTimetable._getWeekNumber(u"Mié"))
        self.assertEqual(3, WeekTimetable._getWeekNumber("Jueves"))
        self.assertEqual(5, WeekTimetable._getWeekNumber("SABADO"))
        with self.assertRaises(weektimetable.DayNotDefinedError):
            WeekTimetable._getWeekNumber("Saraza")

    def test_parse_ranges_days(self):
        self.assertEqual([0, 1, 2], WeekTimetable._parseRangesDays("Mon-Wed"))
        self.assertEqual([2, 4], WeekTimetable._parseRangesDays("Wed,Friday"))
        self.assertEqual([6, 0], WeekTimetable._parseRangesDays("Dom-Lun"))
        self.assertEqual([0, 1, 2, 3, 4, 5, 6], WeekTimetable._parseRangesDays("Lun-Lun"))

    def test_parse_ranges_hours(self):
        self.assertEqual((datetime.time(19), datetime.time(22)), WeekTimetable._parseRangesHours("19-22"))
        self.assertEqual((datetime.time(10, 30), datetime.time(11, 30)),
                         WeekTimetable._parseRangesHours("10:30-11:30"))
        with self.assertRaises(weektimetable.InvalidTimeFormat):
            WeekTimetable._parseRangesHours("11")
        with self.assertRaises(weektimetable.InvalidTimeFormat):
            WeekTimetable._parseRangesHours("11:69-22:30")

    def test_parse(self):
        tt = WeekTimetable.parse("Lun-Dom 7-19")
        self.assertEqual(7, len([x for x in tt._timeRanges.values() if x]))
        tt = WeekTimetable.parse("Lun 7-19 / Mar-Jue 10-12 / Dom 10:30-15:30")
        self.assertEqual(5, len([x for x in tt._timeRanges.values() if x]))


class TestWeektimetable(unittest.TestCase):
    def _parse(self, text, tz="America/Buenos_Aires"):
        return WeekTimetable.parse(text, tz)

    def test_in_timetable(self):
        test_date = datetime.datetime(2020, 1, 6, 11, 30, tzinfo=pytz.timezone("America/Buenos_Aires"))
        self.assertTrue(self._parse("Lun-Dom 10-19").inTimeTable(test_date))
        self.assertFalse(self._parse("Tue-Sun 10-19").inTimeTable(test_date))
        self.assertTrue(self._parse("Lun-Sun 10-19", pytz.utc).inTimeTable(test_date))
        self.assertFalse(self._parse("Lun-Sun 10-12", pytz.utc).inTimeTable(test_date))
        self.assertTrue(self._parse("Tue-Sun 23-12").inTimeTable(test_date))

    def test_overlaps(self):
        self.assertTrue(self._parse("Lun-Jue 10-15").overlaps(self._parse("Mar-Vie 14:30-15:30")))
        self.assertTrue(self._parse("Jue 10-15").overlaps(self._parse("Mar-Vie 14:30-15:30")))
        self.assertFalse(self._parse("Lun-Mie 10-15").overlaps(self._parse("Jue-Vie 14:30-15:30")))
