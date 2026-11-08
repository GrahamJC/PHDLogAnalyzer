# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Parser/analyser for PHD2 (astrophotography autoguiding software) guide logs. `test.log` is a real sample PHD2 log (v2.6.14, log version 2.5) used as the working input.

## Environment & commands

- Python 3.13 virtual environment in `.venv` (dependencies managed with `uv`; `uv sync` to install). `python` is not on PATH on this machine — invoke the venv interpreter directly rather than `uv run`: `.venv/Scripts/python.exe` (Windows layout).
- Launch the GUI: `.venv/Scripts/python.exe main.py [logfile]` (File > Open / Ctrl+O to browse for a log).
- GUI is in [gui.py](gui.py) (tkinter + embedded matplotlib). It wraps `PHDLogFile` and captures the parser's "Unmatched line" stdout to show a count in the status bar.
- Exploratory analysis lives in `notebook.ipynb` (pandas/numpy, kernel via `ipykernel`): it loads `test.log` and builds DataFrames from section steps via `dataclasses.asdict`.
- No test suite, linter, or formatter is configured.

## Architecture

Everything is in [phdlogfile.py](phdlogfile.py). `PHDLogFile(path)` parses the whole file eagerly in `__post_init__` using a line-by-line state machine:

```
VERSION -> SECTION -> CALIBRATE -> CALIBRATE_STEPS -> SECTION
                   \-> GUIDE     -> GUIDE_STEPS     -> SECTION
```

- `SECTION` waits for `Calibration Begins at` / `Guiding Begins at`; top-level `INFO:` lines go to `PHDLogFile.infos`.
- `CALIBRATE` / `GUIDE` parse header key/value lines into fields of `CalibrateSection` / `GuideSection`; the CSV header line switches to the `*_STEPS` state.
- `*_STEPS` parse CSV rows into `CalibrateStep` / `GuideStep`, plus `INFO:` lines (into `section.infos`) and calibration results. A section is appended to `PHDLogFile.sections` only on `Calibration complete` / `Guiding Ends at`.
- Each state is a chain of compiled regexes tried in order; a match `continue`s. Any line that matches nothing in the current state falls through to a `print("Unmatched line ...")` — this output is the main signal of parser coverage gaps. Known current unmatched lines: predictive-PEC algorithm parameter lines in the guide header, and the `Log Summary` / `Log closed` trailer.

Adding support for a new log line: add a field to the relevant section dataclass, a regex in `__post_init__`, and a match block in the appropriate state branch. Calibration and guide headers share many line formats but have separate (duplicated) regexes and handlers.

### Quirks to be aware of

- Empty numeric fields in guide-step CSV rows (e.g. frames with no star) are converted to `0`/`0.0`.
