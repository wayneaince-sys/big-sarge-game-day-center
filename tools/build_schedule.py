#!/usr/bin/env python3
"""Generate index.html for Big Sarge Game Day Center from nflverse games.csv."""
import csv, json, datetime, html, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
SEASON = "2026"

TEAMS = {
 'BUF':('Buffalo Bills','AFC','East','buffalo-bills'),
 'MIA':('Miami Dolphins','AFC','East','miami-dolphins'),
 'NE':('New England Patriots','AFC','East','new-england-patriots'),
 'NYJ':('New York Jets','AFC','East','new-york-jets'),
 'BAL':('Baltimore Ravens','AFC','North','baltimore-ravens'),
 'CIN':('Cincinnati Bengals','AFC','North','cincinnati-bengals'),
 'CLE':('Cleveland Browns','AFC','North','cleveland-browns'),
 'PIT':('Pittsburgh Steelers','AFC','North','pittsburgh-steelers'),
 'HOU':('Houston Texans','AFC','South','houston-texans'),
 'IND':('Indianapolis Colts','AFC','South','indianapolis-colts'),
 'JAX':('Jacksonville Jaguars','AFC','South','jacksonville-jaguars'),
 'TEN':('Tennessee Titans','AFC','South','tennessee-titans'),
 'DEN':('Denver Broncos','AFC','West','denver-broncos'),
 'KC':('Kansas City Chiefs','AFC','West','kansas-city-chiefs'),
 'LV':('Las Vegas Raiders','AFC','West','las-vegas-raiders'),
 'LAC':('Los Angeles Chargers','AFC','West','los-angeles-chargers'),
 'DAL':('Dallas Cowboys','NFC','East','dallas-cowboys'),
 'NYG':('New York Giants','NFC','East','new-york-giants'),
 'PHI':('Philadelphia Eagles','NFC','East','philadelphia-eagles'),
 'WAS':('Washington Commanders','NFC','East','washington-commanders'),
 'CHI':('Chicago Bears','NFC','North','chicago-bears'),
 'DET':('Detroit Lions','NFC','North','detroit-lions'),
 'GB':('Green Bay Packers','NFC','North','green-bay-packers'),
 'MIN':('Minnesota Vikings','NFC','North','minnesota-vikings'),
 'ATL':('Atlanta Falcons','NFC','South','atlanta-falcons'),
 'CAR':('Carolina Panthers','NFC','South','carolina-panthers'),
 'NO':('New Orleans Saints','NFC','South','new-orleans-saints'),
 'TB':('Tampa Bay Buccaneers','NFC','South','tampa-bay-buccaneers'),
 'ARI':('Arizona Cardinals','NFC','West','arizona-cardinals'),
 'LAR':('Los Angeles Rams','NFC','West','los-angeles-rams'),
 'SF':('San Francisco 49ers','NFC','West','san-francisco-49ers'),
 'SEA':('Seattle Seahawks','NFC','West','seattle-seahawks'),
}
ALIAS = {'LA':'LAR'}

VENUE_CITY = {
 'Melbourne Cricket Ground':'Melbourne, Australia',
 'Maracana Stadium':'Rio de Janeiro, Brazil',
 'Tottenham Hotspur Stadium':'London, England',
 'Wembley Stadium':'London, England',
 'Stade de France':'Paris, France',
 'Bernabeu':'Madrid, Spain',
 'FC Bayern Munich Stadium':'Munich, Germany',
 'Estadio Banorte':'Mexico City, Mexico',
}

def fmt_time(t):
    if not t: return 'TBD'
    h, m = int(t[:2]), t[3:5]
    ap = 'AM' if h < 12 else 'PM'
    h12 = h % 12 or 12
    return f'{h12}:{m} {ap} ET'

games, weeks = [], {}
for r in csv.DictReader(SRC.open()):
    if r['season'] != SEASON or r['game_type'] != 'REG':
        continue
    away = ALIAS.get(r['away_team'], r['away_team'])
    home = ALIAS.get(r['home_team'], r['home_team'])
    wk = int(r['week'])
    d = datetime.date.fromisoformat(r['gameday'])
    intl = r['location'] != 'Home'
    g = {
        'wk': wk, 'date': r['gameday'], 'day': r['weekday'],
        'time': fmt_time(r['gametime']),
        'away': away, 'home': home,
        'venue': r['stadium'], 'div': r['div_game'] == '1',
    }
    if r['away_score'] and r['home_score']:
        g['as'] = int(r['away_score']); g['hs'] = int(r['home_score'])
    if intl:
        g['intl'] = VENUE_CITY.get(r['stadium'], r['stadium'])
    elif r['weekday'] == 'Thursday':
        g['kind'] = 'tnf'
    elif r['weekday'] == 'Monday':
        g['kind'] = 'mnf'
    elif r['weekday'] == 'Saturday':
        g['kind'] = 'sat'
    if intl:
        g['kind'] = 'intl'
    # The NFL sets Week 18 days and kickoff times only after Week 17, so the
    # feed carries a Sunday 1:00 placeholder for all 16. Don't show it as fact.
    if wk == 18 and not ('as' in g):
        g['time'] = 'TBD'
        g['tbd'] = True
    games.append(g)
    weeks.setdefault(wk, []).append(g)

games.sort(key=lambda g: (g['wk'], g['date'], g['time']))

# byes
byes = {}
for wk in sorted(weeks):
    playing = {t for g in weeks[wk] for t in (g['home'], g['away'])}
    off = sorted(set(TEAMS) - playing, key=lambda t: TEAMS[t][0])
    if off:
        byes[wk] = off

# week date ranges
ranges = {}
for wk in sorted(weeks):
    ds = sorted({g['date'] for g in weeks[wk]})
    a = datetime.date.fromisoformat(ds[0]); b = datetime.date.fromisoformat(ds[-1])
    ranges[wk] = (f'{a:%b} {a.day}' if a == b else
                  (f'{a:%b} {a.day}–{b.day}' if a.month == b.month
                   else f'{a:%b} {a.day} – {b:%b} {b.day}'))

played = [g for g in games if 'hs' in g]
last_wk = max((g['wk'] for g in played), default=0)
current_wk = min(last_wk + 1, 18) if last_wk else 1
if last_wk and len([g for g in played if g['wk'] == last_wk]) < len(weeks[last_wk]):
    current_wk = last_wk

notes = {
    18: ('Week 18 matchups are final \u2014 all 16 are division games \u2014 but the NFL '
         'assigns days and kickoff times only after Week 17, so times show as TBD. '
         'Expect a Saturday, January 9 split once they are announced.'),
}

data = {
    'season': SEASON, 'games': games, 'notes': notes,
    'teams': {k: {'n': v[0], 'c': v[1], 'd': v[2], 'u': f'https://www.nfl.com/teams/{v[3]}/'}
              for k, v in TEAMS.items()},
    'byes': byes, 'ranges': ranges,
    'currentWeek': current_wk, 'played': len(played),
}

order = ['East', 'North', 'South', 'West']
def dir_html(conf):
    out = []
    for div in order:
        ts = sorted((k for k, v in TEAMS.items() if v[1] == conf and v[2] == div),
                    key=lambda k: TEAMS[k][0])
        cards = '\n'.join(
            f'''                        <a href="{TEAMS[t][3] and f'https://www.nfl.com/teams/{TEAMS[t][3]}/'}" target="_blank" rel="noopener noreferrer" class="team-link" data-team="{t}">
                            <span class="team-logo">{t}</span>
                            <span class="team-name">{html.escape(TEAMS[t][0])}</span>
                            <span class="team-record" data-record="{t}"></span>
                        </a>''' for t in ts)
        out.append(f'''                <div class="division">
                    <h3 class="division-title">{conf} {div}</h3>
                    <div class="teams-grid">
{cards}
                    </div>
                </div>''')
    return '\n\n'.join(out)

today = datetime.date.today().strftime('%B %-d, %Y')

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Big Sarge Game Day Center - the complete NFL 2026 schedule, all 18 weeks and 272 games, plus live standings and playoff picture.">
<meta name="keywords" content="NFL, NFL 2026 schedule, football schedule, NFL standings, playoff picture, Big Sarge, Game Day Center">
<meta name="author" content="Big Sarge Game Day Center">

<meta property="og:title" content="Big Sarge Game Day Center - NFL 2026 Schedule">
<meta property="og:description" content="Every NFL 2026 game, week by week: kickoff times, scores, standings and the playoff picture.">
<meta property="og:type" content="website">

<title>Big Sarge Game Day Center - NFL 2026 Schedule</title>

<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
    line-height: 1.6;
    color: #1f2430;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
}}

.header {{
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 40px;
    text-align: center;
}}
.header h1 {{ font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
.header p {{ font-size: 1.1rem; opacity: 0.95; }}

.nav {{
    background: #2a5298;
    padding: 15px 40px;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 20;
}}
.nav a {{
    color: white; text-decoration: none; margin: 0 15px;
    font-weight: 500; transition: opacity 0.3s;
    display: inline-block;
}}
.nav a:hover {{ opacity: 0.8; }}
.nav a:focus-visible {{ outline: 2px solid #ffd166; outline-offset: 3px; border-radius: 3px; }}

.content {{ padding: 40px; }}

/* Season status strip */
.season-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 40px;
}}
.stat {{
    background: #f4f6fb;
    border: 1px solid #e1e6f0;
    border-left: 4px solid #2a5298;
    border-radius: 10px;
    padding: 15px 18px;
}}
.stat .label {{
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: #5a6478; font-weight: 600;
}}
.stat .value {{ font-size: 1.5rem; font-weight: 700; color: #1e3c72; line-height: 1.2; }}
.stat .sub {{ font-size: 0.85rem; color: #5a6478; }}

/* Section headings */
.section {{ margin-bottom: 50px; scroll-margin-top: 70px; }}
.section-title {{
    font-size: 1.8rem; color: #1e3c72; margin-bottom: 8px;
    padding-bottom: 10px; border-bottom: 3px solid #e0e0e0;
}}
.section-note {{ color: #5a6478; font-size: 0.92rem; margin-bottom: 25px; }}

/* Week selector */
.week-tabs {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;
}}
.week-tab {{
    font: inherit; font-weight: 600; font-size: 0.9rem;
    padding: 8px 14px; border-radius: 8px; cursor: pointer;
    background: #eef1f8; color: #2a5298;
    border: 1px solid #d8dfee;
    transition: background 0.2s, color 0.2s, transform 0.1s;
}}
.week-tab:hover {{ background: #dde4f5; }}
.week-tab:focus-visible {{ outline: 2px solid #1e3c72; outline-offset: 2px; }}
.week-tab[aria-selected="true"] {{
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white; border-color: #1e3c72;
}}
.week-tab .dot {{
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
    background: #2ecc71; margin-left: 6px; vertical-align: middle;
}}
.week-tab[aria-selected="true"] .dot {{ background: #ffd166; }}

.week-head {{
    display: flex; flex-wrap: wrap; align-items: baseline;
    gap: 12px; margin: 25px 0 15px;
}}
.week-head h3 {{ font-size: 1.35rem; color: #1e3c72; }}
.week-head .dates {{ color: #5a6478; font-size: 0.95rem; }}

/* Game day groups */
.day-group {{ margin-bottom: 22px; }}
.day-label {{
    font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: #5a6478;
    padding-bottom: 6px; margin-bottom: 10px;
    border-bottom: 1px solid #e8ecf5;
}}
.game-list {{ display: grid; gap: 8px; }}

.game {{
    display: grid;
    grid-template-columns: 110px 1fr auto;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    background: #f9fafd;
    border: 1px solid #e8ecf5;
    border-radius: 10px;
    transition: background 0.2s, border-color 0.2s;
}}
.game:hover {{ background: #f2f5fc; border-color: #c9d4ea; }}
.game.final {{ background: #fbfbfc; }}

.game-time {{ font-size: 0.85rem; color: #5a6478; font-weight: 600; }}
.game-time .final-tag {{ color: #1e3c72; }}

.matchup {{ display: flex; flex-direction: column; gap: 2px; }}
.side {{ display: flex; align-items: center; gap: 8px; }}
.side .abbr {{
    display: inline-block; min-width: 42px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
    color: white; background: #2a5298;
    padding: 2px 6px; border-radius: 4px; text-align: center;
}}
.side .full {{ font-size: 0.95rem; }}
.side .score {{
    margin-left: auto; font-size: 1.05rem; font-weight: 700;
    color: #8a93a8; font-variant-numeric: tabular-nums;
}}
.side.win .full {{ font-weight: 700; color: #14532d; }}
.side.win .score {{ color: #14532d; }}
.side.win .abbr {{ background: #14532d; }}

.tags {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
.tag {{
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 3px 8px; border-radius: 20px;
    white-space: nowrap;
}}
.tag.tnf {{ background: #e8e2fb; color: #4c2f9c; }}
.tag.mnf {{ background: #fde6cf; color: #8a4b08; }}
.tag.sat {{ background: #d9f0ff; color: #0b4f75; }}
.tag.intl {{ background: #d7f5e3; color: #0f5132; }}
.tag.div {{ background: #f1f3f8; color: #4a5568; }}
.venue {{ font-size: 0.75rem; color: #5a6478; }}

.week-note {{
    margin-bottom: 18px; padding: 12px 16px;
    background: #fff8e6; border: 1px solid #f0dca8;
    border-left: 4px solid #d99a00;
    border-radius: 10px; font-size: 0.88rem; color: #6b4e00;
}}
.game-time.tbd {{ color: #8a93a8; font-style: italic; font-weight: 500; }}

.byes {{
    margin-top: 14px; padding: 12px 16px;
    background: #f4f6fb; border: 1px dashed #c9d4ea;
    border-radius: 10px; font-size: 0.9rem; color: #3d4757;
}}
.byes strong {{ color: #1e3c72; }}

/* Standings + playoff picture */
.two-col {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
    gap: 30px;
}}
.panel {{
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white; border-radius: 15px; padding: 25px;
}}
.panel h3 {{
    font-size: 1.15rem; margin-bottom: 15px;
    padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.25);
}}
.seed {{
    display: grid; grid-template-columns: 26px 1fr auto;
    align-items: center; gap: 10px;
    padding: 9px 0; font-size: 0.93rem;
    border-bottom: 1px solid rgba(255,255,255,0.12);
}}
.seed:last-child {{ border-bottom: none; }}
.seed-number {{ font-weight: 700; color: #ffd166; }}
.seed .rec {{ font-variant-numeric: tabular-nums; opacity: 0.9; font-size: 0.85rem; }}
.seed .role {{ display: block; font-size: 0.75rem; opacity: 0.75; }}
.seed.wc {{ opacity: 0.93; }}
.cut {{
    margin: 8px 0; border-top: 2px dashed rgba(255,209,102,0.7);
    font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: #ffd166; padding-top: 6px;
}}

/* Teams directory */
.conference {{ margin-bottom: 40px; scroll-margin-top: 70px; }}
.conference-title {{
    font-size: 1.8rem; color: #1e3c72; margin-bottom: 25px;
    padding-bottom: 10px; border-bottom: 3px solid #e0e0e0;
}}
.division {{ margin-bottom: 30px; }}
.division-title {{ font-size: 1.3rem; color: #2a5298; margin-bottom: 15px; font-weight: 600; }}
.teams-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
}}
.team-link {{
    display: flex; align-items: center; gap: 10px;
    padding: 12px 15px;
    background: #f8f9fa; border: 2px solid #e0e0e0; border-radius: 10px;
    color: #333; text-decoration: none;
    transition: all 0.3s;
}}
.team-link:hover {{
    background: #2a5298; color: white;
    border-color: #1e3c72; transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(42,82,152,0.3);
}}
.team-link:focus-visible {{ outline: 2px solid #1e3c72; outline-offset: 2px; }}
.team-logo {{
    display: inline-block; min-width: 46px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
    color: white; background: #2a5298;
    padding: 3px 6px; border-radius: 4px; text-align: center;
}}
.team-link:hover .team-logo {{ background: #14284f; }}
.team-name {{ flex: 1; font-size: 0.95rem; }}
.team-record {{ font-size: 0.85rem; font-weight: 700; color: #5a6478; font-variant-numeric: tabular-nums; }}
.team-link:hover .team-record {{ color: #e8ecf5; }}

.footer {{
    background: #1e3c72; color: white;
    padding: 25px 40px; text-align: center; font-size: 0.88rem;
}}
.footer p {{ margin: 4px 0; opacity: 0.9; }}
.footer a {{ color: #ffd166; }}

@media (max-width: 720px) {{
    body {{ padding: 10px; }}
    .header {{ padding: 28px 20px; }}
    .header h1 {{ font-size: 1.7rem; }}
    .nav {{ padding: 12px 15px; }}
    .nav a {{ margin: 0 8px; font-size: 0.9rem; }}
    .content {{ padding: 22px 15px; }}
    .footer {{ padding: 20px 15px; }}
    .game {{ grid-template-columns: 1fr; gap: 8px; }}
    .game-time {{ order: -1; }}
    .tags {{ flex-direction: row; align-items: center; flex-wrap: wrap; }}
}}

@media print {{
    body {{ background: white; padding: 0; }}
    .container {{ box-shadow: none; }}
    .nav, .week-tabs {{ display: none; }}
}}
</style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>&#127944; Big Sarge Game Day Center</h1>
        <p>The complete NFL 2026 schedule &mdash; 18 weeks, 272 games, every kickoff</p>
    </div>

    <nav class="nav">
        <a href="#schedule">Schedule</a>
        <a href="#playoffs">Playoff Picture</a>
        <a href="#afc">AFC</a>
        <a href="#nfc">NFC</a>
    </nav>

    <div class="content">

        <div class="season-bar" id="seasonBar"></div>

        <!-- Schedule -->
        <section class="section" id="schedule">
            <h2 class="section-title">2026 Regular Season Schedule</h2>
            <p class="section-note">
                All 272 games, September 9, 2026 through January 10, 2027. Kickoff times are Eastern
                and subject to flexible scheduling from Week 5 on.
                Pick a week &mdash; weeks with completed games are marked with a dot.
            </p>
            <div class="week-tabs" id="weekTabs" role="tablist" aria-label="Select week"></div>
            <div id="weekPanel" role="tabpanel"></div>
        </section>

        <!-- Playoff picture -->
        <section class="section" id="playoffs">
            <h2 class="section-title">&#127944; Playoff Picture</h2>
            <p class="section-note">
                Seeded from actual results to date: four division leaders, then the next three teams
                by record as wild cards. Straight win-percentage order &mdash; the NFL's full
                head-to-head and common-games tiebreakers are not applied, so treat close seeds as a
                coin flip. Entertainment only.
            </p>
            <div class="two-col" id="playoffPanels"></div>
        </section>

        <!-- AFC -->
        <div class="conference" id="afc">
            <h2 class="conference-title">American Football Conference (AFC)</h2>
{dir_html('AFC')}
        </div>

        <!-- NFC -->
        <div class="conference" id="nfc">
            <h2 class="conference-title">National Football Conference (NFC)</h2>
{dir_html('NFC')}
        </div>

    </div>

    <div class="footer">
        <p>&copy; 2026 Big Sarge Game Day Center | Team names and logos are property of the National Football League</p>
        <p>Schedule and results data from <a href="https://github.com/nflverse/nfldata" target="_blank" rel="noopener noreferrer">nflverse</a> &middot; last updated {today}</p>
    </div>
</div>

<script id="nflData" type="application/json">{json.dumps(data, separators=(',', ':'))}</script>
<script>
(function () {{
    'use strict';

    var DATA = JSON.parse(document.getElementById('nflData').textContent);
    var GAMES = DATA.games, TEAMS = DATA.teams;
    var DIV_ORDER = ['East', 'North', 'South', 'West'];
    var TAG_LABEL = {{ tnf: 'Thursday Night', mnf: 'Monday Night', sat: 'Saturday', intl: 'International' }};

    function el(tag, cls, text) {{
        var n = document.createElement(tag);
        if (cls) n.className = cls;
        if (text != null) n.textContent = text;
        return n;
    }}

    /* ---- records computed from played games ---- */
    var records = {{}};
    Object.keys(TEAMS).forEach(function (t) {{
        records[t] = {{ w: 0, l: 0, t: 0, pf: 0, pa: 0, dw: 0, dl: 0, dt: 0 }};
    }});

    GAMES.forEach(function (g) {{
        if (g.hs == null || g.as == null) return;
        var h = records[g.home], a = records[g.away];
        h.pf += g.hs; h.pa += g.as;
        a.pf += g.as; a.pa += g.hs;
        if (g.hs > g.as) {{ h.w++; a.l++; if (g.div) {{ h.dw++; a.dl++; }} }}
        else if (g.as > g.hs) {{ a.w++; h.l++; if (g.div) {{ a.dw++; h.dl++; }} }}
        else {{ h.t++; a.t++; if (g.div) {{ h.dt++; a.dt++; }} }}
    }});

    function recStr(t) {{
        var r = records[t];
        return r.t ? r.w + '-' + r.l + '-' + r.t : r.w + '-' + r.l;
    }}
    function pct(r) {{
        var n = r.w + r.l + r.t;
        return n ? (r.w + r.t * 0.5) / n : 0;
    }}
    function divPct(r) {{
        var n = r.dw + r.dl + r.dt;
        return n ? (r.dw + r.dt * 0.5) / n : 0;
    }}
    /* win pct, then division record, then point differential, then name */
    function rank(a, b) {{
        var d = pct(records[b]) - pct(records[a]);
        if (d) return d;
        d = divPct(records[b]) - divPct(records[a]);
        if (d) return d;
        d = (records[b].pf - records[b].pa) - (records[a].pf - records[a].pa);
        if (d) return d;
        return TEAMS[a].n.localeCompare(TEAMS[b].n);
    }}

    /* ---- season status ---- */
    function renderSeasonBar() {{
        var bar = document.getElementById('seasonBar');
        var total = GAMES.length;
        var next = GAMES.filter(function (g) {{ return g.hs == null; }})[0];
        var stats = [
            ['Season', '2026', '18 weeks &middot; 272 games'],
            ['Current week', 'Week ' + DATA.currentWeek, DATA.ranges[DATA.currentWeek]],
            ['Games played', DATA.played + ' of ' + total,
             Math.round(DATA.played / total * 100) + '% of the season'],
            ['Next kickoff', next ? next.day + ', ' + fmtDate(next.date) : 'Season complete',
             next ? next.away + ' at ' + next.home + ' &middot; ' + next.time : 'See you in the playoffs']
        ];
        stats.forEach(function (s) {{
            var d = el('div', 'stat');
            d.appendChild(el('div', 'label', s[0]));
            d.appendChild(el('div', 'value', s[1]));
            var sub = el('div', 'sub');
            sub.innerHTML = s[2];
            d.appendChild(sub);
            bar.appendChild(d);
        }});
    }}

    function fmtDate(iso) {{
        var p = iso.split('-');
        var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
        return d.toLocaleDateString('en-US',
            {{ month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' }});
    }}

    /* ---- schedule ---- */
    function gameNode(g) {{
        var done = g.hs != null && g.as != null;
        var node = el('div', 'game' + (done ? ' final' : ''));

        var time = el('div', 'game-time' + (g.tbd ? ' tbd' : ''));
        if (done) {{
            var tag = el('span', 'final-tag', 'FINAL');
            time.appendChild(tag);
        }} else {{
            time.textContent = g.time;
        }}
        node.appendChild(time);

        var m = el('div', 'matchup');
        [[g.away, g.as, g.hs], [g.home, g.hs, g.as]].forEach(function (p, i) {{
            var won = done && p[1] > p[2];
            var side = el('div', 'side' + (won ? ' win' : ''));
            side.appendChild(el('span', 'abbr', p[0]));
            side.appendChild(el('span', 'full', TEAMS[p[0]].n));
            if (done) side.appendChild(el('span', 'score', String(p[1])));
            m.appendChild(side);
        }});
        node.appendChild(m);

        var tags = el('div', 'tags');
        if (g.kind) tags.appendChild(el('span', 'tag ' + g.kind, TAG_LABEL[g.kind]));
        if (g.div) tags.appendChild(el('span', 'tag div', 'Division'));
        if (g.intl) tags.appendChild(el('span', 'venue', g.intl));
        node.appendChild(tags);

        return node;
    }}

    function renderWeek(wk) {{
        var panel = document.getElementById('weekPanel');
        panel.textContent = '';

        var head = el('div', 'week-head');
        head.appendChild(el('h3', null, 'Week ' + wk));
        head.appendChild(el('span', 'dates', DATA.ranges[wk]));
        panel.appendChild(head);

        if (DATA.notes[wk]) {{
            panel.appendChild(el('div', 'week-note', DATA.notes[wk]));
        }}

        var wkGames = GAMES.filter(function (g) {{ return g.wk === wk; }});
        var seen = [];
        wkGames.forEach(function (g) {{
            if (seen.indexOf(g.date) === -1) seen.push(g.date);
        }});

        seen.forEach(function (date) {{
            var grp = el('div', 'day-group');
            var dayGames = wkGames.filter(function (g) {{ return g.date === date; }});
            grp.appendChild(el('div', 'day-label', dayGames[0].day + ', ' + fmtDate(date)));
            var list = el('div', 'game-list');
            dayGames.forEach(function (g) {{ list.appendChild(gameNode(g)); }});
            grp.appendChild(list);
            panel.appendChild(grp);
        }});

        if (DATA.byes[wk]) {{
            var b = el('div', 'byes');
            b.appendChild(el('strong', null, 'On bye: '));
            b.appendChild(document.createTextNode(
                DATA.byes[wk].map(function (t) {{ return TEAMS[t].n; }}).join(', ')));
            panel.appendChild(b);
        }}
    }}

    function renderTabs() {{
        var tabs = document.getElementById('weekTabs');
        var buttons = [];

        for (var wk = 1; wk <= 18; wk++) {{
            (function (w) {{
                var b = el('button', 'week-tab');
                b.type = 'button';
                b.setAttribute('role', 'tab');
                b.id = 'wk-tab-' + w;
                b.appendChild(document.createTextNode('Week ' + w));
                if (GAMES.some(function (g) {{ return g.wk === w && g.hs != null; }})) {{
                    b.appendChild(el('span', 'dot'));
                }}
                b.addEventListener('click', function () {{ select(w); }});
                b.addEventListener('keydown', function (e) {{
                    var next = e.key === 'ArrowRight' ? w + 1 : e.key === 'ArrowLeft' ? w - 1 : 0;
                    if (!next || next < 1 || next > 18) return;
                    e.preventDefault();
                    select(next);
                    buttons[next - 1].focus();
                }});
                tabs.appendChild(b);
                buttons.push(b);
            }})(wk);
        }}

        function select(wk) {{
            buttons.forEach(function (b, i) {{
                var on = i + 1 === wk;
                b.setAttribute('aria-selected', on ? 'true' : 'false');
                b.tabIndex = on ? 0 : -1;
            }});
            document.getElementById('weekPanel').setAttribute('aria-labelledby', 'wk-tab-' + wk);
            renderWeek(wk);
            if (history.replaceState) history.replaceState(null, '', '#week-' + wk);
        }}

        var start = DATA.currentWeek;
        var m = /^#week-(\\d+)$/.exec(location.hash);
        if (m && +m[1] >= 1 && +m[1] <= 18) start = +m[1];
        select(start);
    }}

    /* ---- playoff picture ---- */
    function renderPlayoffs() {{
        var wrap = document.getElementById('playoffPanels');

        ['AFC', 'NFC'].forEach(function (conf) {{
            var panel = el('div', 'panel');
            panel.appendChild(el('h3', null, conf + ' Playoff Seeding'));

            var leaders = DIV_ORDER.map(function (div) {{
                return Object.keys(TEAMS).filter(function (t) {{
                    return TEAMS[t].c === conf && TEAMS[t].d === div;
                }}).sort(rank)[0];
            }}).sort(rank);

            var rest = Object.keys(TEAMS).filter(function (t) {{
                return TEAMS[t].c === conf && leaders.indexOf(t) === -1;
            }}).sort(rank).slice(0, 3);

            leaders.concat(rest).forEach(function (t, i) {{
                if (i === 4) {{
                    panel.appendChild(el('div', 'cut', 'Wild cards'));
                }}
                var row = el('div', 'seed' + (i >= 4 ? ' wc' : ''));
                row.appendChild(el('span', 'seed-number', (i + 1) + '.'));
                var name = el('span');
                name.appendChild(document.createTextNode(TEAMS[t].n));
                name.appendChild(el('span', 'role',
                    i < 4 ? TEAMS[t].c + ' ' + TEAMS[t].d + ' leader' : 'Wild card'));
                row.appendChild(name);
                row.appendChild(el('span', 'rec', recStr(t)));
                panel.appendChild(row);
            }});

            wrap.appendChild(panel);
        }});
    }}

    function renderRecords() {{
        Array.prototype.forEach.call(
            document.querySelectorAll('[data-record]'),
            function (n) {{ n.textContent = recStr(n.getAttribute('data-record')); }});
    }}

    renderSeasonBar();
    renderTabs();
    renderPlayoffs();
    renderRecords();
}})();
</script>
</body>
</html>
'''

OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes)")
print(f"games={len(games)} weeks={len(weeks)} played={len(played)} current_week={current_wk}")
print("byes:", {k: len(v) for k, v in sorted(byes.items())})
