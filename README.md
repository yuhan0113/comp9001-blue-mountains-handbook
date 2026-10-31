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
3. Explore Blue Mountains: discover Katoomba, Leura, Wentworth Falls, Blackheath and Lawson, with postcodes, brief history and nearby walks.
4. Exit. Ctrl+C or end-of-input also exits cleanly.

Choose menu option `1` and try: `300` minutes, `10` km, grade `3`, `car`, `forest`, `active`, `loop`, then `yes` for basic gear. Grand Canyon track ranks first with 100/100 preference points. Choose `yes` at the final prompt to save results, or `no` to return to the menu.

The CSV files are found relative to `main.py`, so running the script from another working directory also works.

## Which files do what?

- `main.py`: menu, input validation, readable output, preparation questions and report saving.
- `data_loader.py`: reads CSV files, converts numbers and booleans, validates data and location references.
- `recommendations.py`: hard-limit filtering, preference scoring, sorting and preparation suggestions.
- `trails.csv`: eleven walks with distance, duration, grade, route type, tags, access notes and source URLs.
- `locations.csv`: five towns with postcodes, descriptions, history notes and source URLs.
- `tests.py`: standard-library `unittest` checks covering logic, file handling and terminal interactions.
- `saved_recommendations.txt`: created only when you choose to save; subsequent sessions append instead of overwriting. This personal output is ignored by Git.

## How recommendations work

First, exclude any walk exceeding the user's maximum walking time, distance or track grade. If the user chooses public transport, also exclude records without public transport support in this small catalogue. Limits are inclusive: a 60-minute walk fits a 60-minute limit. The program never relaxes a limit silently.

Then score each eligible walk:

- 40 points for meeting all four hard limits.
- 30 points if the scenery matches, or the user selected `any`.
- 20 points if the mood matches, or the user selected `any`.
- 10 points if the route style matches, or the user selected `any`.

Sort by descending score, then ascending duration, then alphabetical name. Display the first three. The score is a transparent preference heuristic, not a probability, safety rating or claim that a track is currently open. All eligible walks get at least 40 points. Unmatched scenery, mood and route preferences are shown as trade-offs; they never exclude a walk. Selecting `any` gives equal points to every walk for that factor.

If there are no matches, explain why each walk was excluded and return to the menu. The user decides whether to change their preferences.

Basic gear readiness changes preparation messages, not the score. A user without basic gear is told to prepare before undertaking any walk. Longer, higher-grade and one-way walks receive additional notes.

## Data and modelling decisions

The original five trail records were checked against NSW National Parks on **27 October 2026**. The six additional records and two additional town histories were checked on **31 October 2026**, using the sources below. Council and specialist walking sources supplement NPWS where needed. The stored duration uses the upper end of each published time range; this is an estimate, not a guaranteed completion time. Breaks, travel, delays and extra return journeys are excluded.

- [Three Sisters walk](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/three-sisters-walk): 0.8 km return, 45 minutes, grade 1.
- [Fairfax Heritage walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/fairfax-heritage-walking-track): 1.8 km **one-way**, 45 minutes, grade 1. Arrange pickup or allow additional time and distance to return; the program does not calculate a return itinerary.
- [Princes Rock walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/princes-rock-walking-track): 1.8 km return, 60 minutes, grade 3.
- [Wentworth Falls track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/wentworth-falls-track): 1.4 km return, 60 minutes, grade 3.
- [Grand Canyon track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/grand-canyon-track): 6.3 km loop, 240 minutes, grade 3.


- [South Lawson Waterfall Circuit](https://www.visitbluemountains.com.au/plan/bushwalks): 3.5 km circuit, up to 120 minutes, grade 2. This regional tourism page describes it as three kilometres in prose but gives 3.5 km in its fact list; the catalogue uses the longer stated figure. Access from Lawson station adds walking outside these figures.
- [Gordon Falls to Katoomba walk](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/gordon-falls-to-katoomba-walk/visitor-info): 8 km one-way, 240 minutes, grade 3. The source identifies 1.8 km access from Leura station and 2.5 km from Scenic World to Katoomba station, with a bus alternative at Scenic World.
- [Cliff Top walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/cliff-top-walking-track): 6 km return, 210 minutes, grade 3.
- [Pulpit walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/pulpit-walking-track): 7 km return, 180 minutes, grade 3.
- [Lockley Pylon walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/lockley-pylon-walking-track): 7 km return, 180 minutes, grade 3. Grouped under Leura for road access; NPWS categorises it within its Blackheath park area.
- [Walls Ledge–Porters Pass–Centennial Glen circuit](https://www.wildwalks.com.au/bushwalking-and-hiking-in-nsw/blue-mountains-blackheath-/walls-ledge-porters-pass-centennial-glen-circuit): 5.4 km circuit, 210 minutes, grade 4 from Wildwalks, a specialist route guide rather than the land manager. These values describe that specific circuit; different combinations of nearby tracks have different lengths. Check council notices as well.

The catalogue includes areas from the project owner's walking experience: South Lawson, Wentworth Falls, Grand Canyon and Centennial Glen/Porters Pass. Personal activity times and GPS distances are not used as route facts or completion-time promises. Mount Taylor (ACT) and Berowra are outside this regional scope; the unnamed Blue Mountains activity cannot identify a specific route.

Scenery and mood tags are project-authored categories, not official NPWS classifications. Track grade is retained separately: a longer grade-3 walk can still require substantial effort.

Transport is deliberately simplified. Three Sisters, South Lawson and Gordon Falls to Katoomba are enabled for public transport planning. Access notes describe extra station or bus-stop transfers; those are not included in the hard walking limits. A `no` value means access is **not modelled in this catalogue**, not that public transport is impossible. No timetable, transfer distance or fare is calculated. Car selection also requires the user to arrange suitable trailhead access and any pickup. Check [Transport for NSW Trip Planner](https://transportnsw.info/trip) for actual journeys.

Short history summaries are paraphrased from [Blue Mountains Local Studies](https://bluemlocalstudies.wordpress.com/2016/04/26/katoomba-street-history-walk/), [Powerhouse Collection](https://collection.powerhouse.com.au/object/31124), and the [Wentworth Falls Chamber of Commerce](https://www.wentworthfalls.org.au/history-of-wentworth-falls/). Leura and Lawson history notes come from the [Dictionary of Sydney: Leura](https://dictionaryofsydney.org/index.php/entry/leura) and [Lawson](https://dictionaryofsydney.org/entry/lawson). Each town's source is also in its CSV row.

This is an offline educational guide. It does not check current closures, weather, fire conditions, personal fitness or accessibility requirements. Consult the relevant track pages, [Blue Mountains City Council](https://www.bmcc.nsw.gov.au/) notices and [NPWS alerts](https://www.nationalparks.nsw.gov.au/alerts/alerts-list) before walking. A grade alone does not establish wheelchair or pram access. Grand Canyon has specific heavy-rain advice on its official page.

## Editing the data

Open the CSV files in a text editor or spreadsheet editor and retain the exact header order. Quote any cell containing a comma. Use unique, non-empty IDs and ensure each trail's `location_id` exists in `locations.csv`.

- `distance_km`: a positive finite number.
- `minutes`: a positive whole number.
- `grade`: a whole number from 1 to 5.
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

The 29 tests include exact filter boundaries, deterministic ties, route preference ranking, the South Lawson profile, town filtering, numbered menu choices, matching and non-matching preferences, no results, transport restrictions, invalid numeric input (including infinity and NaN), corrupt CSV records, missing files, report append/read-back, save failures, clean exits and a complete menu session launched from a different directory. Test files and saved reports use temporary folders; the bundled catalogue is not modified.

## COMP9001 concepts and review guide

The implementation uses functions, loops, conditionals, strings, lists, dictionaries, sets, sorting and exceptions. File I/O and program testing are the two planned advanced topics. There is no database, web application, external API or machine learning dependency. The interface uses standard-library `textwrap` and plain separators; no colour or terminal packages are required. Menus accept numbers or the displayed option keywords. Three mood tags keep the model easy to explain. Crowd predictions and extra questionnaire factors are intentionally omitted to keep the demo concise.

Suggested reading order:

1. Follow `main()` in `main.py` through one menu session.
2. Read `load_catalogue()` and compare a raw CSV row with the converted dictionary.
3. Trace `exclusion_reasons()`, `score_trail()` and `recommend()` using the example above.
4. Change one preference and predict which walks disappear or change score.
5. Read `preparation()` and `save_report()`; save two sessions and inspect the output.
6. Run `tests.py`, then add a test when changing a scoring rule or adding a walk.
