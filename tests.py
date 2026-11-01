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
from recommendations import (
    exclusion_reasons,
    preparation,
    recommend,
    trade_offs,
    time_alternatives,
)


def preferences(**changes):
    result = dict(
        max_minutes=300,
        max_distance=10,
        difficulty='moderate',
        scenery='forest',
        mood='active',
        route='any',
    )
    result.update(changes)
    return result


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.locations, self.trails = load_catalogue()
        self.by_id = {trail['id']: trail for trail in self.trails}

    def test_catalogue_loads_typed_data(self):
        self.assertEqual(len(self.locations), 14)
        self.assertEqual(len(self.trails), 18)

    def test_best_match_and_explanation(self):
        results = recommend(self.trails, preferences())

        self.assertEqual(results[0]['trail']['id'], 'gordon-katoomba')
        self.assertEqual(results[0]['score'], 100)
        self.assertEqual(len(results[0]['reasons']), 4)
        self.assertEqual(results[-1]['score'], 50)

    def test_each_hard_limit_excludes(self):
        trail = self.by_id['grand-canyon']

        cases = [
            ({'max_minutes': 239}, 'time'),
            ({'max_distance': 6.2}, 'distance'),
            ({'difficulty': 'easy'}, 'difficulty'),
        ]

        for changes, reason in cases:
            with self.subTest(changes=changes):
                prefs = preferences(**changes)

                self.assertEqual(recommend([trail], prefs), [])
                self.assertIn(
                    reason,
                    ' '.join(exclusion_reasons(trail, prefs))
                )

    def test_limits_are_inclusive(self):
        results = recommend(
            [self.by_id['grand-canyon']],
            preferences(
                max_minutes=240,
                max_distance=6.3,
            ),
        )

        self.assertEqual(len(results), 1)

    def test_no_matches(self):
        self.assertEqual(
            recommend(
                self.trails,
                preferences(max_minutes=1),
            ),
            [],
        )

    def test_any_preferences_and_ties(self):
        results = recommend(
            list(reversed(self.trails)),
            preferences(
                scenery='any',
                mood='any',
            ),
        )

        self.assertTrue(all(result['score'] == 100 for result in results))

        self.assertEqual(
            [result['trail']['id'] for result in results][:2],
            ['fairfax', 'three-sisters'],
        )

    def test_invalid_preferences(self):
        invalid_cases = [
            {'max_minutes': float('nan')},
            {'max_distance': float('inf')},
            {'max_minutes': 0},
            {'difficulty': 'extreme'},
            {'scenery': 'snow'},
            {'mood': 'sleepy'},
            {'route': 'flight'},
        ]

        for changes in invalid_cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                recommend(
                    self.trails,
                    preferences(**changes),
                )

    def test_preparation(self):
        notes = ' '.join(
            preparation(
                self.by_id['grand-canyon'],
                False,
            )
        )

        self.assertIn('heavy rain', notes)
        self.assertIn('missing basic gear', notes)
        self.assertIn('offline map', notes)

        self.assertIn(
            'One-way',
            ' '.join(
                preparation(
                    self.trails[1],
                    True,
                )
            ),
        )

    def test_route_preference_changes_ranking_without_exclusion(self):
        chosen = [
            self.by_id['grand-canyon'],
            self.by_id['gordon-katoomba'],
        ]

        results = recommend(
            chosen,
            preferences(route='one-way'),
        )

        self.assertEqual(
            [result['score'] for result in results],
            [100, 90],
        )

        self.assertEqual(
            results[0]['trail']['id'],
            'gordon-katoomba',
        )

        self.assertEqual(len(results), 2)

        self.assertIn(
            'preferred route',
            ' '.join(
                trade_offs(
                    chosen[0],
                    preferences(route='one-way'),
                )
            ),
        )

    def test_south_lawson_profile(self):
        results = recommend(
            self.trails,
            preferences(
                max_minutes=120,
                max_distance=4,
                difficulty='easy',
                scenery='waterfalls',
                mood='exploring',
                route='loop',
            ),
        )

        self.assertEqual(
            results[0]['trail']['id'],
            'south-lawson',
        )

        self.assertEqual(
            results[0]['score'],
            100,
        )

    def test_every_town_has_walks(self):
        for location in self.locations:
            local = [
                trail
                for trail in self.trails
                if trail['location_id'] == location['id']
            ]

            self.assertTrue(
                local or location['nearby_walk_ids'],
                location['name'],
            )

    def test_difficulty_filter(self):
        trail = self.by_id['porters-pass']

        self.assertEqual(
            recommend(
                [trail],
                preferences(difficulty='moderate'),
            ),
            [],
        )

        self.assertEqual(
            len(
                recommend(
                    [trail],
                    preferences(difficulty='hard'),
                )
            ),
            1,
        )

    def test_birdwood_can_be_recommended(self):
        trail = self.by_id['birdwood']

        self.assertEqual(
            trail['difficulty'],
            'moderate',
        )

        self.assertEqual(
            len(
                recommend(
                    [trail],
                    preferences(difficulty='moderate'),
                )
            ),
            1,
        )

    def test_elevation_is_known_or_explicitly_unknown(self):
        self.assertEqual(
            self.by_id['porters-pass']['elevation_gain_m'],
            473,
        )

        self.assertEqual(
            self.by_id['florabella']['elevation_gain_m'],
            406,
        )

        self.assertEqual(
            self.by_id['victory-sassafras']['elevation_gain_m'],
            338,
        )

        self.assertTrue(all(isinstance(t['elevation_gain_m'], int)
                            and t['elevation_gain_m'] > 0 for t in self.trails))
        self.assertTrue(self.by_id['grand-canyon']['elevation_source'].startswith('Project estimate'))

    def test_night_walk_preparation(self):
        self.assertIn(
            'torch',
            ' '.join(
                preparation(
                    self.by_id['night-lit'],
                    True,
                )
            ),
        )

    def test_does_not_mutate_catalogue(self):
        before = repr(self.trails)

        recommend(
            self.trails,
            preferences(),
        )

        self.assertEqual(
            repr(self.trails),
            before,
        )

    def test_optional_distance_has_no_hidden_cap(self):
        trail = dict(
            self.by_id['grand-canyon'],
            distance_km=100,
        )

        self.assertTrue(
            recommend(
                [trail],
                preferences(max_distance=None),
            )
        )

    def test_time_alternatives_preserve_other_limits(self):
        prefs = preferences(
            max_minutes=30,
            max_distance=2,
            difficulty='easy',
        )

        before = dict(prefs)

        options = time_alternatives(
            self.trails,
            prefs,
        )

        self.assertTrue(options)

        self.assertEqual(
            min(trail['minutes'] for trail in options),
            45,
        )

        self.assertTrue(
            all(
                trail['difficulty'] == 'easy'
                and trail['distance_km'] <= 2
                for trail in options
            )
        )

        self.assertEqual(
            prefs,
            before,
        )

        self.assertEqual(
            recommend(
                self.trails,
                prefs,
            ),
            [],
        )


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(
            self.temp.name
        )

        for name in (
            'locations.csv',
            'trails.csv',
        ):
            shutil.copy(
                BASE_DIR / name,
                self.directory / name,
            )

    def change_trail(self, field, value):
        path = self.directory / 'trails.csv'

        with path.open(
            newline='',
            encoding='utf-8',
        ) as source:
            reader = csv.DictReader(source)

            fields = reader.fieldnames
            rows = list(reader)

        rows[0][field] = value

        with path.open(
            'w',
            newline='',
            encoding='utf-8',
        ) as destination:
            writer = csv.DictWriter(
                destination,
                fieldnames=fields,
            )

            writer.writeheader()
            writer.writerows(rows)

    def test_invalid_fields(self):
        invalid_fields = [
            ('distance_km', 'nan'),
            ('minutes', '-5'),
            ('difficulty', 'extreme'),
            ('location_id', 'unknown'),
            ('route', 'flight'),
            ('scenery', 'snow'),
            ('mood', 'sleepy'),
            ('id', 'fairfax'),
            ('name', ''),
            ('elevation_gain_m', '-1'),
            ('elevation_gain_m', 'nan'),
            ('elevation_gain_m', '1.5'),
        ]

        for field, value in invalid_fields:
            with self.subTest(
                field=field,
                value=value,
            ):
                shutil.copy(
                    BASE_DIR / 'trails.csv',
                    self.directory / 'trails.csv',
                )

                self.change_trail(
                    field,
                    value,
                )

                with self.assertRaises(ValueError):
                    load_catalogue(
                        self.directory
                    )

    def test_missing_file(self):
        (
            self.directory
            / 'trails.csv'
        ).unlink()

        with self.assertRaises(FileNotFoundError):
            load_catalogue(
                self.directory
            )

    def test_bad_header_and_empty_file(self):
        for content in (
            'bad,header\n1,2\n',
            '',
        ):
            (
                self.directory
                / 'trails.csv'
            ).write_text(
                content,
                encoding='utf-8',
            )

            with self.assertRaises(ValueError):
                load_catalogue(
                    self.directory
                )

    def test_missing_and_extra_columns(self):
        original = (
            BASE_DIR
            / 'trails.csv'
        ).read_text(
            encoding='utf-8'
        ).splitlines()

        for row in (
            'incomplete,row',
            original[1] + ',extra',
        ):
            (
                self.directory
                / 'trails.csv'
            ).write_text(
                original[0]
                + '\n'
                + row,
                encoding='utf-8',
            )

            with self.assertRaises(ValueError):
                load_catalogue(
                    self.directory
                )

    def test_save_append_and_read_back(self):
        path = main.save_report(
            'First session',
            self.directory,
        )

        main.save_report(
            'Second session',
            self.directory,
        )

        text = path.read_text()

        self.assertIn(
            'First session',
            text,
        )

        self.assertIn(
            'Second session',
            text,
        )

    def test_unknown_nearby_walk_is_rejected(self):
        path = self.directory / 'locations.csv'

        with path.open(
            encoding='utf-8',
            newline='',
        ) as source:
            reader = csv.DictReader(source)

            fields = reader.fieldnames
            rows = list(reader)

        rows[0]['nearby_walk_ids'] = 'missing-walk'

        with path.open(
            'w',
            encoding='utf-8',
            newline='',
        ) as destination:
            writer = csv.DictWriter(
                destination,
                fieldnames=fields,
            )

            writer.writeheader()
            writer.writerows(rows)

        with self.assertRaisesRegex(
            ValueError,
            'Unknown nearby walk',
        ):
            load_catalogue(
                self.directory
            )

    def test_save_failure(self):
        with self.assertRaises(OSError):
            main.save_report(
                'test',
                self.directory / 'missing',
            )


class InteractionTests(unittest.TestCase):
    def test_number_validation(self):
        with patch(
            'builtins.input',
            side_effect=[
                'abc',
                'nan',
                'inf',
                '0',
                '-1',
                '1.5',
                '6',
                '3',
            ],
        ), contextlib.redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(
                main.ask_number(
                    'Number: ',
                    whole=True,
                    maximum=5,
                ),
                3,
            )

    def test_choice_normalises_input(self):
        with patch(
            'builtins.input',
            side_effect=[
                'invalid',
                ' YES ',
            ],
        ), contextlib.redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(
                main.choose(
                    'Continue?',
                    ['yes', 'no'],
                ),
                'yes',
            )

    def test_full_menu_from_other_directory(self):
        answers = '\n'.join([
            '3',
            'all',

            '2',
            'all',
            '1',
            '0',

            '1',
            'active',
            '300',
            'forest',
            'moderate',
            'yes',
            '10',
            'loop',
            'no',

            '4',
        ]) + '\n'

        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(BASE_DIR / 'main.py'),
                ],
                input=answers,
                text=True,
                capture_output=True,
                cwd=directory,
                timeout=10,
            )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )

        self.assertIn(
            'History:',
            result.stdout,
        )

        self.assertIn(
            'YOUR WALK SUGGESTIONS',
            result.stdout,
        )

        self.assertIn(
            'Grand Canyon track',
            result.stdout,
        )

        self.assertIn(
            'Goodbye!',
            result.stdout,
        )

    def test_no_match_flow(self):
        answers = [
            '1',
            'any',
            '1',
            'any',
            'easy',
            'no',
            'no',
            'no',
            '4',
        ]

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=answers,
        ), contextlib.redirect_stdout(
            output
        ):
            self.assertEqual(
                main.main(),
                0,
            )

        self.assertIn(
            'No walks match',
            output.getvalue(),
        )

    def test_save_flow_and_error_message(self):
        answers = [
            'relaxed',
            '45',
            'views',
            'easy',
            'yes',
            '1',
            'any',
            'yes',
        ]

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=answers,
        ), patch(
            'main.save_report',
            side_effect=PermissionError(
                'read-only'
            ),
        ), contextlib.redirect_stdout(
            output
        ):
            main.find_walk(
                load_catalogue()[1]
            )

        self.assertIn(
            'Could not save results',
            output.getvalue(),
        )

        self.assertIn(
            'Bring water',
            output.getvalue(),
        )

    def test_eof_and_interrupt(self):
        for error in (
            EOFError,
            KeyboardInterrupt,
        ):
            with patch(
                'builtins.input',
                side_effect=error,
            ), contextlib.redirect_stdout(
                io.StringIO()
            ):
                self.assertEqual(
                    main.main(),
                    0,
                )

    def test_numbered_choices(self):
        with patch(
            'builtins.input',
            return_value='2',
        ), contextlib.redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(
                main.choose(
                    'Difficulty',
                    [
                        'easy',
                        'moderate',
                        'hard',
                    ],
                ),
                'moderate',
            )

    def test_browse_filter_and_back(self):
        locations, trails = load_catalogue()

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=[
                'lawson',
                '1',
                '0',
            ],
        ), contextlib.redirect_stdout(
            output
        ):
            main.browse(
                locations,
                trails,
            )

        self.assertIn(
            'South Lawson',
            output.getvalue(),
        )

        self.assertNotIn(
            'Grand Canyon',
            output.getvalue(),
        )

    def test_explore_one_town(self):
        output = io.StringIO()

        with patch(
            'builtins.input',
            return_value='leura',
        ), contextlib.redirect_stdout(
            output
        ):
            main.explore(
                *load_catalogue()
            )

        self.assertIn(
            'Leura | NSW 2780',
            output.getvalue(),
        )

        self.assertNotIn(
            'Lawson | NSW',
            output.getvalue(),
        )

    def test_walk_columns_align_with_long_names(self):
        trails = load_catalogue()[1]

        lines = main.walk_list_lines(
            trails
        )

        rows = [
            line
            for line in lines
            if line[:3].strip().isdigit()
        ]

        self.assertEqual(
            len(rows),
            len(trails),
        )

        self.assertEqual(
            len({
                len(row)
                for row in rows
            }),
            1,
        )

        self.assertTrue(
            all(
                len(line) <= main.WIDTH
                for line in lines
            )
        )

        for row, trail in zip(
            rows,
            trails,
        ):
            self.assertEqual(
                float(row[34:39]),
                trail['distance_km'],
            )

            self.assertEqual(
                int(row[40:44]),
                trail['minutes'],
            )

        table = '\n'.join(rows)

        self.assertNotIn('--', table)
        for row, trail in zip(rows, trails):
            self.assertEqual(int(row.split()[-1]), trail['elevation_gain_m'])
        missing = dict(trails[0], elevation_gain_m=None)
        self.assertIn('--', '\n'.join(main.walk_list_lines([missing])))

        self.assertIn(
            'Easy',
            table,
        )

        self.assertIn(
            'Moderate',
            table,
        )

        self.assertIn(
            'Hard',
            table,
        )

    def test_nearby_walks_are_labelled(self):
        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=[
                'warrimoo',
                '0',
            ],
        ), contextlib.redirect_stdout(
            output
        ):
            main.browse(
                *load_catalogue()
            )

        self.assertIn(
            'nearby / connecting',
            output.getvalue(),
        )

        self.assertIn(
            'Florabella',
            output.getvalue(),
        )

    def test_yellow_deli_in_katoomba(self):
        output = io.StringIO()

        with patch(
            'builtins.input',
            return_value='katoomba',
        ), contextlib.redirect_stdout(
            output
        ):
            main.explore(
                *load_catalogue()
            )

        self.assertIn(
            'Yellow Deli',
            output.getvalue(),
        )

        self.assertIn(
            '214 Katoomba Street',
            output.getvalue(),
        )

    def test_accept_time_change_then_save_uses_new_limit(self):
        answers = [
            'relaxed',
            '30',
            'waterfalls',
            'easy',
            'yes',
            '2',
            'loop',
            'yes',
            'yes',
        ]

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=answers,
        ), patch(
            'main.save_report'
        ) as save, contextlib.redirect_stdout(
            output
        ):
            main.find_walk(
                load_catalogue()[1]
            )

        self.assertIn(
            'need 45 minutes',
            output.getvalue(),
        )

        self.assertIn(
            'YOUR WALK SUGGESTIONS',
            output.getvalue(),
        )

        self.assertIn(
            'Walking time limit (minutes): 45',
            save.call_args.args[0],
        )

        self.assertNotIn(
            'Grand Canyon track',
            output.getvalue(),
        )

    def test_declining_time_change_does_not_recommend(self):
        answers = [
            'relaxed',
            '30',
            'waterfalls',
            'easy',
            'no',
            'no',
            'no',
        ]

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=answers,
        ), contextlib.redirect_stdout(
            output
        ):
            main.find_walk(
                load_catalogue()[1]
            )

        self.assertNotIn(
            'YOUR WALK SUGGESTIONS',
            output.getvalue(),
        )

        self.assertNotIn(
            'exceeds time limit',
            output.getvalue(),
        )

    def test_retry_after_impossible_distance(self):
        answers = [
            'relaxed',
            '30',
            'views',
            'easy',
            'yes',
            '0.1',
            'any',
            'yes',

            'relaxed',
            '60',
            'views',
            'easy',
            'no',
            'no',
        ]

        output = io.StringIO()

        with patch(
            'builtins.input',
            side_effect=answers,
        ), contextlib.redirect_stdout(
            output
        ):
            main.find_walk(
                load_catalogue()[1]
            )

        self.assertIn(
            'YOUR WALK SUGGESTIONS',
            output.getvalue(),
        )

    def test_friendly_labels_accept_displayed_text(self):
        with patch(
            'builtins.input',
            return_value='Ready for a workout',
        ), contextlib.redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(
                main.choose(
                    'Mood',
                    [
                        'relaxed',
                        'exploring',
                        'active',
                    ],
                    {
                        'relaxed': 'Taking it easy',
                        'exploring': 'Keen to explore',
                        'active': 'Ready for a workout',
                    },
                ),
                'active',
            )

    def test_compact_results_no_fake_perfect_match(self):
        prefs = preferences(
            mood='any',
            scenery='any',
            route='any',
            max_distance=None,
        )

        results = recommend(
            load_catalogue()[1],
            prefs,
        )

        screen = main.short_results(
            results,
            prefs,
        )

        report = main.format_results(
            results,
            prefs,
            True,
        )

        self.assertNotIn(
            '100/100',
            screen,
        )

        self.assertNotIn(
            'Elevation source:',
            screen,
        )

        self.assertIn(
            'Ordered by walking time',
            screen,
        )

        self.assertIn(
            'Source:',
            report,
        )

        self.assertNotIn(
            'None',
            report,
        )

    def test_startup_error(self):
        output = io.StringIO()

        with patch(
            'main.load_catalogue',
            side_effect=ValueError(
                'bad row'
            ),
        ), contextlib.redirect_stdout(
            output
        ):
            self.assertEqual(
                main.main(),
                1,
            )

        self.assertIn(
            'Could not load catalogue',
            output.getvalue(),
        )


class FinalAuditTests(unittest.TestCase):
    def test_unusual_menu_numbers_retry(self):
        with patch('builtins.input', side_effect=['²', '9' * 5000, '2']), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.choose('Choose', ['easy', 'moderate']), 'moderate')

    def test_all_difficulty_limits_and_information_only_fields(self):
        trails = load_catalogue()[1]
        for level, allowed in [('easy', {'easy'}),
                               ('moderate', {'easy', 'moderate'}),
                               ('hard', {'easy', 'moderate', 'hard'})]:
            prefs = preferences(difficulty=level, max_minutes=1000, max_distance=None)
            results = recommend(trails, prefs)
            self.assertEqual({r['trail']['id'] for r in results},
                             {t['id'] for t in trails if t['difficulty'] in allowed})
            changed = [dict(t, public_transport=not t['public_transport'],
                            elevation_gain_m=9999) for t in trails]
            self.assertEqual([(r['trail']['id'], r['score']) for r in results],
                             [(r['trail']['id'], r['score']) for r in recommend(changed, prefs)])

    def test_demo_and_all_extra_route_choices(self):
        trails = load_catalogue()[1]
        prefs = preferences(mood='exploring', max_minutes=70, scenery='waterfalls',
                            difficulty='moderate', max_distance=None)
        self.assertEqual([r['trail']['id'] for r in recommend(trails, prefs)[:3]],
                         ['horseshoe', 'princes-rock', 'wentworth-track'])
        for route in ('loop', 'return', 'one-way', 'any'):
            with patch('builtins.input', side_effect=['exploring', '70', 'waterfalls',
                       'moderate', 'yes', '2', route, 'no']), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                main.find_walk(trails)
            self.assertIn('YOUR WALK SUGGESTIONS', out.getvalue())

    def test_sixty_minute_boundary(self):
        trail = next(t for t in load_catalogue()[1] if t['id'] == 'horseshoe')
        self.assertTrue(recommend([trail], preferences(max_minutes=60, max_distance=1)))
        self.assertFalse(recommend([trail], preferences(max_minutes=59)))


if __name__ == '__main__':
    unittest.main(
        verbosity=2
    )