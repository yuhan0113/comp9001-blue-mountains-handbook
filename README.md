# USYD COMP9001 Final Project - Blue Mountains Handbook
## Personalised Bushwalking & Local Guide

**Student:** Yu-Han Chang  
**Student ID:** 540140295  
**Tutorial:** Activity 01 - Niousha Nazemi  
**Github Repository (Private):** https://github.com/yuhan0113/comp9001-blue-mountains-handbook

## Overview

Blue Mountains Handbook is a terminal-based Python program that helps users explore the Blue Mountains and find bushwalks that suit their preferences.

The program contains 18 walks and 14 towns or areas. Users can receive personalised walk recommendations, browse the walking catalogue, explore local town information and save recommendation reports.

The recommendation system considers available walking time, difficulty, scenery, mood and optional distance or route preferences.

## Requirements

- Python 3.9 or later
- The following project data files:
  - `trails.csv`
  - `locations.csv`

Place all project files in the same folder before running the program.

No third-party Python packages, installation or internet connection are required.

## Running the Program

Open a terminal in the project folder, then run:

```sh
python3 main.py
```

The main menu provides four options:

1. Find a Walk for Me
2. Browse Walks
3. Explore Local Towns in the Blue Mountains
4. Exit

For personalised recommendations, the program asks for:

- current mood
- available walking time
- preferred scenery
- comfortable difficulty

Users may optionally set:

- maximum walking distance
- preferred route style

Invalid input produces a message and another prompt. Missing or malformed catalogue files produce a startup error instead of continuing with incomplete data.

## Submission Files

- `main.py` — main menu, user interaction, walk and town display, and report saving.
- `data_loader.py` — reads and validates the CSV catalogue.
- `recommendations.py` — filters, scores and ranks suitable walks.
- `trails.csv` — data for the 18 walking routes.
- `locations.csv` — data for the 14 towns and areas.
- `tests.py` — automated tests for recommendation logic, file handling and terminal interaction.
- `README.md` — project overview and instructions.

`saved_recommendations.txt` is created only when the user chooses to save a recommendation report and is not required for the initial program run.

## Recommendation Logic

Walks are first filtered using three hard limits:

```text
Walking Time
Optional Maximum Distance
Difficulty
```

Difficulty uses three project-defined categories:

```text
Easy < Moderate < Hard
```

An Easy selection includes Easy walks only. Moderate includes Easy and Moderate walks, while Hard allows all three categories.

Eligible walks are then scored using:

```text
Score = Eligibility + Scenery Match + Mood Match + Route Match
```

The components are:

```text
Eligibility     = 40 points
Scenery Match  = 30 points
Mood Match     = 20 points
Route Match    = 10 points
```

No preference awards the same points to every eligible walk for that factor. Unmatched scenery, mood or route preferences are explained as trade-offs, not exclusions. Results are sorted by descending score, ascending walking time and alphabetical name. Up to three recommendations are displayed.

When no walks fit, the program can offer a longer time while preserving the other limits. It asks before changing the time; users can retry or return to the menu. Saved reports append to earlier sessions.

The score measures preference fit only. It is not a safety rating or confirmation that a track is currently open.

## Walk and Town Information

Each walk may include:

- distance
- estimated walking time
- Easy, Moderate or Hard difficulty
- route type
- scenery and mood tags
- access information
- description
- elevation gain where a suitable source is available
- source and route notes

Elevation is displayed for planning information only and does not affect recommendations. Missing elevation values are shown as `--`.

Town entries may include:

- postcode
- short history
- things to do
- visitor information
- food and supply suggestions
- local walks
- nearby or connecting walks

Transport information is retained as access information but is not used as a recommendation filter.

## Safety and Limitations

Blue Mountains Handbook is an offline educational guide and does not provide live information about track closures, weather, fire conditions, flooding, accessibility or transport services.

Before walking, users should check current information from:

- NSW National Parks and Wildlife Service alerts  
  https://www.nationalparks.nsw.gov.au/alerts/alerts-list
- Blue Mountains City Council  
  https://www.bmcc.nsw.gov.au/

Walking times are planning estimates and do not include travel, breaks or unexpected delays.

The Easy, Moderate and Hard categories are project-defined comparison categories rather than official track grades.

## Verification

Run the automated tests with:

```sh
python3 tests.py
```

or:

```sh
python3 -m unittest discover -v
```

The current version passes 47 automated tests.

The project demonstrates file I/O through CSV loading and report writing, and program testing through standard-library `unittest`. Tests cover ranking, validation, file errors and terminal interactions.
