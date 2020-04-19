"""Models used to simplify glyphs use."""


from itertools import cycle

from bokeh.core.enums import MarkerType, NamedColor
from bokeh.models import Column, LegendItem, Panel
from bokeh.models.widgets import Button, ColorPicker, Select, Slider, TextInput
from bokeh.palettes import Category10_10  # pylint: disable=no-name-in-module

COLORS = cycle(Category10_10)


def prettify(prop):
    """Makes the property name look prettier.

    Args:
        prop (str): property name

    Returns:
        str: prettier property name
    """
    return prop.replace("_", " ").capitalize()


ID = 0


class Series(object):
    """Wrapper for series glyphs."""

    labels = []

    def __init__(self, label, plot, renderer):
        """Constructor.

        Args:
            label (str): label to show on legend.
            plot (bokeh.Figure): plot do put the series on.
            renderer (bokeh.model.renderer): glyph renderer.
        """
        self.ID = Series.ID
        Series.ID += 1
        while label in self.labels:
            try:
                last_number = int(label.split(" ")[-1])
                last_number += 1
                label = label[: -len(str(last_number))] + str(last_number)
            except:
                label = "% 1" % label
        self.labels.append(label)
        self.plot = plot
        self.glyph = renderer.glyph
        legend_item = LegendItem(label=label, renderers=[renderer])
        self.plot.legend.items.append(legend_item)
        self.legend_label = TextInput(title="Legend label", value=label)
        self.legend_label.on_change("value", self.update_legend_label)
        panel_width = 360
        self.panel = Panel(
            child=Column(self.legend_label, width=panel_width), title=label,
        )
        widgets_list = get_widgets(self.glyph)
        if widgets_list:
            column_width = 380
            self.panel.child.children.append(
                Column(
                    *sorted(widgets_list, key=lambda widget: widget.name),
                    width=column_width,
                )
            )
        self.delete_button = Button(label="Delete glyph", button_type="danger")
        self.panel.child.children.append(self.delete_button)

    def update_legend_label(self, attr, old, new):
        """Update the legend label.

        Args:
            attr (str): updated attribute.
            old (str): old value
            new (str): new value.
        """
        legend_items = self.plot.legend.items
        for item in legend_items:
            if self.glyph in (renderer.glyph for renderer in item.renderers):
                item.label["value"] = new
        legend_items = list(legend_items)
        self.plot.legend.items = []
        self.plot.legend.items = legend_items


def line_series(plot, **kw):
    """Adidiona um glyph do tipo line ao gráfico.

    Args:
        plot (bokeh.plotting.Figure): gráfico.
        kw: keyword-argument's para o glyph.

    Returns:
        Series: objeto associado com o glyph no gráfico.
    """
    renderer = plot.line(line_color=next(COLORS), line_width=2, **kw)
    return Series("Line 1", plot, renderer)


def scatter_series(plot, **kw):
    """Adidiona um glyph do tipo scatter ao gráfico.

    Args:
        plot (bokeh.plotting.Figure): gráfico.
        kw: keyword-argument's para o glyph.

    Returns:
        Series: objeto associado com o glyph no gráfico.
    """
    renderer = plot.scatter(color=next(COLORS), line_width=1, **kw)
    return Series("Scatter 1", plot, renderer)


def prop_to_widget(prop, value):
    kw = {
        "title": prettify(prop),
        "name": prettify(prop),
        "value": value,
        "width": 360,
    }
    if "alpha" in prop:
        slider_step = 0.5
        return Slider(start=0, step=slider_step, end=1, **kw)
    elif "color" in prop:
        if value in list(NamedColor):
            return Select(options=list(NamedColor), **kw)
        kw.pop("value")
        return ColorPicker(color=value, **kw)
    elif prop.endswith("width"):
        slider_step = 0.2
        return Slider(start=0, step=slider_step, end=5, **kw)
    elif "marker" in prop:
        return Select(options=list(MarkerType), **kw)
    elif prop == "size":
        end_value = 20
        return Slider(start=0, step=1, end=end_value, **kw)
    elif prop.endswith("text") or prop.endswith("label"):
        return TextInput(**kw)
    return None


def get_widgets(model):
    """Crate a column width widgets associated to item properties.

    Args:
        model (bokeh.models.Model): model.

    Returns:
        Column: column with the widgets.
    """
    widgets_list = []
    for prop, value in model.properties_with_values().items():
        if isinstance(value, dict):
            if "value" in value:
                value = value.get("value")
            else:
                continue
        if value is None:
            continue
        widget = prop_to_widget(prop, value)
        if isinstance(widget, ColorPicker):
            widget.js_link("color", model, prop)
        else:
            widget.js_link("value", model, prop)
        widgets_list.append(widget)
    return widgets_list
