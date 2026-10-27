"""Blue Mountains Handbook: run with python3 main.py."""
import csv
from pathlib import Path

from data_loader import BASE_DIR, MOODS, SCENERY, load_catalogue, positive_number
from recommendations import exclusion_reasons, preparation, recommend

NOTICE = ('Offline study guide: track status is unknown. Check current NPWS alerts, '
          'weather and access before walking. Times exclude travel, breaks and delays.')
ALERTS = 'https://www.nationalparks.nsw.gov.au/alerts/alerts-list'


def choose(prompt, options):
    while True:
        answer = input(f'{prompt} ({" / ".join(options)}): ').strip().lower()
        if answer in options:
            return answer
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
    return (f'{trail["name"]} [{trail["id"]}]\n'
            f'  {trail["distance_km"]:g} km {trail["route"]}; '
            f'allow {trail["minutes"]} minutes; grade {trail["grade"]}/5\n'
            f'  {trail["description"]}\n'
            f'  Scenery: {", ".join(trail["scenery"])}; mood: {trail["mood"]}\n'
            f'  Access: {trail["transport_note"]}\n'
            f'  Official details: {trail["source"]}')


def explore(locations, trails):
    for location in locations:
        print(f'\n{location["name"]} ({location["postcode"]})')
        print(location['description'])
        print('History:', location['history'])
        print('History source:', location['source'])
        print('Nearby walks:', ', '.join(trail['name'] for trail in trails
                                        if trail['location_id'] == location['id']))


def browse(locations, trails):
    print('Locations:', ', '.join(location['id'] for location in locations))
    location_id = choose('Choose location', ['all'] + [item['id'] for item in locations])
    for trail in trails:
        if location_id == 'all' or trail['location_id'] == location_id:
            print('\n' + trail_text(trail))


def collect_preferences():
    print('\nEnter limits for the walk itself, excluding travel and breaks.')
    print('Grades: 1 easiest to 5 most demanding. Check official track details.')
    return {
        'max_minutes': ask_number('Maximum walking time in minutes: '),
        'max_distance': ask_number('Maximum walking distance in km: '),
        'max_grade': ask_number('Maximum track grade (1-5): ', whole=True, maximum=5),
        'transport': choose('Transport', ['car', 'public']),
        'scenery': choose('Preferred scenery', ['any'] + list(SCENERY)),
        'mood': choose('Your mood', ['any'] + list(MOODS)),
    }


def format_results(results, preferences, ready):
    lines = ['Blue Mountains Handbook — Personalised Bushwalking & Local Guide',
             'Find a walk that fits your day.', NOTICE, ALERTS, '', 'Your preferences:']
    lines.extend(f'{key}: {value}' for key, value in preferences.items())
    lines.append(f'Basic gear ready: {"yes" if ready else "no"}')
    lines.append('Scores measure preference fit, not safety or track availability.')
    for index, result in enumerate(results[:3], 1):
        trail = result['trail']
        lines.extend(['', f'{index}. Match score: {result["score"]}/100', trail_text(trail)])
        lines.extend('  ' + reason for reason in result['reasons'])
        lines.extend('  Preparation: ' + note for note in preparation(trail, ready))
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
    print('\nBlue Mountains Handbook — Personalised Bushwalking & Local Guide')
    print('Find a walk that fits your day.\n')
    print(NOTICE)
    print(ALERTS)
    try:
        locations, trails = load_catalogue()
    except (OSError, ValueError, csv.Error) as error:
        print(f'Could not load catalogue: {error}')
        print('Check locations.csv and trails.csv in the project folder.')
        return 1
    try:
        while True:
            print('\n1. Explore locations\n2. Browse walks\n3. Find a walk\n4. Exit')
            choice = choose('Choose a menu item', ['1', '2', '3', '4'])
            if choice == '1':
                explore(locations, trails)
            elif choice == '2':
                browse(locations, trails)
            elif choice == '3':
                find_walk(trails)
            else:
                print('Goodbye!')
                return 0
    except (EOFError, KeyboardInterrupt):
        print('\nGoodbye!')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
