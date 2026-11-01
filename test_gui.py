"""Small GUI helper tests; no desktop or Tk window required."""
import unittest
from gui import preferences_from_form, town_text, elevation_text, walk_detail_text
from data_loader import load_catalogue
from recommendations import recommend


class GUIHelpersTests(unittest.TestCase):
    def test_form_and_shared_demo_ranking(self):
        prefs = preferences_from_form('Keen to explore', '70', 'Waterfalls',
                                      'Moderate', False, 'invalid ignored', 'Loop')
        self.assertIsNone(prefs['max_distance'])
        self.assertEqual(prefs['route'], 'any')
        self.assertEqual([r['trail']['id'] for r in recommend(load_catalogue()[1], prefs)[:3]],
                         ['horseshoe', 'princes-rock', 'wentworth-track'])

    def test_numeric_validation_and_extra_preferences(self):
        for bad in ('', 'abc', '0', '-1', 'nan', 'inf'):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                preferences_from_form('Taking it easy', bad, 'Views', 'Easy', False, '', 'Loop')
            with self.subTest(distance=bad), self.assertRaises(ValueError):
                preferences_from_form('Taking it easy', '60', 'Views', 'Easy', True, bad, 'Loop')
        prefs = preferences_from_form('Ready for a workout', '300', 'Forest',
                                      'Moderate', True, '10', 'Loop')
        self.assertEqual(recommend(load_catalogue()[1], prefs)[0]['trail']['id'], 'grand-canyon')

    def test_elevation_provenance_display(self):
        for trail in load_catalogue()[1]:
            rendered = elevation_text(trail)
            if trail['id'] in ('porters-pass', 'florabella', 'victory-sassafras'):
                self.assertEqual(rendered, f"{trail['elevation_gain_m']} m")
            else:
                self.assertTrue(rendered.startswith('Approx. '))
                self.assertIn('not an official track measurement', walk_detail_text(trail))
            self.assertNotIn('Unavailable', walk_detail_text(trail))

    def test_town_nearby_is_distinguished(self):
        locations, trails = load_catalogue()
        town = next(l for l in locations if l['id'] == 'valley-heights')
        text = town_text(town, trails)
        self.assertIn('No local route', text)
        self.assertIn('NEARBY / CONNECTING', text)
        self.assertIn('Birdwood Gully', text)


if __name__ == '__main__':
    unittest.main()
