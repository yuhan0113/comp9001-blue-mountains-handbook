"""Simple, explainable filtering and scoring using lists and dictionaries."""
from data_loader import MOODS, SCENERY, positive_number


def validate_preferences(preferences):
    positive_number(preferences['max_minutes'])
    if preferences['max_distance'] is not None:
        positive_number(preferences['max_distance'])
    if preferences['max_grade'] not in range(1, 6):
        raise ValueError('Maximum grade must be 1 to 5')
    if preferences.get('route', 'any') not in ('any', 'loop', 'return', 'one-way'):
        raise ValueError('Unknown route preference')
    if preferences['transport'] not in ('car', 'public'):
        raise ValueError('Transport must be car or public')
    if preferences['scenery'] not in SCENERY + ('any',):
        raise ValueError('Unknown scenery preference')
    if preferences['mood'] not in MOODS + ('any',):
        raise ValueError('Unknown mood preference')


def exclusion_reasons(trail, preferences):
    """Hard limits are never overridden by a high preference score."""
    reasons = []
    if trail['minutes'] > preferences['max_minutes']:
        reasons.append('exceeds time limit')
    if preferences['max_distance'] is not None and trail['distance_km'] > preferences['max_distance']:
        reasons.append('exceeds distance limit')
    if trail['grade'] is None:
        reasons.append('numeric grade unverified; available in Browse Walks only')
    elif trail['grade'] > preferences['max_grade']:
        reasons.append('exceeds maximum grade')
    if preferences['transport'] == 'public' and not trail['public_transport']:
        reasons.append('public transport access not included in this catalogue')
    return reasons


def score_trail(trail, preferences):
    """40 points for eligibility, then scenery (30), mood (20) and route (10)."""
    score = 40
    reasons = ['Fits your walking time, distance, grade and access limits (+40)']
    if preferences['scenery'] == 'any':
        score += 30
        reasons.append('No scenery preference; equal scenery points (+30)')
    elif preferences['scenery'] in trail['scenery']:
        score += 30
        reasons.append(f"Matches your {preferences['scenery']} preference (+30)")
    if preferences['mood'] == 'any':
        score += 20
        reasons.append('No mood preference; equal mood points (+20)')
    elif preferences['mood'] == trail['mood']:
        score += 20
        reasons.append(f"Matches your {trail['mood']} mood (+20)")
    route = preferences.get('route', 'any')
    if route == 'any' or route == trail['route']:
        score += 10
        reasons.append('Route matches, or no route preference (+10)')
    return score, reasons


def trade_offs(trail, preferences):
    """Explain unmet soft preferences without excluding the walk."""
    notes = []
    if preferences['scenery'] != 'any' and preferences['scenery'] not in trail['scenery']:
        notes.append(f"Does not have the requested {preferences['scenery']} scenery tag.")
    if preferences['mood'] != 'any' and preferences['mood'] != trail['mood']:
        notes.append(f"Tagged {trail['mood']}, rather than your {preferences['mood']} mood.")
    if preferences.get('route', 'any') not in ('any', trail['route']):
        notes.append(f"This is a {trail['route']} walk, not your preferred route style.")
    if preferences['transport'] == 'public':
        notes.append('Check the access note: additional transfers may be outside the stated walking figures.')
    if trail['route'] == 'one-way':
        notes.append('The stated distance and time do not include a return journey.')
    return notes


def recommend(trails, preferences):
    """Return all eligible matches, highest score first; ties favour shorter walks."""
    validate_preferences(preferences)
    results = []
    for trail in trails:
        if not exclusion_reasons(trail, preferences):
            score, reasons = score_trail(trail, preferences)
            results.append({'trail': trail, 'score': score, 'reasons': reasons})
    return sorted(results, key=lambda result: (
        -result['score'], result['trail']['minutes'], result['trail']['name']))


def preparation(trail, ready):
    notes = ['Bring drinking water, sun protection, suitable shoes and weather layers.',
             'Check NPWS and council track notices and weather; tell someone your plans.']
    if trail['minutes'] >= 180:
        notes.append('Allow a full walking session; pack food and an offline map.')
    if trail['grade'] is None or trail['grade'] >= 3:
        notes.append('Expect uneven surfaces and steps; assess your fitness and experience.')
    if trail['route'] == 'one-way':
        notes.append('One-way figures only: arrange pickup or allow extra time and distance to return.')
    if trail['id'] == 'night-lit':
        notes.append('Bring a torch; confirm lighting hours and closures with council. Keep to the lit route.')
    if trail['id'] == 'grand-canyon':
        notes.append('Do not enter the canyon before, during or after heavy rain; check NPWS advice.')
    if trail['id'] == 'lockley-pylon':
        notes.append('Exposed terrain: check the official navigation and equipment advice.')
    if trail['id'] == 'porters-pass':
        notes.append('Steep cliff passes and slippery ledges: check council notices and route notes.')
    if not ready:
        notes.append('You reported missing basic gear: prepare before undertaking any walk.')
    return notes


def time_alternatives(trails, preferences):
    """Find walks blocked only by time, without changing the user's limits."""
    return sorted([trail for trail in trails
                   if exclusion_reasons(trail, preferences) == ['exceeds time limit']],
                  key=lambda trail: (trail['minutes'], trail['name']))
