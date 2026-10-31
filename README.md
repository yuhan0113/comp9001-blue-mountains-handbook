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

The questions start with mood and scenery, followed by time, difficulty and transport. Difficulty choices map to maximum grades: Easy = 2, Moderate = 3, Challenging = 5. Distance and route style are optional; selecting `no` leaves distance unrestricted and route style as no preference. Mood affects ranking, not your difficulty limit. Packing advice appears with the results instead of an extra gear question.

The CSV files are found relative to `main.py`, so running the script from another working directory also works.

## Which files do what?

- `main.py`: menu, input validation, readable output, preparation questions and report saving.
- `data_loader.py`: reads CSV files, converts numbers and booleans, validates data and location references.
- `recommendations.py`: hard-limit filtering, preference scoring, sorting and preparation suggestions.
- `trails.csv`: eighteen walks with distance, duration, grade, route type, tags, access notes and source URLs.
- `locations.csv`: fourteen towns with postcodes, descriptions, history notes and source URLs.
- `tests.py`: standard-library `unittest` checks covering logic, file handling and terminal interactions.
- `saved_recommendations.txt`: created only when you choose to save; subsequent sessions append instead of overwriting. This personal output is ignored by Git.

## How recommendations work

First, exclude any walk exceeding the user's maximum walking time, optional distance or track grade. If the user chooses public transport, also exclude records without public transport support in this small catalogue. Limits are inclusive: a 60-minute walk fits a 60-minute limit. The program never relaxes a limit silently.

Then score each eligible walk:

- 40 points for meeting all four hard limits.
- 30 points if the scenery matches, or the user selected `any`.
- 20 points if the mood matches, or the user selected `any`.
- 10 points if the route style matches, or the user selected `any`.

Sort by descending score, then ascending duration, then alphabetical name. Display the first three. The score is a transparent preference heuristic, not a probability, safety rating or claim that a track is currently open. All eligible walks get at least 40 points. Unmatched scenery, mood and route preferences are shown as trade-offs; they never exclude a walk. Selecting `any` gives equal points to every walk for that factor.

If there are no matches, look for walks blocked only by time. Show the shortest required time and ask before changing it; distance, grade and transport limits stay unchanged. Declining keeps the original limits. The user can retry the questionnaire or return to the menu. No long list of rejected walks is printed.

The screen shows brief walk suggestions, matching preferences, trade-offs and access notes. Packing advice appears once, with route-specific preparation where needed. Full scoring explanations and source notes remain in saved reports and walk details. With no soft preferences, the screen explains that results are ordered by time and name rather than advertising a perfect match score.

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

Transport is deliberately simplified. Transport-enabled routes include Three Sisters, South Lawson, Gordon Falls to Katoomba, the night-lit walk, Florabella Pass, the Victory/Sassafras route, Woodford Creek and Horseshoe Falls (browse-only because of its unverified numeric grade). Access notes describe extra station or bus-stop transfers; those are not included in the hard walking limits. A `no` value means access is **not modelled in this catalogue**, not that public transport is impossible. No timetable, transfer distance or fare is calculated. Car selection also requires the user to arrange suitable trailhead access and any pickup. Check [Transport for NSW Trip Planner](https://transportnsw.info/trip) for actual journeys.

Short history summaries are paraphrased from [Blue Mountains Local Studies](https://bluemlocalstudies.wordpress.com/2016/04/26/katoomba-street-history-walk/), [Powerhouse Collection](https://collection.powerhouse.com.au/object/31124), and the [Wentworth Falls Chamber of Commerce](https://www.wentworthfalls.org.au/history-of-wentworth-falls/). Leura and Lawson history notes come from the [Dictionary of Sydney: Leura](https://dictionaryofsydney.org/index.php/entry/leura) and [Lawson](https://dictionaryofsydney.org/entry/lawson). Each town's source is also in its CSV row.

This is an offline educational guide. It does not check current closures, weather, fire conditions, personal fitness or accessibility requirements. Consult the relevant track pages, [Blue Mountains City Council](https://www.bmcc.nsw.gov.au/) notices and [NPWS alerts](https://www.nationalparks.nsw.gov.au/alerts/alerts-list) before walking. A grade alone does not establish wheelchair or pram access. Grand Canyon has specific heavy-rain advice on its official page.

## Editing the data

Open the CSV files in a text editor or spreadsheet editor and retain the exact header order. Quote any cell containing a comma. Use unique, non-empty IDs and ensure each trail's `location_id` exists in `locations.csv`.

- `distance_km`: a positive finite number.
- `minutes`: a positive whole number.
- `grade`: a whole number from 1 to 5, or `unknown` when a comparable numeric grade is not published. Unknown grades are excluded from recommendations, not guessed.
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

- [Katoomba Falls Night-lit Walk](https://www.visitbluemountains.com.au/plan/bushwalks): 1.5 km, up to 60 minutes return, grade 1 in the regional tourism guide. The [NSW Government listing](https://www.nsw.gov.au/visiting-and-exploring-nsw/locations-and-attractions/katoomba-falls-night-lit-walk) instead states 1.3 km. The longer tourism planning figure is used and the discrepancy is shown in the walk details. Paths include steps; no lighting timetable or accessibility guarantee is made. Check council notices and carry a torch.
- [Jellybean track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/jellybean-track): NPWS 1 km return, 30–60 minutes, grade 3.
- [Blaxland to Warrimoo via Florabella Pass](https://www.wildwalks.com/bushwalking-and-hiking-in-nsw/glenbrook-eastern-blue-mountains/blaxland-to-warrimoo-station-florabella-pass): Wildwalks 6 km one-way, 180 minutes, grade 4, 406 m total climbing. These figures include the publisher's described detour, not every possible Florabella variant.
- [Faulconbridge to Springwood via Sassafras Gully](https://www.wildwalks.com/bushwalking-and-hiking-in-nsw/blue-mountains-springwood/faulconbridge-to-springwood-via-sassafras-gully): Wildwalks 6.1 km one-way, 180 minutes, grade 4, 338 m total climbing.
- [Woodford Creek walk](https://walkingvolunteers.org.au/walks/woodford-creek-walk/): Walking Volunteers 7.1 km one-way, 180 minutes excluding breaks, grade 3. It starts at Hazelbrook station and ends at Woodford station. It is not the Woodford–Oaks cycling trail.
- [Birdwood Gully](https://www.bushtrackers.com.au/guides-maps/35-birdwood-gully-walk): Bush Trackers 2.6 km, 90 minutes, qualitative Medium grade. This is a loop; no unsupported numeric grade is assigned.
- [Horseshoe Falls](https://www.bushtrackers.com.au/guides-maps/13-horseshoe-falls-walk): Bush Trackers 1 km, 60 minutes, qualitative Medium grade. The [route map](https://www.bushtrackers.com.au/images/pdf-guides/Horseshoe-Falls.pdf) describes the loop and station approach. Longer Burgess Falls routes are different walks.

Birdwood Gully and Horseshoe Falls are available in Browse Walks but are excluded from scored recommendations until a numeric grade is verified. The numeric filter otherwise retains each source's published grade; specialist Wildwalks grades are labelled as such in route notes rather than presented as official NPWS grades.

### Elevation gain and data quality

Elevation gain means cumulative ascent in metres, not altitude or net height change. Eight walks now have approximate ascent figures. Third-party GPS/route estimates are accepted; differences in start points, side trips and GPS processing are disclosed in `data_note`. The screen says “about” and the browse list labels gain as approximate. Missing estimates remain `--`; zero is never substituted for missing data. Elevation is informational and does not change scores.

- Porters Pass 473 m, Florabella Pass 406 m and Victory/Sassafras 338 m: existing Wildwalks sources.
- Grand Canyon about 443 m: [Trail Hiking Australia](https://www.trailhiking.com.au/hikes/grand-canyon-track/) gives 443 m, with 6.5 km in its listing and 6.119 km GPS distance. [Coast and Crest](https://www.coastandcrest.com.au/guide-grand-canyon-track) instead reports 294 m over 6.16 km. This is a source estimate, not agreement between sources; the NPWS 6.3 km planning distance remains.
- South Lawson about 112 m: [We Are Explorers](https://weareexplorers.co/sydney-waterfall-way/) describes a 3.1 km four-waterfall circuit. The tourism distance of 3.5 km remains. The owner's pasted Strava record (2.90 km, 118 m) is a broadly similar comparison, not proof of an identical route.
- Lockley Pylon about 325 m: [Trail Hiking Australia](https://www.trailhiking.com.au/hikes/lockleys-pylon-walking-track/), 7 km return.
- Jellybean about 80 m: [Itineraries Redefined](https://www.itinerariesredefined.com/jellybean-pool-glenbrook.html/), 1 km return from Glenbrook Office; not the 260 m pool-car-park walk.
- Birdwood Gully about 68 m: [Itineraries Redefined](https://www.itinerariesredefined.com/magical-glow-worms-in-birdwood-gully-springwood.html/) loop fact list, 2.6 km; not the short glow-worm visit in its prose.

The owner's other pasted Strava records (Grand Canyon 7.30 km / 695 m; Centennial Glen–Porters Pass 4.86 km / 426 m; Wentworth Falls 4.61 km / 229 m and 3 km / 204 m) have different distances from the catalogue routes. They were considered as comparisons, not copied as exact-route figures. No private Strava account or GPS track was accessed. Several third-party pages display zero for all elevation fields; these were treated as missing. Council's night-lit page still returned an access error, and no suitable ascent figure was established for that route.

The Grand Canyon [adventure-sports page](https://www.nationalparks.nsw.gov.au/things-to-do/adventure-sports-experiences/grand-canyon) describes technical canyoning involving swimming and a 20 m abseil. The catalogue uses the separate [Grand Canyon walking track](https://www.nationalparks.nsw.gov.au/things-to-do/walking-tracks/grand-canyon-track), not that activity.

Source checks establish the published route description, not that a route is open today. Original route sources were checked on 27/31 October as described above; these additions were checked on 31 October. Council's night-walk page could not be fetched during this check, so the government listing and regional tourism guide were used with their disagreement disclosed.

### Town stops

Katoomba includes [Yellow Deli](https://www.yellowdeli.com/katoomba), 214 Katoomba Street, using the business's own location page. No fixed opening hours are stored. Other highlights include [Everglades](https://www.nationaltrust.org.au/places/everglades-house-gardens/), [Norman Lindsay Gallery](https://www.nationaltrust.org.au/places/norman-lindsay-gallery/), [Woodford Academy](https://www.nationaltrust.org.au/places/woodford-academy/), [Valley Heights museum](https://mgnsw.org.au/organisations/valley-heights-locomotive-depot-heritage-museum/) and [Linden Observatory](https://www.lindenobservatory.org.au/). The observatory is appointment/event-only. Town pages include reference links; supply notes are planning suggestions, not live shop inventories. Check business hours and any booking requirements directly.
