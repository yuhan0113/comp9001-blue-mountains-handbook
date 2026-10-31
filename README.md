# USYD COMP9001 Final Project - Blue Mountains Handbook
## Personalised Bushwalking & Local Guide

**Find a walk that fits your day.**

**University:** The University of Sydney  
**Student:** Yu-Han Chang  
**Student ID:** 540140295  
**Tutorial:** Activity 01 - Niousha Nazemi  
**Github Repository (Private):** https://github.com/yuhan0113/comp9001-blue-mountains-handbook

## Run the program

Use Python 3.9 or later. No third-party packages, installation or internet connection are needed to run the program.

From this project folder:

```sh
python3 main.py
```

The terminal menu lets you:

1. Find a Walk for Me: enter preferences and receive up to three explained recommendations.
2. Browse Walks: choose an area, then select a walk for its details; enter `0` to return.
3. Explore Blue Mountains: discover 14 towns, with postcodes, brief history, things to do, food/supply notes and local or nearby walks.
4. Exit. Ctrl+C or end-of-input also exits cleanly.

Choose menu option `1` and try: `active`, `forest`, `300` minutes, `moderate`, `car`, then `yes` to set extra preferences, `10` km and `loop`. Grand Canyon track ranks first. Choose `yes` to save a full report, or `no` to return to the menu.

The questions start with mood and scenery, followed by time, difficulty and transport. Difficulty uses three project-defined categories: Easy, Moderate and Hard. Easy only includes Easy walks, Moderate includes Easy and Moderate walks, and Hard allows all three categories. Distance and route style are optional; selecting `no` leaves distance unrestricted and route style as no preference. Mood affects ranking, not your difficulty limit. Packing advice appears with the results instead of an extra gear question.

The CSV files are found relative to `main.py`, so running the script from another working directory also works.

## Which files do what?

- `main.py`: menu, input validation, readable output, preparation questions and report saving.
- `data_loader.py`: reads CSV files, converts numbers and booleans, validates data and location references.
- `recommendations.py`: hard-limit filtering, preference scoring, sorting and preparation suggestions.
- `trails.csv`: eighteen walks with distance, duration, difficulty, route type, tags, access notes and source URLs.
- `locations.csv`: fourteen towns with postcodes, descriptions, history notes and source URLs.
- `tests.py`: standard-library `unittest` checks covering logic, file handling and terminal interactions.
- `saved_recommendations.txt`: created only when you choose to save; subsequent sessions append instead of overwriting. This personal output is ignored by Git.

## How recommendations work

First, exclude any walk exceeding the user's maximum walking time, optional distance or selected difficulty. If the user chooses public transport, also exclude records without public transport support in this small catalogue. Limits are inclusive: a 60-minute walk fits a 60-minute limit. The program never relaxes a limit silently.

Then score each eligible walk:

- 40 points for meeting all four hard limits.
- 30 points if the scenery matches, or the user selected `any`.
- 20 points if the mood matches, or the user selected `any`.
- 10 points if the route style matches, or the user selected `any`.

Sort by descending score, then ascending duration, then alphabetical name. Display the first three. The score is a transparent preference heuristic, not a probability, safety rating or claim that a track is currently open. All eligible walks get at least 40 points. Unmatched scenery, mood and route preferences are shown as trade-offs; they never exclude a walk. Selecting `any` gives equal points to every walk for that factor.

If there are no matches, look for walks blocked only by time. Show the shortest required time and ask before changing it; distance, difficulty and transport limits stay unchanged. Declining keeps the original limits. The user can retry the questionnaire or return to the menu. No long list of rejected walks is printed.

The screen shows brief walk suggestions, matching preferences, trade-offs and access notes. Packing advice appears once, with route-specific preparation where needed. Full scoring explanations and source notes remain in saved reports and walk details. With no soft preferences, the screen explains that results are ordered by time and name rather than advertising a perfect match score.

## Data and modelling decisions

The original five trail records were checked against NSW National Parks on **27 October 2026**. The six additional records and two additional town histories were checked on **31 October 2026**, using the sources below. Council and specialist walking sources supplement NPWS where needed. The stored duration uses the upper end of each published time range; this is an estimate, not a guaranteed completion time. Breaks, travel, delays and extra return journeys are excluded.

- [Three Sisters walk](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/three-sisters-walk): 0.8 km return, up to 45 minutes.
- [Fairfax Heritage walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/fairfax-heritage-walking-track): 1.8 km **one-way**, up to 45 minutes. Arrange pickup or allow additional time and distance to return; the program does not calculate a return itinerary.
- [Princes Rock walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/princes-rock-walking-track): 1.8 km return, up to 60 minutes.
- [Wentworth Falls track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/wentworth-falls-track): 1.4 km return, up to 60 minutes.
- [Grand Canyon track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/grand-canyon-track): 6.3 km loop, up to 240 minutes.


- [South Lawson Waterfall Circuit](https://www.visitbluemountains.com.au/plan/bushwalks): 3.5 km circuit, up to 120 minutes. This regional tourism page describes it as three kilometres in prose but gives 3.5 km in its fact list; the catalogue uses the longer stated figure. Access from Lawson station adds walking outside these figures.
- [Gordon Falls to Katoomba walk](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/gordon-falls-to-katoomba-walk/visitor-info): 8 km one-way, up to 240 minutes. The source identifies 1.8 km access from Leura station and 2.5 km from Scenic World to Katoomba station, with a bus alternative at Scenic World.
- [Cliff Top walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/cliff-top-walking-track): 6 km return, up to 210 minutes.
- [Pulpit walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/pulpit-walking-track): 7 km return, up to 180 minutes.
- [Lockley Pylon walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/lockley-pylon-walking-track): 7 km return, up to 180 minutes. Grouped under Leura for road access; NPWS categorises it within its Blackheath park area.
- [Walls Ledge–Porters Pass–Centennial Glen circuit](https://www.wildwalks.com.au/bushwalking-and-hiking-in-nsw/blue-mountains-blackheath-/walls-ledge-porters-pass-centennial-glen-circuit): 5.4 km circuit, 210 minutes and approximately 473 m published climb from Wildwalks, a specialist route guide rather than the land manager. These values describe that specific circuit; different combinations of nearby tracks have different lengths. Check council notices as well.

The catalogue includes areas from the project owner's walking experience: South Lawson, Wentworth Falls, Grand Canyon and Centennial Glen/Porters Pass. Personal activity times and GPS distances are not used as route facts or completion-time promises. Mount Taylor (ACT) and Berowra are outside this regional scope; the unnamed Blue Mountains activity cannot identify a specific route.

Scenery and mood tags are project-authored categories. Difficulty is also a project-defined comparison category: Easy, Moderate or Hard. It is not an official track grading system. The classification uses the cited route descriptions, distance, duration and terrain information so walks from different publishers can be compared consistently within this project.

Transport is deliberately simplified. Transport-enabled routes include Three Sisters, South Lawson, Gordon Falls to Katoomba, the night-lit walk, Florabella Pass, the Victory/Sassafras route, Woodford Creek and Horseshoe Falls. Access notes describe extra station or bus-stop transfers; those are not included in the hard walking limits. A `no` value means access is **not modelled in this catalogue**, not that public transport is impossible. No timetable, transfer distance or fare is calculated. Car selection also requires the user to arrange suitable trailhead access and any pickup. Check [Transport for NSW Trip Planner](https://transportnsw.info/trip) for actual journeys.

Short history summaries are paraphrased from [Blue Mountains Local Studies](https://bluemlocalstudies.wordpress.com/2016/04/26/katoomba-street-history-walk/), [Powerhouse Collection](https://collection.powerhouse.com.au/object/31124), and the [Wentworth Falls Chamber of Commerce](https://www.wentworthfalls.org.au/history-of-wentworth-falls/). Leura and Lawson history notes come from the [Dictionary of Sydney: Leura](https://dictionaryofsydney.org/index.php/entry/leura) and [Lawson](https://dictionaryofsydney.org/entry/lawson). Each town's source is also in its CSV row.

This is an offline educational guide. It does not check current closures, weather, fire conditions, personal fitness or accessibility requirements. Consult the relevant track pages, [Blue Mountains City Council](https://www.bmcc.nsw.gov.au/) notices and [NPWS alerts](https://www.nationalparks.nsw.gov.au/alerts/alerts-list) before walking. The project difficulty category does not establish wheelchair or pram access. Grand Canyon has specific heavy-rain advice on its official page.

## Editing the data

Open the CSV files in a text editor or spreadsheet editor and retain the exact header order. Quote any cell containing a comma. Use unique, non-empty IDs and ensure each trail's `location_id` exists in `locations.csv`.

- `distance_km`: a positive finite number.
- `minutes`: a positive whole number.
- `difficulty`: one of `easy`, `moderate` or `hard`. This is a project-defined comparison category, not an official difficulty rating.
- `elevation_gain_m`: a non-negative whole number of metres climbed, or `unknown`. Never use zero to mean missing.
- `elevation_source`: the exact source for the climb estimate, or an explanation of missing data.
- `data_note`: route-specific qualifications, source differences and grading context.
- Town fields `things_to_do`, `visitor_source`, `food_supplies` and `food_source` hold short visitor notes and their references.
- Town `nearby_walk_ids`: pipe-separated existing trail IDs, or `none`; these are explicitly labelled nearby/connecting routes.
- `route`: `return`, `loop` or `one-way`.
- `scenery`: one or more of `views`, `waterfalls`, `forest`, separated with `|`.
- `mood`: `relaxed`, `exploring` or `active`.
- `public_transport`: `yes` or `no`.
- Postcodes: four digits; all text fields must be populated.

Missing files, malformed rows, invalid values, duplicate IDs and unknown locations produce a startup error rather than partial recommendations. Correct the data and restart. Saving errors are reported without closing the menu.

## Tests

```sh
python3 tests.py
```

Alternatively:

```sh
python3 -m unittest discover -v
```

The tests include exact filter boundaries, deterministic ties, route preference ranking, the South Lawson profile, town filtering, numbered menu choices, matching and non-matching preferences, no results, transport restrictions, invalid numeric input (including infinity and NaN), corrupt CSV records, missing files, report append/read-back, save failures, clean exits and a complete menu session launched from a different directory. Test files and saved reports use temporary folders; the bundled catalogue is not modified.

## COMP9001 concepts and review guide

The implementation uses functions, loops, conditionals, strings, lists, dictionaries, sets, sorting and exceptions. File I/O and program testing are the two planned advanced topics. There is no database, web application, external API or machine learning dependency. The interface uses standard-library `textwrap` and plain separators; no colour or terminal packages are required. Menus accept numbers or the displayed option keywords. Three mood tags keep the model easy to explain. Fixed-width f-strings align numeric browse columns; long names wrap in the name column without moving the figures. Crowd predictions and extra questionnaire factors are intentionally omitted to keep the demo concise.

Suggested reading order:

1. Follow `main()` in `main.py` through one menu session.
2. Read `load_catalogue()` and compare a raw CSV row with the converted dictionary.
3. Trace `exclusion_reasons()`, `score_trail()` and `recommend()` using the example above.
4. Change one preference and predict which walks disappear or change score.
5. Read `preparation()` and `save_report()`; save two sessions and inspect the output.
6. Run `tests.py`, then add a test when changing a scoring rule or adding a walk.


## Town and walk expansion — 31 October 2026

The guide now contains 14 towns and 18 distinct walks. New towns are Glenbrook, Blaxland, Warrimoo, Valley Heights, Springwood, Faulconbridge, Linden, Woodford and Hazelbrook. This is a curated selection, not a measured popularity ranking. There is no three-walk quota.

Warrimoo links to the Blaxland-to-Warrimoo route. Valley Heights points to nearby Birdwood Gully in Springwood, and Linden points to the nearby Hazelbrook-to-Woodford walk. These are explicitly labelled nearby, not invented local routes. Shared routes are stored once. The Norman Lindsay Gallery is correctly listed in **Faulconbridge**, although it is often associated with the Springwood area.

New walk sources and exact variants:

- [Katoomba Falls Night-lit Walk](https://www.visitbluemountains.com.au/plan/bushwalks): 1.5 km, up to 60 minutes return in the regional tourism guide. The [NSW Government listing](https://www.nsw.gov.au/visiting-and-exploring-nsw/locations-and-attractions/katoomba-falls-night-lit-walk) instead states 1.3 km. The longer tourism planning figure is used and the discrepancy is shown in the walk details. Paths include steps; no lighting timetable or accessibility guarantee is made. Check council notices and carry a torch.
- [Jellybean track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/jellybean-track): NPWS 1 km return, 30–60 minutes.
- [Blaxland to Warrimoo via Florabella Pass](https://www.wildwalks.com/bushwalking-and-hiking-in-nsw/glenbrook-eastern-blue-mountains/blaxland-to-warrimoo-station-florabella-pass): Wildwalks 6 km one-way, 180 minutes and 406 m total climbing. These figures include the publisher's described detour, not every possible Florabella variant.
- [Faulconbridge to Springwood via Sassafras Gully](https://www.wildwalks.com/bushwalking-and-hiking-in-nsw/blue-mountains-springwood/faulconbridge-to-springwood-via-sassafras-gully): Wildwalks 6.1 km one-way, 180 minutes and 338 m total climbing.
- [Woodford Creek walk](https://walkingvolunteers.org.au/walks/woodford-creek-walk/): Walking Volunteers 7.1 km one-way and 180 minutes excluding breaks. It starts at Hazelbrook station and ends at Woodford station. It is not the Woodford–Oaks cycling trail.
- [Birdwood Gully](https://www.bushtrackers.com.au/guides-maps/35-birdwood-gully-walk): Bush Trackers 2.6 km and 90 minutes. This is a loop; the project classifies it as Moderate for comparison.
- [Horseshoe Falls](https://www.bushtrackers.com.au/guides-maps/13-horseshoe-falls-walk): Bush Trackers 1 km and 60 minutes. The [route map](https://www.bushtrackers.com.au/images/pdf-guides/Horseshoe-Falls.pdf) describes the loop and station approach. Longer Burgess Falls routes are different walks.

Birdwood Gully and Horseshoe Falls are classified as Moderate within the project difficulty system and can participate in recommendations.

### Elevation gain and data quality

Elevation gain means cumulative ascent in metres, not altitude or net height change. It is displayed as additional planning information and does not affect recommendation scores.

An elevation value is stored only when the cited source provides a suitable estimate for the same specific route represented in the catalogue. Where route variants, starting points or GPS measurements produce incompatible figures, elevation remains `unknown` rather than combining different routes.

The following catalogue routes currently retain published climb estimates:

- Walls Ledge–Porters Pass–Centennial Glen circuit: approximately 473 m.
- Blaxland to Warrimoo via Florabella Pass: approximately 406 m.
- Faulconbridge to Springwood via Sassafras Gully: approximately 338 m.

Missing elevation appears as `--` in the browse table. Elevation is informational only and does not affect recommendation scoring.

Source checks establish the published route description, not that a route is open today. Check current NPWS and council notices before departure.

### Town stops

Katoomba includes [Yellow Deli](https://www.yellowdeli.com/katoomba), 214 Katoomba Street, using the business's own location page. No fixed opening hours are stored. Other highlights include [Everglades](https://www.nationaltrust.org.au/places/everglades-house-gardens/), [Norman Lindsay Gallery](https://www.nationaltrust.org.au/places/norman-lindsay-gallery/), [Woodford Academy](https://www.nationaltrust.org.au/places/woodford-academy/), [Valley Heights museum](https://mgnsw.org.au/organisations/valley-heights-locomotive-depot-heritage-museum/) and [Linden Observatory](https://www.lindenobservatory.org.au/). The observatory is appointment/event-only. Town pages include reference links; supply notes are planning suggestions, not live shop inventories. Check business hours and any booking requirements directly.
