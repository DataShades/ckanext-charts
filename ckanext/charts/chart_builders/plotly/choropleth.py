from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
from humanize import intword

from ckanext.charts import exception

from .base import BasePlotlyForm, PlotlyBuilder

# silence SettingWithCopyWarning
pd.options.mode.chained_assignment = None


class PlotlyChoroplethBuilder(PlotlyBuilder):
    colors = ["#DBEDF8", "#B7DBF2", "#93CAEB", "#6FB8E5", "#009ADE", "#004E70"]
    custom_color_scale = "aazure"

    def to_json(self) -> Any:
        return self.build_choropleth_chart()

    def build_choropleth_chart(self) -> Any:
        """Renders a choropleth map using Plotly.

        The `locations` field must be the ISO 3166-1 alpha-3 country codes.
        The `color` field must be a numeric/string value that corresponds to
        the color scale.

        For string values, we can use the `legend` instead of `coloraxis`.

        We should investigate if the choropleth supports date values.
        """

        infer_iso_a3 = self.settings["infer_iso_a3"]

        # Create a new column with the ISO alpha-3 country code and try
        # to infer it from the country name if the flag is enabled.
        if infer_iso_a3:
            try:
                self.df["__iso_a3"] = self.df[self.settings["x"]].apply(
                    lambda x: (
                        pycountry.countries.get(name=x).alpha_3  # type: ignore
                        if pycountry.countries.get(name=x)
                        else None
                    ),
                )
            except LookupError:
                raise exception.ChartBuildError(
                    "Error while trying to infer the ISO alpha-3 country code.",
                ) from None

        fig = px.choropleth(
            self.df,
            locations=self.settings["x"] if not infer_iso_a3 else "__iso_a3",
            color=self.settings["y"],
            hover_name=self.settings["y"],
            color_continuous_scale=self._get_color_scale(),
            range_color=(
                self.df[self.settings["y"]].min(),
                self.df[self.settings["y"]].max(),
            ),
        )

        # change the hover tooltip template
        fig.update_traces(
            hovertemplate="<b>Region Code: %{location}<br>Value: %{z}<extra></extra>",
        )

        fig.update_layout(
            dragmode=False,  # Disable dragging
            uirevision="constant",  # Disable zooming
            height=600,  # Set the height of the plot
            margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
            legend={
                "title": "",  # remove the legend title
                "orientation": "h",  # Horizontal orientation
            },
            coloraxis=self._get_coloraxis_settings(),
            hoverlabel={  # change hover label bg and font-size
                "bgcolor": "white",
                "font_size": 16,
            },
        )

        fig.update_geos(
            showcoastlines=True,  # Display coastlines
            coastlinewidth=0.1,  # Set the thickness of the coastline
            showland=True,  # Display land masses
            showcountries=True,  # Show country borders
            countrycolor="white",  # Border color between countries
            showrivers=False,  # Hide rivers
            showlakes=True,  # Display lakes
            projection={"type": self.settings["projection"]},  # map projection type
            showframe=False,  # Remove the border around the projection
            resolution=50,  # Set the resolution of the map
            lataxis={"range": [-60, 80]},  # Exclude Antarctica
            lonaxis={"range": [-180, 210]},  # Move the map a bit right
        )

        if self.settings["color_scale"] == self.custom_color_scale:
            fig.update_geos(
                coastlinecolor="#B3B3B3",  # Set the color of the coastline
                lakecolor="#B3B3B3",  # Set lake color
                landcolor="#B7DBF2",  # Set land mass color
            )

        self._update_location_mode(fig)

        return fig.to_json()

    def _get_color_scale(self) -> list[tuple[float, str]]:
        """Get the color scale for the choropleth map.

        Returns:
            list of tuples with the color scale
        """
        # blue is our custom color scale
        if self.settings["color_scale"] != self.custom_color_scale:
            return self.settings["color_scale"]

        colors_scale = []

        for i in range(len(self.colors)):
            start = i / len(self.colors)
            end = (i + 1) / len(self.colors)

            colors_scale.append((start, self.colors[i]))
            colors_scale.append((end, self.colors[i]))

        return colors_scale

    def _get_coloraxis_settings(self) -> dict[str, Any]:
        if not self._is_numeric():
            return {}

        vals = np.linspace(
            self.df[self.settings["y"]].min(),
            self.df[self.settings["y"]].max(),
            len(self.colors) + 1,
        )

        ticktext = [intword(num) for num in vals]

        settings = {
            "colorbar": {
                "x": 0.5,  # Center horizontally
                "y": -0.2,  # Move it down
                "orientation": "h",  # Horizontal orientation
                "title": "",  # remove the scale label
                "xpad": 50,  # Adjust X axis padding
                "yanchor": "bottom",  # Anchor the colorbar to the bottom
                "tickvals": vals,  # Set the tick values
                "ticktext": ticktext,  # Set the tick text
                "ticklabelposition": "outside",  # Place the tick labels pos
            },
        }

        if self.settings["show_scale_ticks"]:
            # will work only if the column is numeric
            # for string we can skip it, as it will use `legend` instead of `coloraxis`
            # for date we should investigate if choropleth supports it

            settings["colorbar"].update(
                {
                    "ticks": "inside",  # Place the ticks on the colorbar
                    "tickwidth": 1,  # Adjust tick width for visibility
                    "tickfont": {"color": "#3C3B3B"},  # Set tick color
                    "ticklen": 30,  # Adjust tick height
                },
            )

        return settings

    def _is_numeric(self) -> bool:
        column_type = self.df[self.settings["y"]].convert_dtypes().dtype.type

        return column_type in (np.int64, np.float64)

    def _update_location_mode(self, fig: go.Figure) -> None:
        """Update the location mode for the choropleth map.

        It defines the preferred location to display on the map.

        Args:
            fig (go.Figure): Plotly figure
        """
        location_mode = self.settings["location_mode"]

        if location_mode == "europe":
            fig.update_geos(
                lataxis_range=[35, 70],  # Latitude range for Europe
                lonaxis_range=[-25, 45],  # Longitude range for Europe
            )
        elif location_mode == "north_america":
            fig.update_geos(
                lataxis_range=[15, 80],  # Latitude range for North America
                lonaxis_range=[-170, -50],  # Longitude range for North America
            )
        elif location_mode == "south_america":
            fig.update_geos(
                lataxis_range=[-60, 15],  # Latitude range for South America
                lonaxis_range=[-90, -30],  # Longitude range for South America
            )
        elif location_mode == "africa":
            fig.update_geos(
                lataxis_range=[-35, 37],  # Latitude range for Africa
                lonaxis_range=[-20, 55],  # Longitude range for Africa
            )
        elif location_mode == "asia":
            fig.update_geos(
                lataxis_range=[5, 60],  # Latitude range for Asia
                lonaxis_range=[60, 150],  # Longitude range for Asia
            )
        elif location_mode == "oceania":
            fig.update_geos(
                lataxis_range=[-50, 10],  # Latitude range for Oceania
                lonaxis_range=[110, 180],  # Longitude range for Oceania
            )


class PlotlyChoroplethForm(BasePlotlyForm):
    name = "Choropleth"
    builder = PlotlyChoroplethBuilder

    projections = [
        "airy",
        "aitoff",
        "albers",
        "albers usa",
        "august",
        "azimuthal equal area",
        "azimuthal equidistant",
        "baker",
        "bertin1953",
        "boggs",
        "bonne",
        "bottomley",
        "bromley",
        "collignon",
        "conic conformal",
        "conic equal area",
        "conic equidistant",
        "craig",
        "craster",
        "cylindrical equalarea",
        "cylindrical stereographic",
        "eckert1",
        "eckert2",
        "eckert3",
        "eckert4",
        "eckert5",
        "eckert6",
        "eisenlohr",
        "equal earth",
        "equirectangular",
        "fahey",
        "foucaut",
        "foucaut sinusoidal",
        "ginzburg4",
        "ginzburg5",
        "ginzburg6",
        "ginzburg8",
        "ginzburg9",
        "gnomonic",
        "gringorten",
        "gringorten quincuncial",
        "guyou",
        "hammer",
        "hill",
        "homolosine",
        "hufnagel",
        "hyperelliptical",
        "kavrayskiy7",
        "lagrange",
        "larrivee",
        "laskowski",
        "loximuthal",
        "mercator",
        "miller",
        "mollweide",
        "mt flat polar parabolic",
        "mt flat polar quartic",
        "mt flat polar sinusoidal",
        "natural earth",
        "natural earth1",
        "natural earth2",
        "nell hammer",
        "nicolosi",
        "orthographic",
        "patterson",
        "peirce quincuncial",
        "polyconic",
        "rectangular polyconic",
        "robinson",
        "satellite",
        "sinu mollweide",
        "sinusoidal",
        "stereographic",
        "times",
        "transverse mercator",
        "van der grinten",
        "van der grinten2",
        "van der grinten3",
        "van der grinten4",
        "wagner4",
        "wagner6",
        "wiechel",
        "winkel tripel",
        "winkel3",
    ]

    color_scales = [
        "aggrnyl",
        "agsunset",
        "blackbody",
        "bluered",
        "blues",
        "blugrn",
        "bluyl",
        "brwnyl",
        "bugn",
        "bupu",
        "burg",
        "burgyl",
        "cividis",
        "darkmint",
        "electric",
        "emrld",
        "gnbu",
        "greens",
        "greys",
        "hot",
        "inferno",
        "jet",
        "magenta",
        "magma",
        "mint",
        "orrd",
        "oranges",
        "oryel",
        "peach",
        "pinkyl",
        "plasma",
        "plotly3",
        "pubu",
        "pubugn",
        "purd",
        "purp",
        "purples",
        "purpor",
        "rainbow",
        "rdbu",
        "rdpu",
        "redor",
        "reds",
        "sunset",
        "sunsetdark",
        "teal",
        "tealgrn",
        "turbo",
        "viridis",
        "ylgn",
        "ylgnbu",
        "ylorbr",
        "ylorrd",
        "algae",
        "amp",
        "deep",
        "dense",
        "gray",
        "haline",
        "ice",
        "matter",
        "solar",
        "speed",
        "tempo",
        "thermal",
        "turbid",
        "armyrose",
        "brbg",
        "earth",
        "fall",
        "geyser",
        "prgn",
        "piyg",
        "picnic",
        "portland",
        "puor",
        "rdgy",
        "rdylbu",
        "rdylgn",
        "spectral",
        "tealrose",
        "temps",
        "tropic",
        "balance",
        "curl",
        "delta",
        "oxy",
        "edge",
        "hsv",
        "icefire",
        "phase",
        "twilight",
        "mrybm",
        "mygbm",
    ]

    def get_form_fields(self):
        """Get the form fields for the Plotly scatter chart."""
        columns = [{"value": col, "label": col} for col in self.get_all_column_names()]
        chart_types = [
            {"value": form.name, "label": form.name}
            for form in self.builder.get_supported_forms()
        ]
        projections = [
            {"value": projection, "label": projection}
            for projection in self.projections
        ]

        return [
            self.title_field(),
            self.description_field(),
            self.engine_field(),
            self.type_field(chart_types),
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.infer_iso_a3_field(),
            self.projection_field(projections),
            self.location_mode_field(),
            self.color_scale_field(),
            self.show_scale_ticks_field(),
            self.filter_field(columns),
            self.limit_field(default=1000),
        ]

    def projection_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "projection",
            "label": "Projection",
            "group": "Styles",
            "type": "text",
            "default": "eckert5",
            "help_text": "Set the map projection type.",
            "form_snippet": "chart_select.html",
            "required": True,
            "choices": choices,
            "validators": [
                self.get_validator("default")("eckert5"),
                self.get_validator("unicode_safe"),
            ],
        }

    def infer_iso_a3_field(self) -> dict[str, Any]:
        return {
            "field_name": "infer_iso_a3",
            "label": "Infer ISO alpha-3 country code",
            "group": "Data",
            "help_text": "Try to infer the ISO_A3 code from the country name.",
            "form_snippet": "chart_checkbox.html",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(True),
                self.get_validator("boolean_validator"),
            ],
            "type": "bool",
            "default": False,
        }

    def location_mode_field(self) -> dict[str, Any]:
        return {
            "field_name": "location_mode",
            "label": "Location",
            "group": "Styles",
            "help_text": "Set the location to display on the map.",
            "form_snippet": "chart_select.html",
            "choices": [
                {"value": "world", "label": "World"},
                {"value": "europe", "label": "Europe"},
                {"value": "north_america", "label": "North America"},
                {"value": "south_america", "label": "South America"},
                {"value": "africa", "label": "Africa"},
                {"value": "asia", "label": "Asia"},
                {"value": "oceania", "label": "Oceania (Australia & Pacific Islands)"},
            ],
            "validators": [
                self.get_validator("default")("world"),
                self.get_validator("unicode_safe"),
            ],
            "type": "text",
            "default": "world",
        }

    def color_scale_field(self) -> dict[str, Any]:
        choices = [
            {
                "value": self.builder.custom_color_scale,
                "label": self.builder.custom_color_scale.capitalize(),
            },
        ] + [
            {"value": color, "label": color.capitalize()} for color in self.color_scales
        ]

        return {
            "field_name": "color_scale",
            "label": "Color Scale",
            "group": "Styles",
            "help_text": "Set the color scale for the choropleth map.",
            "form_snippet": "chart_select.html",
            "choices": choices,
            "validators": [
                self.get_validator("default")(self.builder.custom_color_scale),
                self.get_validator("unicode_safe"),
            ],
            "type": "text",
            "default": "blue",
        }

    def show_scale_ticks_field(self) -> dict[str, Any]:
        return {
            "field_name": "show_scale_ticks",
            "label": "Show Scale Ticks",
            "group": "Styles",
            "help_text": "Show the scale ticks on the colorbar.",
            "form_snippet": "chart_checkbox.html",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(True),
                self.get_validator("boolean_validator"),
            ],
            "type": "bool",
            "default": True,
        }
