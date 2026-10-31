"""Blue Mountains Handbook: run with python3 main.py."""
import csv
import textwrap
from pathlib import Path

from data_loader import BASE_DIR, load_catalogue, positive_number
from recommendations import preparation, recommend, trade_offs, time_alternatives

NOTICE = ('Offline study guide: track status is unknown. Check current NPWS and council notices, '
          'weather and access before walking. Times exclude travel, breaks and delays.')
ALERTS = 'https://www.nationalparks.nsw.gov.au/alerts/alerts-list'
COUNCIL = 'https://www.bmcc.nsw.gov.au/'


WIDTH = 76


def heading(title):
    print('\n' + '=' * WIDTH)
    print(title)
    print('=' * WIDTH)


def wrapped(text, indent='  '):
    return textwrap.fill(text, width=WIDTH, initial_indent=indent,
                         subsequent_indent=indent, break_long_words=False,
                         break_on_hyphens=False)


def choose(prompt, options, labels=None):
    """Accept a displayed number or its text label; keep validation in one place."""
    print('\n' + prompt)
    numbered = not all(option.isdigit() for option in options)
    if numbered:
        for index, option in enumerate(options, 1):
            label = option.replace('-', ' ').title()
            if labels:
                label = labels.get(option, label)
            if option == 'any':
                label = 'No preference'
            print(f'  {index}. {label}')
    while True:
        answer = input('Your choice: ').strip().lower()
        if answer in options:
            return answer
        for option in options:
            label = (labels or {}).get(option, option.replace('-', ' '))
            if option == 'any':
                label = 'No preference'
            if answer == label.lower():
                return option
        if numbered and answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print('Please enter one of the listed options.')


def ask_number(prompt, whole=False, maximum=None):
    while True:
        try:
            number = positive_number(input(prompt).strip())
            if whole and not number.is_integer():
                raise ValueError('Enter a whole number.')
            if maximum is not None and number > maximum:
                raise ValueError(f'Enter a value no greater than {maximum}.')
            return int(number) if whole else number
        except ValueError as error:
            print(f'Invalid number: {error}')


def trail_text(trail):
    hours, minutes = divmod(trail['minutes'], 60)
    duration = f'{hours} hr' if hours else ''
    if minutes:
        duration += f' {minutes} min'
    duration = duration.strip()
    area = trail['location_id'].replace('-', ' ').title()
    lines = [wrapped(trail['name'], ''), f"  {area} | {trail['distance_km']:g} km {trail['route']} | "
             f"{duration} | Grade {trail['grade'] if trail['grade'] is not None else 'unverified'}",
             wrapped('Elevation gain: ' + (f"about {trail['elevation_gain_m']} m"
                     if trail['elevation_gain_m'] is not None else 'estimate unavailable')),

             wrapped(trail['description']),
             wrapped(f"Scenery: {', '.join(trail['scenery'])} | Mood: {trail['mood']}"),
             wrapped('Access: ' + trail['transport_note']),
             wrapped('Route notes: ' + trail['data_note']),
             '  Source: ' + trail['source']]
    if trail['elevation_gain_m'] is not None:
        lines.append(wrapped('Elevation source: ' + trail['elevation_source']))
    if trail['grade'] is None:
        lines.append(wrapped('Browse only: a numeric grade is needed before this walk can be recommended.'))
    return '\n'.join(lines)


def explore(locations, trails):
    heading('EXPLORE LOCAL TOWNS IN THE BLUE MOUNTAINS')
    options = ['all'] + [location['id'] for location in locations] + ['back']
    selected = choose('Choose an area', options)
    for location in locations:
        if selected not in ('all', location['id']):
            continue
        print(f"\n{location['name']} | NSW {location['postcode']}")
        print(wrapped(location['description']))
        print(wrapped('History: ' + location['history']))
        print('  History source:', location['source'])
        print(wrapped('Things to do: ' + location['things_to_do']))
        print('  Visitor information:', location['visitor_source'])
        print(wrapped('Food and supplies: ' + location['food_supplies']))
        print('  Food information:', location['food_source'])
        print('  Check current opening hours and bookings before visiting.')
        print('  Local walks in this catalogue:')
        local = [trail for trail in trails if trail['location_id'] == location['id']]
        for trail in local:
            print(wrapped('- ' + trail['name'], '    '))
        if not local:
            print('    No local route verified in this catalogue yet.')
        if location['nearby_walk_ids']:
            print('  Nearby / connecting walks (travel may be needed):')
            for trail in trails:
                if trail['id'] in location['nearby_walk_ids']:
                    print(wrapped('- ' + trail['name'], '    '))


def walk_list_lines(trails):
    """Fixed-width numeric columns; long names continue on their own lines."""
    lines = [f"{'No.':>3}  {'Walk':<32} {'km':>5} {'min':>4} {'Grade':>5} {'Gain m':>7}"]
    for index, trail in enumerate(trails, 1):
        names = textwrap.wrap(trail['name'], width=32)
        grade = str(trail['grade']) if trail['grade'] is not None else '?'
        gain = str(trail['elevation_gain_m']) if trail['elevation_gain_m'] is not None else '--'
        lines.append(f"{index:>3}  {names[0]:<32} {trail['distance_km']:>5.1f} "
                     f"{trail['minutes']:>4} {grade:>5} {gain:>7}")
        for name in names[1:]:
            lines.append('     ' + name)
    lines.append('Gain = approximate total ascent. -- = unavailable; ? = unverified grade.')
    return lines


def browse(locations, trails):
    heading('BROWSE WALKS')
    location_id = choose('Choose an area', ['all'] + [item['id'] for item in locations] + ['back'])
    if location_id == 'back':
        return
    nearby_ids = []
    for location in locations:
        if location['id'] == location_id:
            nearby_ids = location['nearby_walk_ids']
    selected = []
    for trail in trails:
        if location_id == 'all' or trail['location_id'] == location_id or trail['id'] in nearby_ids:
            selected.append(trail)
    if nearby_ids:
        print('Includes nearby / connecting walks; details show the route location.')
    if not selected:
        print('No walks are listed for this area yet.')
        return
    while True:
        print('\nWalks in this area:')
        for line in walk_list_lines(selected):
            print(line)
        print('  0. Back to main menu')
        choice = choose('View details for a walk', [str(i) for i in range(len(selected) + 1)])
        if choice == '0':
            return
        print('\n' + trail_text(selected[int(choice) - 1]))
        print('-' * WIDTH)


def collect_preferences():
    heading('FIND A WALK FOR ME')
    mood = choose('How are you feeling today?', ['relaxed', 'exploring', 'active', 'any'],
                  {'relaxed': 'Taking it easy', 'exploring': 'Keen to explore',
                   'active': 'Ready for a workout'})
    scenery = choose('What would you like to see?', ['views', 'waterfalls', 'forest', 'any'])
    print('\nAllow extra time for travel and breaks. Walk times are planning estimates.')
    minutes = ask_number('How much walking time do you have (minutes)? ')
    difficulty = choose('What difficulty are you comfortable with?',
                        ['easy', 'moderate', 'challenging'],
                        {'easy': 'Easy - grades 1 to 2',
                         'moderate': 'Moderate - up to grade 3, with steps and hills',
                         'challenging': 'Challenging - up to grade 5, experienced walkers'})
    transport = choose('How will you get there?', ['car', 'public'],
                       {'public': 'Public transport'})
    distance = None
    route = 'any'
    if choose('Set a distance limit or preferred route style?', ['no', 'yes']) == 'yes':
        distance = ask_number('Maximum walking distance in km: ')
        route = choose('Preferred route style', ['any', 'loop', 'return', 'one-way'])
    return dict(mood=mood, scenery=scenery, max_minutes=minutes,
                max_grade={'easy': 2, 'moderate': 3, 'challenging': 5}[difficulty],
                transport=transport, max_distance=distance, route=route)


def short_results(results, preferences):
    """A compact screen view; the saved report retains full source notes."""
    lines = ['YOUR WALK SUGGESTIONS', '-' * WIDTH,
             f"Up to {preferences['max_minutes']:g} min | Grade {preferences['max_grade']} or below"]
    if preferences['max_distance'] is not None:
        lines.append(f"Distance limit: {preferences['max_distance']:g} km")
    no_preferences = all(preferences.get(key, 'any') == 'any'
                         for key in ('mood', 'scenery', 'route'))
    lines.append('Ordered by walking time, then name.' if no_preferences else
                 'Ordered by how well they match your preferences, then walking time.')
    for index, result in enumerate(results[:3], 1):
        trail = result['trail']
        gain = (f"about {trail['elevation_gain_m']} m ascent"
                if trail['elevation_gain_m'] is not None else 'ascent estimate unavailable')
        lines.extend(['', wrapped(f"{index}. {trail['name']}", ''),
                      wrapped(f"{trail['distance_km']:g} km {trail['route']} | "
                              f"{trail['minutes']} min | Grade {trail['grade']} | {gain}"),
                      wrapped(trail['description'])])
        matches = []
        if preferences['mood'] != 'any' and trail['mood'] == preferences['mood']:
            matches.append('your mood')
        if preferences['scenery'] != 'any' and preferences['scenery'] in trail['scenery']:
            matches.append(preferences['scenery'])
        if preferences.get('route', 'any') != 'any' and trail['route'] == preferences['route']:
            matches.append('route style')
        if matches:
            lines.append(wrapped('Matches: ' + ', '.join(matches) + '.'))
        for note in trade_offs(trail, preferences):
            lines.append(wrapped('Note: ' + note))
        lines.append(wrapped('Getting there: ' + trail['transport_note']))
        # The first two reminders are shared by every walk; show them once below.
        for note in preparation(trail, True)[2:]:
            if not note.startswith('One-way'):
                lines.append(wrapped('Prepare: ' + note))
    lines.extend(['', 'BEFORE YOU GO', wrapped('Bring water, suitable shoes and weather protection. '
                  'Check current track notices and weather; tell someone your plans.', ''),
                  'Browse Walks has full details and sources. Saved reports include them too.'])
    return '\n'.join(lines)


def format_results(results, preferences, ready):
    lines = ['Blue Mountains Handbook — Personalised Bushwalking & Local Guide',
             'Find a walk that fits your day.', wrapped(NOTICE, ''), ALERTS,
             'Council-managed tracks: ' + COUNCIL, '', 'Your preferences:']
    labels = {'max_minutes': 'Walking time limit (minutes)', 'max_distance': 'Distance limit (km)',
              'max_grade': 'Maximum grade', 'transport': 'Transport', 'scenery': 'Scenery',
              'mood': 'Mood', 'route': 'Route style'}
    for key, value in preferences.items():
        if value is None or value == 'any':
            value = 'No preference'
        elif isinstance(value, float):
            value = f'{value:g}'
        lines.append(f'{labels[key]}: {value}')
    lines.append('Prepare water, suitable shoes and weather protection before leaving.')
    lines.extend(['', 'YOUR BEST MATCHES', '-' * WIDTH])
    lines.append('Scores measure preference fit, not safety or track availability.')
    for index, result in enumerate(results[:3], 1):
        trail = result['trail']
        lines.extend(['', f'{index}. Match score: {result["score"]}/100', trail_text(trail)])
        lines.append('  Why it suits you:')
        lines.extend(wrapped('+ ' + reason, '    ') for reason in result['reasons'])
        notes = trade_offs(trail, preferences)
        if notes:
            lines.append('  Trade-offs:')
            lines.extend(wrapped('- ' + note, '    ') for note in notes)
        lines.append('  Preparation:')
        lines.extend(wrapped('- ' + note, '    ') for note in preparation(trail, ready))
    return '\n'.join(lines) + '\n'


def save_report(report, directory=BASE_DIR):
    """Append a session to one readable file; previous sessions are preserved."""
    path = Path(directory) / 'saved_recommendations.txt'
    with path.open('a', encoding='utf-8') as destination:
        destination.write(report + '\n' + '-' * 60 + '\n')
    return path


def find_walk(trails):
    while True:
        preferences = collect_preferences()
        results = recommend(trails, preferences)
        if not results:
            print('\nNo walks match your current limits. Your limits have not changed.')
            longer = time_alternatives(trails, preferences)
            if longer:
                minutes = min(trail['minutes'] for trail in longer)
                print(wrapped(f'The shortest walks within your other limits need {minutes} minutes. '
                              'Times use the upper end of the published range.', ''))
                names = [trail['name'] for trail in longer if trail['minutes'] == minutes]
                print(wrapped('Options: ' + '; '.join(names[:3]), ''))
                if choose(f'Allow {minutes} minutes instead?', ['yes', 'no']) == 'yes':
                    preferences['max_minutes'] = minutes
                    results = recommend(trails, preferences)
            else:
                print('Try a different distance or difficulty, or explore Browse Walks.')
            if not results:
                if choose('Try another search?', ['yes', 'no']) == 'yes':
                    continue
                return
        print('\n' + short_results(results, preferences))
        if choose('Save a full report to a text file?', ['yes', 'no']) == 'yes':
            try:
                print('Saved to:', save_report(format_results(results, preferences, True)))
            except OSError as error:
                print(f'Could not save results: {error}. Results remain above.')
        return


def main():
    heading('BLUE MOUNTAINS HANDBOOK')
    print('Personalised Bushwalking & Local Guide')
    print('Find a walk that fits your day.\n')
    print(wrapped(NOTICE, ''))
    print(ALERTS)
    print('Council-managed tracks:', COUNCIL)
    try:
        locations, trails = load_catalogue()
    except (OSError, ValueError, csv.Error) as error:
        print(f'Could not load catalogue: {error}')
        print('Check locations.csv and trails.csv in the project folder.')
        return 1
    print(f'\n{len(locations)} towns | {len(trails)} walks | No internet needed to run')
    try:
        while True:
            print('\n1. Find a Walk for Me\n2. Browse Walks\n3. Explore Blue Mountains\n4. Exit')
            choice = choose('Choose a menu item', ['1', '2', '3', '4'])
            if choice == '1':
                find_walk(trails)
            elif choice == '2':
                browse(locations, trails)
            elif choice == '3':
                explore(locations, trails)
            else:
                print('Goodbye!')
                return 0
    except (EOFError, KeyboardInterrupt):
        print('\nGoodbye!')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
