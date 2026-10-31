"""Run with python3 tests.py or python3 -m unittest discover -v."""
import contextlib
import csv
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from data_loader import BASE_DIR, load_catalogue
import main
from recommendations import exclusion_reasons, preparation, recommend, trade_offs, time_alternatives


def preferences(**changes):
    result = dict(max_minutes=300, max_distance=10, difficulty='moderate',
                  transport='car', scenery='forest', mood='active')
    result.update(changes)
    return result


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.locations, self.trails = load_catalogue()
        self.by_id = {trail['id']: trail for trail in self.trails}

    def test_catalogue_loads_typed_data(self):
        self.assertEqual(len(self.locations), 14)
        self.assertEqual(len(self.trails), 18)
        self.assertIsInstance(self.trails[0]['public_transport'], bool)

    def test_best_match_and_explanation(self):
        results = recommend(self.trails, preferences())
        self.assertEqual(results[0]['trail']['id'], 'gordon-katoomba')
        self.assertEqual(results[0]['score'], 100)
        self.assertEqual(len(results[0]['reasons']), 4)
        self.assertEqual(results[-1]['score'], 50)

    def test_each_hard_limit_excludes(self):
        trail = self.by_id['grand-canyon']
        for changes, reason in [({'max_minutes': 239}, 'time'),
                                ({'max_distance': 6.2}, 'distance'),
                                ({'difficulty': 'easy'}, 'difficulty'),
                                ({'transport': 'public'}, 'transport')]:
            with self.subTest(changes=changes):
                self.assertEqual(recommend([trail], preferences(**changes)), [])
                self.assertIn(reason, ' '.join(exclusion_reasons(trail, preferences(**changes))))

    def test_limits_are_inclusive(self):
        results = recommend([self.by_id['grand-canyon']], preferences(max_minutes=240, max_distance=6.3))
        self.assertEqual(len(results), 1)

    def test_no_matches(self):
        self.assertEqual(recommend(self.trails, preferences(max_minutes=1)), [])

    def test_public_transport(self):
        results = recommend(self.trails, preferences(transport='public'))
        self.assertEqual({r['trail']['id'] for r in results},
                         {'three-sisters', 'south-lawson', 'gordon-katoomba', 'night-lit', 'woodford-creek', 'horseshoe'})

    def test_any_preferences_and_ties(self):
        results = recommend(list(reversed(self.trails)), preferences(scenery='any', mood='any'))
        self.assertTrue(all(r['score'] == 100 for r in results))
        self.assertEqual([r['trail']['id'] for r in results][:2], ['fairfax', 'three-sisters'])

    def test_invalid_preferences(self):
        for changes in ({'max_minutes': float('nan')}, {'max_distance': float('inf')},
                        {'max_minutes': 0}, {'difficulty': 'extreme'}, {'scenery': 'snow'},
                        {'mood': 'sleepy'}, {'transport': 'helicopter'}, {'route': 'flight'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                recommend(self.trails, preferences(**changes))

    def test_preparation(self):
        notes = ' '.join(preparation(self.by_id['grand-canyon'], False))
        self.assertIn('heavy rain', notes)
        self.assertIn('missing basic gear', notes)
        self.assertIn('offline map', notes)
        self.assertIn('One-way', ' '.join(preparation(self.trails[1], True)))

    def test_route_preference_changes_ranking_without_exclusion(self):
        chosen = [self.by_id['grand-canyon'], self.by_id['gordon-katoomba']]
        results = recommend(chosen, preferences(route='one-way'))
        self.assertEqual([r['score'] for r in results], [100, 90])
        self.assertEqual(results[0]['trail']['id'], 'gordon-katoomba')
        self.assertEqual(len(results), 2)
        self.assertIn('preferred route', ' '.join(trade_offs(chosen[0], preferences(route='one-way'))))

    def test_south_lawson_profile(self):
        results = recommend(self.trails, preferences(max_minutes=120, max_distance=4,
                            difficulty='easy', scenery='waterfalls', mood='exploring', route='loop'))
        self.assertEqual(results[0]['trail']['id'], 'south-lawson')
        self.assertEqual(results[0]['score'], 100)

    def test_every_town_has_walks(self):
        for location in self.locations:
            local = [t for t in self.trails if t['location_id'] == location['id']]
            self.assertTrue(local or location['nearby_walk_ids'], location['name'])

    def test_difficulty_filter(self):
        trail = self.by_id['porters-pass']
        self.assertEqual(recommend([trail], preferences(difficulty='moderate')), [])
        self.assertEqual(len(recommend([trail], preferences(difficulty='hard'))), 1)

    def test_birdwood_can_be_recommended(self):
        trail = self.by_id['birdwood']
        self.assertEqual(trail['difficulty'], 'moderate')
        self.assertEqual(len(recommend([trail], preferences(difficulty='moderate'))), 1)

    def test_elevation_is_known_or_explicitly_unknown(self):
        self.assertEqual(self.by_id['porters-pass']['elevation_gain_m'], 473)
        self.assertEqual(self.by_id['florabella']['elevation_gain_m'], 406)
        self.assertEqual(self.by_id['victory-sassafras']['elevation_gain_m'], 338)
        self.assertIsNone(self.by_id['grand-canyon']['elevation_gain_m'])
        self.assertIsNone(self.by_id['fairfax']['elevation_gain_m'])
        self.assertIn('estimate unavailable', main.trail_text(self.by_id['grand-canyon']))

    def test_night_walk_preparation(self):
        self.assertIn('torch', ' '.join(preparation(self.by_id['night-lit'], True)))

    def test_does_not_mutate_catalogue(self):
        before = repr(self.trails)
        recommend(self.trails, preferences())
        self.assertEqual(repr(self.trails), before)

    def test_optional_distance_has_no_hidden_cap(self):
        trail = dict(self.by_id['grand-canyon'], distance_km=100)
        self.assertTrue(recommend([trail], preferences(max_distance=None)))

    def test_time_alternatives_preserve_other_limits(self):
        prefs = preferences(max_minutes=30, max_distance=2, difficulty='easy')
        before = dict(prefs)
        options = time_alternatives(self.trails, prefs)
        self.assertTrue(options)
        self.assertEqual(min(t['minutes'] for t in options), 45)
        self.assertTrue(all(t['difficulty'] == 'easy' and t['distance_km'] <= 2 for t in options))
        self.assertEqual(prefs, before)
        self.assertEqual(recommend(self.trails, prefs), [])


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name in ('locations.csv', 'trails.csv'):
            shutil.copy(BASE_DIR / name, self.directory / name)

    def change_trail(self, field, value):
        path = self.directory / 'trails.csv'
        with path.open(newline='', encoding='utf-8') as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            rows = list(reader)
        rows[0][field] = value
        with path.open('w', newline='', encoding='utf-8') as destination:
            writer = csv.DictWriter(destination, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_invalid_fields(self):
        for field, value in [('distance_km', 'nan'), ('minutes', '-5'), ('difficulty', 'extreme'),
                             ('location_id', 'unknown'), ('public_transport', 'maybe'),
                             ('route', 'flight'), ('scenery', 'snow'), ('mood', 'sleepy'),
                             ('id', 'fairfax'), ('name', ''), ('elevation_gain_m', '-1'),
                             ('elevation_gain_m', 'nan'), ('elevation_gain_m', '1.5')]:
            with self.subTest(field=field):
                shutil.copy(BASE_DIR / 'trails.csv', self.directory / 'trails.csv')
                self.change_trail(field, value)
                with self.assertRaises(ValueError):
                    load_catalogue(self.directory)

    def test_missing_file(self):
        (self.directory / 'trails.csv').unlink()
        with self.assertRaises(FileNotFoundError):
            load_catalogue(self.directory)

    def test_bad_header_and_empty_file(self):
        for content in ('bad,header\n1,2\n', ''):
            (self.directory / 'trails.csv').write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                load_catalogue(self.directory)

    def test_missing_and_extra_columns(self):
        original = (BASE_DIR / 'trails.csv').read_text(encoding='utf-8').splitlines()
        for row in ('incomplete,row', original[1] + ',extra'):
            (self.directory / 'trails.csv').write_text(original[0] + '\n' + row, encoding='utf-8')
            with self.assertRaises(ValueError):
                load_catalogue(self.directory)

    def test_save_append_and_read_back(self):
        path = main.save_report('First session', self.directory)
        main.save_report('Second session', self.directory)
        self.assertIn('First session', path.read_text())
        self.assertIn('Second session', path.read_text())

    def test_unknown_nearby_walk_is_rejected(self):
        path = self.directory / 'locations.csv'
        with path.open(encoding='utf-8', newline='') as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            rows = list(reader)
        rows[0]['nearby_walk_ids'] = 'missing-walk'
        with path.open('w', encoding='utf-8', newline='') as destination:
            writer = csv.DictWriter(destination, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, 'Unknown nearby walk'):
            load_catalogue(self.directory)

    def test_save_failure(self):
        with self.assertRaises(OSError):
            main.save_report('test', self.directory / 'missing')


class InteractionTests(unittest.TestCase):
    def test_number_validation(self):
        with patch('builtins.input', side_effect=['abc', 'nan', 'inf', '0', '-1', '1.5', '6', '3']), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.ask_number('Grade: ', whole=True, maximum=5), 3)

    def test_choice_normalises_input(self):
        with patch('builtins.input', side_effect=['invalid', ' YES ']), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.choose('Ready?', ['yes', 'no']), 'yes')

    def test_full_menu_from_other_directory(self):
        answers = '\n'.join(['3', 'all', '2', 'all', '1', '0', '1', 'active', 'forest', '300',
                             'moderate', 'car', 'yes', '10', 'loop', 'no', '4']) + '\n'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(BASE_DIR / 'main.py')],
                                    input=answers, text=True, capture_output=True,
                                    cwd=directory, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('History:', result.stdout)
        self.assertIn('YOUR WALK SUGGESTIONS', result.stdout)
        self.assertIn('Grand Canyon track', result.stdout)
        self.assertIn('Goodbye!', result.stdout)

    def test_no_match_flow(self):
        answers = ['1', 'any', 'any', '1', 'easy', 'public', 'no', 'no', 'no', '4']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            self.assertEqual(main.main(), 0)
        self.assertIn('No walks match', output.getvalue())

    def test_save_flow_and_error_message(self):
        answers = ['relaxed', 'views', '45', 'easy', 'public', 'yes', '1', 'any', 'yes']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), \
                patch('main.save_report', side_effect=PermissionError('read-only')), \
                contextlib.redirect_stdout(output):
            main.find_walk(load_catalogue()[1])
        self.assertIn('Could not save results', output.getvalue())
        self.assertIn('Bring water', output.getvalue())

    def test_eof_and_interrupt(self):
        for error in (EOFError, KeyboardInterrupt):
            with patch('builtins.input', side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.main(), 0)

    def test_numbered_choices(self):
        with patch('builtins.input', return_value='2'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.choose('Transport', ['car', 'public']), 'public')

    def test_browse_filter_and_back(self):
        locations, trails = load_catalogue()
        output = io.StringIO()
        with patch('builtins.input', side_effect=['lawson', '1', '0']), contextlib.redirect_stdout(output):
            main.browse(locations, trails)
        self.assertIn('South Lawson', output.getvalue())
        self.assertNotIn('Grand Canyon', output.getvalue())

    def test_explore_one_town(self):
        output = io.StringIO()
        with patch('builtins.input', return_value='leura'), contextlib.redirect_stdout(output):
            main.explore(*load_catalogue())
        self.assertIn('Leura | NSW 2780', output.getvalue())
        self.assertNotIn('Lawson | NSW', output.getvalue())

    def test_walk_columns_align_with_long_names(self):
        trails = load_catalogue()[1]
        lines = main.walk_list_lines(trails)
        rows = [line for line in lines if line[:3].strip().isdigit()]
        self.assertEqual(len(rows), len(trails))
        self.assertEqual(len({len(row) for row in rows}), 1)
        self.assertTrue(all(len(line) <= main.WIDTH for line in lines))
        for row, trail in zip(rows, trails):
            self.assertEqual(float(row[34:39]), trail['distance_km'])
            self.assertEqual(int(row[40:44]), trail['minutes'])
        self.assertIn('--', '\n'.join(rows))
        self.assertIn('Easy', '\n'.join(rows))
        self.assertIn('Moderate', '\n'.join(rows))
        self.assertIn('Hard', '\n'.join(rows))

    def test_nearby_walks_are_labelled(self):
        output = io.StringIO()
        with patch('builtins.input', side_effect=['warrimoo', '0']), contextlib.redirect_stdout(output):
            main.browse(*load_catalogue())
        self.assertIn('nearby / connecting', output.getvalue())
        self.assertIn('Florabella', output.getvalue())

    def test_yellow_deli_in_katoomba(self):
        output = io.StringIO()
        with patch('builtins.input', return_value='katoomba'), contextlib.redirect_stdout(output):
            main.explore(*load_catalogue())
        self.assertIn('Yellow Deli', output.getvalue())
        self.assertIn('214 Katoomba Street', output.getvalue())

    def test_accept_time_change_then_save_uses_new_limit(self):
        answers = ['relaxed', 'waterfalls', '30', 'easy', 'car', 'yes', '2', 'loop', 'yes', 'yes']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), patch('main.save_report') as save, \
                contextlib.redirect_stdout(output):
            main.find_walk(load_catalogue()[1])
        self.assertIn('need 45 minutes', output.getvalue())
        self.assertIn('YOUR WALK SUGGESTIONS', output.getvalue())
        self.assertIn('Walking time limit (minutes): 45', save.call_args.args[0])
        self.assertNotIn('Grand Canyon track', output.getvalue())

    def test_declining_time_change_does_not_recommend(self):
        answers = ['relaxed', 'waterfalls', '30', 'easy', 'car', 'no', 'no', 'no']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            main.find_walk(load_catalogue()[1])
        self.assertNotIn('YOUR WALK SUGGESTIONS', output.getvalue())
        self.assertNotIn('exceeds time limit', output.getvalue())

    def test_retry_after_impossible_distance(self):
        answers = ['relaxed', 'views', '30', 'easy', 'car', 'yes', '0.1', 'any', 'yes',
                   'relaxed', 'views', '60', 'easy', 'car', 'no', 'no']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            main.find_walk(load_catalogue()[1])
        self.assertIn('YOUR WALK SUGGESTIONS', output.getvalue())

    def test_friendly_labels_accept_displayed_text(self):
        with patch('builtins.input', return_value='Public transport'), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.choose('Transport', ['car', 'public'],
                                         {'public': 'Public transport'}), 'public')

    def test_compact_results_no_fake_perfect_match(self):
        prefs = preferences(mood='any', scenery='any', route='any', max_distance=None)
        results = recommend(load_catalogue()[1], prefs)
        screen = main.short_results(results, prefs)
        report = main.format_results(results, prefs, True)
        self.assertNotIn('100/100', screen)
        self.assertNotIn('Elevation source:', screen)
        self.assertIn('Ordered by walking time', screen)
        self.assertIn('Source:', report)
        self.assertNotIn('None', report)

    def test_startup_error(self):
        output = io.StringIO()
        with patch('main.load_catalogue', side_effect=ValueError('bad row')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(main.main(), 1)
        self.assertIn('Could not load catalogue', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
