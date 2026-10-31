"""Read and validate the small CSV catalogue; no third-party packages needed."""
import csv
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCENERY = ('views', 'waterfalls', 'forest')
MOODS = ('relaxed', 'exploring', 'active')


def read_rows(path, fields):
    """Reject incomplete files instead of silently recommending from bad data."""
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f'{Path(path).name}: incorrect CSV header')
        rows = []
        seen = set()
        for row in reader:
            if None in row or any(value is None or not value.strip()
                                  for value in row.values()):
                raise ValueError(f'{Path(path).name}: incomplete row {reader.line_num}')
            row = {key: value.strip() for key, value in row.items()}
            if row['id'] in seen:
                raise ValueError(f'{Path(path).name}: duplicate ID {row["id"]}')
            seen.add(row['id'])
            rows.append(row)
        if not rows:
            raise ValueError(f'{Path(path).name}: no records')
        return rows


def positive_number(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError('Numbers must be finite and greater than zero')
    return number


def load_catalogue(directory=BASE_DIR):
    directory = Path(directory)
    locations = read_rows(directory / 'locations.csv',
                          ['id', 'name', 'postcode', 'description', 'history', 'source',
                           'things_to_do', 'visitor_source', 'food_supplies', 'food_source',
                           'nearby_walk_ids'])
    location_ids = {location['id'] for location in locations}
    for location in locations:
        if len(location['postcode']) != 4 or not location['postcode'].isdigit():
            raise ValueError(f'Invalid postcode for {location["name"]}')
    trails = read_rows(directory / 'trails.csv', [
        'id', 'name', 'location_id', 'distance_km', 'minutes', 'grade',
        'route', 'scenery', 'mood', 'public_transport', 'transport_note',
        'description', 'source', 'elevation_gain_m', 'elevation_source', 'data_note'])
    for trail in trails:
        try:
            trail['distance_km'] = positive_number(trail['distance_km'])
            trail['minutes'] = int(trail['minutes'])
            trail['grade'] = None if trail['grade'] == 'unknown' else int(trail['grade'])
            if trail['minutes'] <= 0 or (trail['grade'] is not None and trail['grade'] not in range(1, 6)):
                raise ValueError('Invalid time or grade')
            if trail['elevation_gain_m'] == 'unknown':
                trail['elevation_gain_m'] = None
            else:
                trail['elevation_gain_m'] = int(trail['elevation_gain_m'])
                if trail['elevation_gain_m'] < 0:
                    raise ValueError('Elevation gain cannot be negative')
            if trail['location_id'] not in location_ids:
                raise ValueError('Unknown location')
            if trail['route'] not in ('return', 'loop', 'one-way'):
                raise ValueError('Unknown route type')
            trail['scenery'] = trail['scenery'].split('|')
            if any(tag not in SCENERY for tag in trail['scenery']):
                raise ValueError('Unknown scenery')
            if trail['mood'] not in MOODS:
                raise ValueError('Unknown mood')
            if trail['public_transport'] not in ('yes', 'no'):
                raise ValueError('Transport must be yes or no')
            trail['public_transport'] = trail['public_transport'] == 'yes'
        except ValueError as error:
            raise ValueError(f'Trail {trail["id"]}: {error}') from error
    trail_ids = {trail['id'] for trail in trails}
    for location in locations:
        location['nearby_walk_ids'] = ([] if location['nearby_walk_ids'] == 'none'
                                       else location['nearby_walk_ids'].split('|'))
        if any(trail_id not in trail_ids for trail_id in location['nearby_walk_ids']):
            raise ValueError(f'Unknown nearby walk for {location["name"]}')
    return locations, trails
