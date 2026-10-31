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
from recommendations import exclusion_reasons, preparation, recommend, trade_offs


def preferences(**changes):
    result = dict(max_minutes=300, max_distance=10, max_grade=3,
                  transport='car', scenery='forest', mood='active')
    result.update(changes)
    return result


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.locations, self.trails = load_catalogue()
        self.by_id = {trail['id']: trail for trail in self.trails}

    def test_catalogue_loads_typed_data(self):
        self.assertEqual(len(self.locations), 5)
        self.assertEqual(len(self.trails), 11)
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
                                ({'max_grade': 2}, 'grade'),
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
                         {'three-sisters', 'south-lawson', 'gordon-katoomba'})

    def test_any_preferences_and_ties(self):
        results = recommend(list(reversed(self.trails)), preferences(scenery='any', mood='any'))
        self.assertTrue(all(r['score'] == 100 for r in results))
        self.assertEqual([r['trail']['id'] for r in results][:2], ['fairfax', 'three-sisters'])

    def test_invalid_preferences(self):
        for changes in ({'max_minutes': float('nan')}, {'max_distance': float('inf')},
                        {'max_minutes': 0}, {'max_grade': 6}, {'scenery': 'snow'},
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
                            max_grade=2, scenery='waterfalls', mood='exploring', route='loop'))
        self.assertEqual(results[0]['trail']['id'], 'south-lawson')
        self.assertEqual(results[0]['score'], 100)

    def test_every_town_has_walks(self):
        self.assertEqual({t['location_id'] for t in self.trails},
                         {location['id'] for location in self.locations})

    def test_does_not_mutate_catalogue(self):
        before = repr(self.trails)
        recommend(self.trails, preferences())
        self.assertEqual(repr(self.trails), before)


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
        for field, value in [('distance_km', 'nan'), ('minutes', '-5'), ('grade', '9'),
                             ('location_id', 'unknown'), ('public_transport', 'maybe'),
                             ('route', 'flight'), ('scenery', 'snow'), ('mood', 'sleepy'),
                             ('id', 'fairfax'), ('name', '')]:
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
        answers = '\n'.join(['3', 'all', '2', 'all', '1', '0', '1', '300', '10', '3',
                             'car', 'forest', 'active', 'loop', 'yes', 'no', '4']) + '\n'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(BASE_DIR / 'main.py')],
                                    input=answers, text=True, capture_output=True,
                                    cwd=directory, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('History:', result.stdout)
        self.assertIn('1. Match score: 100/100', result.stdout)
        self.assertIn('Grand Canyon track', result.stdout)
        self.assertIn('Goodbye!', result.stdout)

    def test_no_match_flow(self):
        answers = ['1', '1', '1', '1', 'public', 'any', 'any', 'any', 'no', '4']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            self.assertEqual(main.main(), 0)
        self.assertIn('No walks match', output.getvalue())

    def test_save_flow_and_error_message(self):
        answers = ['45', '1', '1', 'public', 'views', 'relaxed', 'any', 'no', 'yes']
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), \
                patch('main.save_report', side_effect=PermissionError('read-only')), \
                contextlib.redirect_stdout(output):
            main.find_walk(load_catalogue()[1])
        self.assertIn('Could not save results', output.getvalue())
        self.assertIn('missing basic gear', output.getvalue())

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

    def test_startup_error(self):
        output = io.StringIO()
        with patch('main.load_catalogue', side_effect=ValueError('bad row')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(main.main(), 1)
        self.assertIn('Could not load catalogue', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
