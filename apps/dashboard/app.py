# $env:PYTHONPATH = "."
# shiny run --reload --launch-browser apps/dashboard/app.py

from collections import Counter

import pandas as pd
from ipyleaflet import Map, Marker, basemaps, AwesomeIcon, CircleMarker, Polyline
from ipywidgets import HTML # for popups
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget

from apps.shared.database import ArachneDB

db = ArachneDB()
HONEYPOT_COORDS = (41.2619,-95.8608)

def get_bezier_path(start, end, height=0.3, points=20):
    # Calculate midpoint
    mid_lat = (start[0] + end[0]) / 2
    mid_lon = (start[1] + end[1]) / 2
    
    # height controls how curved the arc is
    ctrl_lat = mid_lat + (abs(start[1] - end[1]) * height)
    ctrl_lon = mid_lon
    
    path_points = []
    for t in [i/points for i in range(points+1)]:
        # Quadratic Bezier Formula: (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
        lat = (1-t)**2 * start[0] + 2*(1-t)*t * ctrl_lat + t**2 * end[0]
        lon = (1-t)**2 * start[1] + 2*(1-t)*t * ctrl_lon + t**2 * end[1]
        path_points.append((lat, lon))
        
    return path_points

app_ui = ui.page_fillable(
    ui.head_content(
        ui.tags.script("""
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        """),
        # Fallback: Target by stroke color because ipyleaflet seems to be ignoring class names
        # or applying them to parent groups, breaking direct css styling
        ui.tags.style("""
            * {
                font-family: 'Courier New', Courier, monospace;          
            }
                      
            .card { border: 1px solid #2a2a2a; background-color: #121212; }

            /* attack line */
            path[stroke='#28f049']  {
                animation: linePulse 4s ease-in-out infinite !important;
            }
            @keyframes linePulse {
                0% { opacity: 0.4; }
                50% { opacity: 0.8; }
                100% { opacity: 0.4; }
            }

            /* target circle */
            path[stroke='red'] {
                animation: beacon 3s ease-out infinite !important;
                transform-origin: center;
                transform-box: fill-box;
            }
            @keyframes beacon {
                0% { transform: scale(3); opacity: 0.1; }
                100% { transform: scale(1); opacity: 0.7; }
            }

            /* slider bar (background) */
            .irs-line {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                height: 8px !important;
                top: 33px !important;
            }

            /* slider bar (selected) */
            .irs-bar {
                background: #28f049 !important;
                border-top: 1px solid #28f049 !important;
                border-bottom: 1px solid #28f049 !important;
                height: 8px !important;
                top: 33px !important;
            }

            /* slider bar (circle) */
            .irs-handle {
                background: #000 !important;
                border: 2px solid #28f049 !important;
                width: 16px !important;
                height: 16px !important;
                top: 28px !important;
                box-shadow: 0 0 8px #28f049 !important; /* Makes the knob glow */
                cursor: pointer !important;
            }

            /* slider bar (text) */
            .irs-single, .irs-min, .irs-max {
                background: transparent !important;
                color: #28f049 !important;
                font-family: 'Courier New', monospace !important;
                font-weight: bold !important;
            }

        """)
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("world map"),
            ui.p(output_widget("map")),
        ),
        ui.card(
            ui.card(
                ui.layout_columns(
                    ui.div(
                        ui.h5("Project:", style="padding-top:10%; color:#666;"),
                        ui.h1("Arachne", style="font-family:Lucida Console; font-weight:700; color:#28f049;"),
                    ),
                    ui.card(
                        ui.card_header("Hours Scanned"), 
                        ui.input_slider(id="duration_slider", label="", min=1, max=168, value=24),
                    ),
                    col_widths=(5,7)
                ),
                ui.layout_columns(
                    ui.value_box(
                        title="Threat Count",
                        value=ui.output_ui("duration_slider_value"),
                    ),
                    ui.value_box(
                        title="Top Country",
                        value=ui.output_ui("top_ip_value"),
                    ),
                    col_widths=(4,8)
                ),
            ),
            ui.card(
                ui.card_header("attack logs"), 
                ui.output_ui("attacks_console_feed")
            ),
        ),
        col_widths=(7,5)
    )
)

# app_ui = ui.page_fluid(
#     ui.panel_title("Arachne Monitor"),
#     ui.input_dark_mode(),
#     ui.navset_card_pill(
#         ui.nav_panel("Live Map", output_widget("map")),
#         ui.nav_panel("Data Grid", ui.output_data_frame("attack_table"))
#     )
# )

def server(input, output, session):
    @render.ui
    def attacks_console_feed():
        attacks = enriched_attacks()
        if not attacks:
            return ui.div("Awaiting attacks", style="color: #444;")
        
        log_entries = [
            ui.div(
                ui.span(f"[{curr_attack.get('timestamp').strftime('%H:%M:%S')}] ", style="color: #666;"),
                ui.span(f"ATTACK: {curr_attack.get('ip_address')} ", style="color: #14bb4c;"),
                ui.span(f"via {curr_attack.get('city')} - {curr_attack.get('country', '??')}", style="color: #ff9d00;"),

                style="font-size: 0.8rem; padding: 2px;"
            ) for curr_attack in attacks[:40]
        ]

        return ui.div(log_entries, style="height: 400px; overflow-y: auto;")

    @render.text
    def top_ip_value():
        attacks = enriched_attacks()
        if not attacks:
            return "N/A"
        
        countries = [a.get('country') for a in attacks if a.get('country')]
        if not countries:
            return "N/A"

        top_ip, count = Counter(countries).most_common(1)[0]
        return f"{top_ip}"

    @render.text
    def duration_slider_value():
        return f"{len(enriched_attacks())}"
    
    @reactive.calc
    def enriched_attacks():
        try:
            data = db.get_enriched(input.duration_slider())
            return data if data else []
        except Exception as e:
            print(f"[ERROR] Failed to retrieve enriched data: {e}")
            return []
    
    @render.data_frame
    def attack_table():
        try:
            attacks = db.get_enriched(50)
        except Exception as e:
            print(f'Error fetching attacks: {e}')
            return render.DataTable(pd.DataFrame(columns=[f'Error fetching attacks: {e}']))

        df = pd.DataFrame(attacks)

        if df.empty:
            return render.DataTable(pd.DataFrame(columns=["No Data Found"]))
        
        return render.DataTable(df)


    @render_widget
    def map():
        m = Map(
                basemap=basemaps.CartoDB.DarkMatter,
                # basemap=basemaps.Esri.WorldImagery,
                # basemap=basemaps.NASAGIBS.ViirsEarthAtNight2012,
                # basemap=basemaps.Stadia.AlidadeSmoothDark,
                scroll_wheel_zoom=True)
        if len(m.layers) > 1:
            m.layers = m.layers[:1]

        attacks = enriched_attacks()

        aggregated_attacks = {}

        min_lat = HONEYPOT_COORDS[0]
        max_lat = HONEYPOT_COORDS[0]
        min_lon = HONEYPOT_COORDS[1]
        max_lon = HONEYPOT_COORDS[1]
        for curratt in attacks:
            lat = curratt.get('latitude')
            lon = curratt.get('longitude')

            if lat is not None and lon is not None:
                if lat < min_lat: min_lat = lat
                if lat > max_lat: max_lat = lat
                if lon < min_lon: min_lon = lon
                if lon > max_lon: max_lon = lon
                curved_points = get_bezier_path(start=(lat, lon), end=HONEYPOT_COORDS, points=10)

                if (lat, lon) not in aggregated_attacks:
                        aggregated_attacks[(lat, lon)] = {
                            "points": curved_points,
                            "count": 1,
                        }
                else:
                    aggregated_attacks[(lat,lon)]["count"] = aggregated_attacks[(lat,lon)]["count"] + 1

        for lat, lon in aggregated_attacks:
            source = CircleMarker(
                location=(lat, lon),
                radius=2,
                color="orange",
                fill_color="orange",
                fill_opacity=0.2,
                weight=1
            )

            line = Polyline(
                locations=aggregated_attacks[(lat, lon)]["points"],
                color="#28f049",
                weight=min(aggregated_attacks[(lat, lon)]["count"], 3),
                opacity=0.4,
                fill=False,
            )
            m.add_layer(line)
            m.add_layer(source)

        target = CircleMarker(
            location=HONEYPOT_COORDS,
            radius=5,
            color="red",
            fill_color="red",
            fill_opacity=0.8,
            weight=1,
        )
        m.add_layer(target)

        # 60% off the bottom to shift view window up
        min_lat = min_lat + (abs(max_lat - min_lat) * 0.6)
        bounds = [
            [min_lat - 1, min_lon - 1], 
            [max_lat + 1, max_lon + 1]
        ]
        m.fit_bounds(bounds)
        return m

app = App(app_ui, server)