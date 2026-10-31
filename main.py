"""Blue Mountains Handbook: run with python3 main.py."""
import csv
import textwrap
from pathlib import Path

from data_loader import BASE_DIR, MOODS, SCENERY, load_catalogue, positive_number
from recommendations import exclusion_reasons, preparation, recommend, trade_offs

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


def choose(prompt, options):
    """Accept a displayed number or its text label; keep validation in one place."""
    print('\n' + prompt)
    numbered = not all(option.isdigit() for option in options)
    if numbered:
        for index, option in enumerate(options, 1):
            label = option.replace('-', ' ').capitalize()
            if option == 'any':
                label = 'No preference'
            print(f'  {index}. {label}')
    while True:
        answer = input('Your choice: ').strip().lower()
        if answer in options:
            return answer
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
             f"{duration} | Grade {trail['grade']}/5",
             wrapped(trail['description']),
             wrapped(f"Scenery: {', '.join(trail['scenery'])} | Mood: {trail['mood']}"),
             wrapped('Access: ' + trail['transport_note']),
             '  Source: ' + trail['source']]
    return '\n'.join(lines)


def explore(locations, trails):
    heading('EXPLORE BLUE MOUNTAINS')
    options = ['all'] + [location['id'] for location in locations] + ['back']
    selected = choose('Choose an area', options)
    for location in locations:
        if selected not in ('all', location['id']):
            continue
        print(f"\n{location['name']} | NSW {location['postcode']}")
        print(wrapped(location['description']))
        print(wrapped('History: ' + location['history']))
        print('  History source:', location['source'])
        print('  Walks in this catalogue:')
        for trail in trails:
            if trail['location_id'] == location['id']:
                print(wrapped('- ' + trail['name'], '    '))


def browse(locations, trails):
    heading('BROWSE WALKS')
    location_id = choose('Choose an area', ['all'] + [item['id'] for item in locations] + ['back'])
    if location_id == 'back':
        return
    selected = []
    for trail in trails:
        if location_id == 'all' or trail['location_id'] == location_id:
            selected.append(trail)
    if not selected:
        print('No walks are listed for this area yet.')
        return
    while True:
        print('\nWalks in this area:')
        for index, trail in enumerate(selected, 1):
            print(wrapped(f'{index}. {trail["name"]} | {trail["distance_km"]:g} km | '
                          f'{trail["minutes"]} min | Grade {trail["grade"]}'))
        print('  0. Back to main menu')
        choice = choose('View details for a walk', [str(i) for i in range(len(selected) + 1)])
        if choice == '0':
            return
        print('\n' + trail_text(selected[int(choice) - 1]))
        print('-' * WIDTH)


def collect_preferences():
    heading('FIND A WALK FOR ME')
    print('Enter limits for the walk itself, excluding travel and breaks.')
    print('Grades: 1 easiest to 5 most demanding. Check official track details.')
    return {
        'max_minutes': ask_number('Maximum walking time in minutes: '),
        'max_distance': ask_number('Maximum walking distance in km: '),
        'max_grade': ask_number('Maximum track grade (1-5): ', whole=True, maximum=5),
        'transport': choose('Transport', ['car', 'public']),
        'scenery': choose('Preferred scenery', ['any'] + list(SCENERY)),
        'mood': choose('How are you feeling today?', ['any'] + list(MOODS)),
        'route': choose('Preferred route style', ['any', 'loop', 'return', 'one-way']),
    }


def format_results(results, preferences, ready):
    lines = ['Blue Mountains Handbook — Personalised Bushwalking & Local Guide',
             'Find a walk that fits your day.', wrapped(NOTICE, ''), ALERTS,
             'Council-managed tracks: ' + COUNCIL, '', 'Your preferences:']
    labels = {'max_minutes': 'Walking time limit (minutes)', 'max_distance': 'Distance limit (km)',
              'max_grade': 'Maximum grade', 'transport': 'Transport', 'scenery': 'Scenery',
              'mood': 'Mood', 'route': 'Route style'}
    lines.extend(f'{labels[key]}: {value}' for key, value in preferences.items())
    lines.append(f'Basic gear ready: {"yes" if ready else "no"}')
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
    preferences = collect_preferences()
    ready = choose('Do you have water, suitable shoes and weather protection ready?',
                   ['yes', 'no']) == 'yes'
    results = recommend(trails, preferences)
    if not results:
        print('\nNo walks match all your limits. No limits have been relaxed.')
        for trail in trails:
            print(f'  {trail["name"]}: {"; ".join(exclusion_reasons(trail, preferences))}')
        print('Return to the menu to try different preferences.')
        return
    report = format_results(results, preferences, ready)
    print('\n' + report)
    if choose('Save these results to a text file?', ['yes', 'no']) == 'yes':
        try:
            print('Saved to:', save_report(report))
        except OSError as error:
            print(f'Could not save results: {error}. Results remain above.')


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
