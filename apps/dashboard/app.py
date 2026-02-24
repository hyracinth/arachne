# $env:PYTHONPATH = "."
# shiny run --reload --launch-browser apps/dashboard/app.py

import pandas as pd
from ipyleaflet import Map, Marker, basemaps, AwesomeIcon, AntPath, CircleMarker, Polyline
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
            .card { border: 1px solid #2a2a2a; background-color: #121212; }

            path[stroke='#28f049']  {
                animation: linePulse 4s ease-in-out infinite !important;
            }
            @keyframes linePulse {
                0% { opacity: 0.4; }
                50% { opacity: 0.8; }
                100% { opacity: 0.4; }
            }

            path[stroke='red'] {
                animation: beacon 3s ease-out infinite !important;
                transform-origin: center;
                transform-box: fill-box;
            }
            @keyframes beacon {
                0% { transform: scale(3); opacity: 0.1; }
                100% { transform: scale(1); opacity: 0.7; }
            }

        """)
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("project: arachne"),
            ui.p(output_widget("map")),
        ),
        ui.card(
            ui.card(
                ui.card_header("scan duration"), 
                ui.input_slider(id="duration_slider", label="", min=1, max=168, value=24),
            ),
            ui.card(
                ui.card_header("total threats"), 
                ui.output_text_verbatim("duration_slider_value"),),
            ui.card(
                ui.card_header("attack logs"), 
                ui.p("[HH:mm:ss] Logged attack from XYZ..."),
                ui.p("[HH:mm:ss] Logged attack from ABC..."),
                ui.p("[HH:mm:ss] Logged attack from AAA..."),
                ui.p("[HH:mm:ss] Logged attack from BBB..."),
            ),
        ),
        col_widths=(8,4)
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
    @render.text
    def duration_slider_value():
        return f"{len(enriched_attacks_map())}"
    
    @reactive.calc
    def enriched_attacks_map():
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

        attacks = enriched_attacks_map()

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