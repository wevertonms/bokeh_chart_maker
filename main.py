#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small python web application for plotting with Bokeh."""

import base64
import io
from itertools import cycle

import pandas as pd
from bokeh.core.enums import LegendLocation
from bokeh.embed import file_html
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import CustomJS, DataTable, Div, Legend, TableColumn, Tabs
from bokeh.models.widgets import Button, FileInput, Select, TextInput
from bokeh.palettes import Category10_10  # pylint: disable=no-name-in-module
from bokeh.plotting import ColumnDataSource, figure, output_file, save
from bokeh.resources import INLINE
from bokeh.server.server import Server

import models


def create_layout():
    """Inclui o gráficos e os controles no curdoc do Bokeh Server."""
    plot_html = ColumnDataSource(dict(file_html=["Title"], html=[""]))
    plot = figure(
        title="Title",
        sizing_mode="stretch_both",
        tools="wheel_zoom,box_zoom,pan,,crosshair,reset,save",
        # tooltips=[("y", "$y"), ("x", "$x")],
        active_scroll="wheel_zoom",
        toolbar_location="above",
        output_backend="webgl",
    )
    plot.xaxis.axis_label = "X"
    plot.yaxis.axis_label = "Y"
    plot.add_layout(Legend())
    plot.legend.click_policy = "hide"
    plot.legend.background_fill_alpha = 0.6
    table_source = ColumnDataSource()
    side_controls = column(width=400, height=200)
    series_source_controls = row(sizing_mode="scale_width")
    tabs = Tabs()
    models.COLORS = cycle(Category10_10)
    models.Series.labels = []

    def upload_callback(attr, old, new):
        """Função que atualiza os dados do arquivo aberto."""
        file_contents = base64.b64decode(new)
        file_contents_bytes = io.BytesIO(file_contents)
        table_source.data = pd.read_csv(file_contents_bytes).to_dict("list")
        colmmns = list(table_source.data.keys())
        for widget in list(values_selectors.values()):
            widget.options = colmmns
        datatable.columns = [TableColumn(field=_, title=_) for _ in colmmns]

    def update_plot_html(event):
        title = plot.title.text
        file_name = title + ".html"
        # output_file(file_name, title=title, mode="inline")
        # save(plot)
        html = file_html(plot, INLINE, title)
        plot_html.data = dict(file_name=[file_name], html=[html])

    # Widgets (controls) ======================================================
    # Plot controls
    plot_title = TextInput(title="Plot title", value="Title")
    x_title = TextInput(title="X title", value="X")
    y_title = TextInput(title="Y title", value="Y")
    positions = [_.replace("_", "-") for _ in list(LegendLocation)]
    legend_position = Select(title="Legend position", options=positions)
    download_button = Button(label="Download saved", button_type="success", align="end")
    save_button = Button(label="Save", align="end")
    save_button.on_click(update_plot_html)
    with open("download.js") as f:
        callback = CustomJS(args=dict(source=plot_html), code=f.read())
    download_button.js_on_click(callback)
    plot_controls = row(
        plot_title, x_title, y_title, legend_position, save_button, download_button
    )

    def update_plot(attr, old, new):
        plot.title.text = plot_title.value
        plot.xaxis.axis_label = x_title.value
        plot.yaxis.axis_label = y_title.value
        plot.legend.location = legend_position.value.replace("-", "_")

    for widget in plot_controls.children:
        if hasattr(widget, "value"):
            widget.on_change("value", update_plot)
    legend_position.value = "top_left"

    # Series controls
    upload_button = FileInput(accept=".csv")
    upload_button.on_change("value", upload_callback)
    columns = [
        TableColumn(field=_, title=_, width=10) for _ in table_source.data.keys()
    ]
    datatable = DataTable(source=table_source, columns=columns, width=390, height=200)
    values_selectors = {}
    glyph_type = Select(title="Glyph type", options=["line", "scatter"], width=100)

    def update_series_source_controls(attr, old, new):
        colmmns = list(table_source.data.keys())
        kw = dict(options=colmmns, width=80)
        values_selectors["x"] = Select(title=f"x-values", **kw)
        values_selectors["y"] = Select(title=f"y-values", **kw)
        series_source_controls.children = list(values_selectors.values())

    glyph_type.on_change("value", update_series_source_controls)
    glyph_type.value = "line"
    add_button = Button(label="Add glyph", button_type="success", width=50, align="end")
    side_controls.children = [
        Div(text="<h3>Load file</h3>", height=35),
        upload_button,
        datatable,
        row(glyph_type, series_source_controls, add_button, width=390),
        Div(text="<h3>Glyphs</h3>", height=35),
        tabs,
    ]

    def add_series(event):
        any_col = list(table_source.data.keys())[0]
        source = ColumnDataSource()
        for key, selector in values_selectors.items():
            column_name = selector.value or any_col
            source.data[key] = table_source.data[column_name]
        vars_map = dict((k, str(k)) for k in values_selectors.keys())
        if glyph_type.value == "line":
            series = models.line_series(plot, source=source, **vars_map)
        elif glyph_type.value == "scatter":
            series = models.scatter_series(plot, source=source, **vars_map)

        def delete_series(event):
            plot.renderers = [r for r in plot.renderers if r.glyph != series.glyph]
            legend_items = list(plot.legend.items)
            plot.legend.items = [
                item for item in legend_items if series.glyph != item.renderers[0].glyph
            ]
            tabs.tabs = [panel for panel in tabs.tabs if panel != series.panel]

        series.delete_button.on_click(delete_series)
        tabs.tabs.append(series.panel)

    add_button.on_click(add_series)
    return [side_controls, column(plot_controls, plot, sizing_mode="stretch_width")]


def modify_doc(doc):
    """Inclui o gráficos e os controles no curdoc do Bokeh Server."""
    layout = row(sizing_mode="stretch_both")
    layout.children = create_layout()
    doc.add_root(layout)
    doc.title = "Chart Studio"


if __name__ == "__main__":
    server = Server({"/": modify_doc})
    server.start()
    print(f"Opening Bokeh application on http://localhost:5006/")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    layout = row(sizing_mode="stretch_both")
    layout.children = create_layout()
    curdoc().add_root(layout)
    curdoc().title = "Chart Studio"
