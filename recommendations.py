"""Simple, explainable filtering and scoring using lists and dictionaries."""
from data_loader import MOODS, SCENERY, positive_number


def validate_preferences(preferences):
    for key in ('max_minutes', 'max_distance'):
        positive_number(preferences[key])
    if preferences['max_grade'] not in range(1, 6):
        raise ValueError('Maximum grade must be 1 to 5')
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
    if trail['distance_km'] > preferences['max_distance']:
        reasons.append('exceeds distance limit')
    if trail['grade'] > preferences['max_grade']:
        reasons.append('exceeds maximum grade')
    if preferences['transport'] == 'public' and not trail['public_transport']:
        reasons.append('public transport access not included in this catalogue')
    return reasons


def score_trail(trail, preferences):
    """Eligible walks receive 50 base points plus scenery (30) and mood (20)."""
    score = 50
    reasons = ['Within your time, distance, grade and transport limits (+50)']
    if preferences['scenery'] == 'any' or preferences['scenery'] in trail['scenery']:
        score += 30
        reasons.append('Scenery matches, or no scenery preference (+30)')
    if preferences['mood'] == 'any' or preferences['mood'] == trail['mood']:
        score += 20
        reasons.append('Mood matches, or no mood preference (+20)')
    return score, reasons


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
             'Check official alerts and weather; tell someone your plans.']
    if trail['minutes'] >= 180:
        notes.append('Allow a full walking session; pack food and an offline map.')
    if trail['grade'] >= 3:
        notes.append('Expect uneven surfaces and steps; assess your fitness and experience.')
    if trail['route'] == 'one-way':
        notes.append('One-way figures only: arrange pickup or allow extra time and distance to return.')
    if trail['id'] == 'grand-canyon':
        notes.append('Do not enter the canyon before, during or after heavy rain; check NPWS advice.')
    if not ready:
        notes.append('You reported missing basic gear: prepare before undertaking any walk.')
    return notes
