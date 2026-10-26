# COMP9001 - Blue Mountains Handbook

#### GitHub Repository Link: https://github.com/yuhan0113/comp9001-blue-mountains-handbook.git

#### Student Name: Yu-Han CHANG

#### Student ID: 540 140 295

#### Tutorial Activity 01 (Niousha Nazemi)

## Run the program

From this project folder:

```sh
python3 main.py
```

The program provides an interactive guide to selected Blue Mountains locations and bushwalking tracks. Users can explore local information, browse available walks and receive personalised walk recommendations based on their preferences.

No third-party Python packages are required.

## Which files do what?

- `main.py`: entry point; displays the main menu and coordinates the program.
- `trails.csv`: stores bushwalking trail information used by the program.
- `locations.csv`: stores information about selected Blue Mountains towns and locations.
- `tests.py`: contains developer tests for recommendation and scoring functions.
- `README.md`: explains how to run and understand the project.

Additional Python modules may be added as the program is developed.

## Main Features

The program allows users to:

- Explore selected Blue Mountains towns and locations.
- View information such as postcode, local history and nearby walks.
- Browse available bushwalking tracks.
- Enter personal preferences such as available time, distance, difficulty and scenery.
- Consider transport and preparation requirements.
- Receive personalised bushwalking recommendations.
- View suggested gear and preparation for recommended walks.

## Advanced Topics

The project is designed to demonstrate advanced COMP9001 topics including:

- File I/O for loading trail and location data.
- Program testing for recommendation and scoring functions.

Other advanced concepts may also be used where appropriate during development.

## Run the checks

From this project folder:

```sh
python3 tests.py
```

Tests display their results in the terminal.

The tests will focus on areas such as recommendation scoring, preference handling, invalid inputs and expected program behaviour.

## Suggested reading order

1. Start with `main()` in `main.py` to understand the overall program flow and menu.
2. Follow the location and trail loading functions to see how external data is read.
3. Read the recommendation and scoring functions to understand how user preferences affect trail rankings.
4. Review the gear recommendation logic to see how preparation suggestions are generated.
5. Run `tests.py` to check important program behaviours.

## Project Scope

Blue Mountains Handbook is a personalised bushwalking and local guide focused on selected locations within the Blue Mountains.

The program does not provide real-time weather, track closure, emergency or safety information. Recommendations are based on stored trail characteristics and user preferences rather than live environmental conditions.

Users should check official and current information before undertaking any bushwalk.

The code may be prepared with AI assistance where permitted. All submitted work should be understood and reviewed by the student in accordance with COMP9001 AI-use and disclosure requirements.
