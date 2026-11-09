# Obesity Trends in US Children and Adolescents

Analysis of CDC/NCHS obesity prevalence across ten NHANES survey cycles
(1988-1994 through 2015-2018), broken down by sex, age band, race and Hispanic
origin, and percent of poverty level.


## Headline finding

Obesity prevalence among 2-19 year-olds rose **+3.0 percentage points per
decade**, from 10.0% in 1988-1994 to 18.9% in 2015-2018. 
Every subgroup fitted on 5 or more cycles shows a rising trend except the
highest income bracket (400%+ of the poverty level), whose slope is essentially
flat (**-0.4 pp/decade**). The Asian-only groups (2-3 cycles) come out between
0.0 and +3.0 pp/decade, too thinly supported to call.

Among groups fitted on the full 10 cycles, the steepest increases are in the
Hispanic or Latino: Mexican subgroup (+4.1 pp/decade, +4.3 for females
specifically), the 100-199% poverty bracket (+4.3 pp/decade), and adolescents
aged 12-19 (+4.0 pp/decade).

The broader "Hispanic or Latino: All races" group and its sex-split versions
look steeper still for the overall group and females (+5.5 and +6.75
pp/decade) but not for males (+4.4). All three are fit on only 5 cycles — so it shouldn't be read with the same confidence as the Mexican-origin subgroup, which has the full 10 cycles.

Each slope is a plain (unweighted) least-squares fit against the survey
window midpoint — a descriptive summary of direction and rough size, not a
statistically tested estimate. Groups fit on very few cycles should be read as even less certain than that.

## The caveat that matters

The linear fit is visibly mis-specified: prevalence rose steeply from 1991 to
about 2002 and has been much flatter since, so a single straight line
under-predicts the middle cycles and over-predicts the recent ones.


## The tidy frame

`load.tidy()` reshapes the published CSV into one row per (group, age band,
survey cycle). These ten columns are what every other module reads:

| Column | Type | Meaning |
| --- | --- | --- |
| `group_kind` | str | Rows are broken into characteristics according to the CSV: `total`, `sex`, `age`, `race`, `sex_race`, `poverty`. Mapped from the source `STUB_NAME_NUM` so downstream code compares against names, not integer codes. |
| `group_label` | str | The specific group within that kind — `Male`, `Below 100%`, `Hispanic or Latino: All races`|
| `age_band` | str | Age range the estimate covers: `2-19 years`, `2-5 years`, `6-11 years`, `12-19 years`. Every breakdown except `age` is published once per band. |
| `age_num` | float | Numeric code for `age_band`: `0.0`, `0.1`, `0.2`, `0.3` respectively. **`age_num == 0` selects the full 2-19 band**, which is what makes groups comparable — `series_for` filters on it. |
| `year_window` | str | The survey window as published, e.g. `2001-2004`. Ten windows, several overlapping. |
| `year_mid` | float | Midpoint of the survey window (`2001-2004` -> `2002.5`). **Use this as the time axis, not `cycle`** -- surveys aren't evenly spaced, so only `year_mid` gives a slope in percent per year. |
| `cycle` | int | 1..10 ordinal position of the survey window. Useful for ordering; not a time axis. |
| `estimate` | float | Obesity prevalence, percent of population, crude. Range 5.2 to 33.3. Never null (suppressed cells are dropped)|
| `se` | float | NCHS standard error of `estimate`. Range 0.5 to 4.5. Shown as an error band on the charts; not used to weight the trend fit. |
| `flag` | str | NCHS footnote: `*` means the estimate fails their reliability standards. |

Dropped from the source as redundant: 
- `INDICATOR` and `UNIT`/`UNIT_NUM` (constant across all rows), 
- `PANEL`/`PANEL_NUM` (duplicates of `AGE`/`AGE_NUM`)
- `STUB_*` codes (superseded by `group_kind` and `group_label`).


## Known defects in the source data

- The published CSV **omits the "Female: Not Hispanic or Latino: Black or
  African American" group entirely** — the male counterpart is present. Any
  sex-by-race conclusion has this hole in it.
- Groups with fewer than 2 usable cycles are refused rather than fitted, since
  a line needs at least two points. The Asian-only breakdowns (2-3 cycles) are
  fitted but should be read as illustrative, not reliable.


## Data source

CDC/NCHS, National Health and Nutrition Examination Survey
Estimates are crude percent of population.
Rows the NCHS flagged `*` (fails
reliability standards) are excluded by default.
