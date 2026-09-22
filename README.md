# 🏈 Big Sarge Game Day Center

The complete **NFL 2026 regular season schedule** — all 18 weeks, all 272 games — plus live
standings, a playoff picture, and a full team directory. One static page, no build step,
no dependencies.

**Live site:** https://wayneaince-sys.github.io/big-sarge-game-day-center/

## What's on the page

- **Full schedule.** Every game from the Wednesday, September 9, 2026 opener in Seattle
  through Week 18 on January 10, 2027. Pick any week from the tab strip; games are grouped
  by day with kickoff times in Eastern.
- **Scores and records.** Completed games show the final with the winner highlighted.
  Team records are computed from actual results, so the directory and the playoff picture
  update themselves as scores land.
- **Game flags.** Thursday Night, Monday Night, Saturday, International (with the host city),
  and division matchups are all labelled.
- **Bye weeks.** Listed under each week's games. Byes run Week 5 through Week 14.
- **Playoff picture.** Four division leaders plus three wild cards per conference, seeded from
  real results.
- **Team directory.** All 32 teams by conference and division, each linking to its NFL.com page.
- **Deep links.** `#week-7` opens straight to that week. Arrow keys move between weeks.

## Accuracy notes

- **Week 18 times show as TBD.** The matchups are final — all 16 are division games — but the
  NFL only assigns days and kickoff times after Week 17. A Saturday, January 9 split is expected.
- **Kickoff times flex from Week 5 on.** Sunday windows can move; the page shows the currently
  scheduled slot.
- **The playoff picture is a straight win-percentage sort**, broken by division record and then
  point differential. The NFL's full head-to-head and common-games tiebreakers are *not* applied,
  so close seeds are approximate. Entertainment only.

## Updating the schedule

`index.html` is generated. To pull the latest scores and re-render:

```bash
curl -o games.csv https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv
python3 tools/build_schedule.py games.csv index.html
```

Requires Python 3 only — no packages to install. Commit the regenerated `index.html`
and GitHub Pages picks it up.

## Data source

Schedule and results come from [nflverse/nfldata](https://github.com/nflverse/nfldata),
which tracks the official NFL schedule. Week counts, the Week 18 all-division slate, and the
Week 5–14 bye window all match the NFL's own 2026 schedule release.

## Tech

Plain HTML, CSS and vanilla JavaScript in a single file. Responsive down to phone width,
keyboard navigable, and it prints cleanly. Nothing to install, nothing to compile.

---

Team names and logos are property of the National Football League.
