import unittest
from check_tennis import parse_slots, TARGET_DAYS

SAMPLE_HTML = '''
<div class="timetable">
  <div class="table-row">
    <div class="table-head">Montag</div>
  </div>
  <div class="table-row">
    <div class="date bookable">
      <a><strong class="time">18:00-19:00</strong></a>
    </div>
    <div class="date bookable">
      <a><strong class="time">22:00-23:00</strong></a>
    </div>
  </div>
  <div class="table-row">
    <div class="table-head">Dienstag</div>
  </div>
  <div class="table-row">
    <div class="date bookable">
      <a><strong class="time">17:00-18:00</strong></a>
    </div>
  </div>
</div>
'''

class TestParseSlots(unittest.TestCase):
    def test_parse_slots(self):
        slots = parse_slots(SAMPLE_HTML)
        # Only slots between 17 and 21 (inclusive) should be included
        expected = [
            {'day': 'Montag', 'time': '18:00-19:00'},
            {'day': 'Dienstag', 'time': '17:00-18:00'},
        ]
        self.assertEqual(slots, expected)

if __name__ == "__main__":
    unittest.main()
