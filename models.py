from itertools import cycle

from bokeh.core.enums import LineDash, MarkerType, NamedColor
from bokeh.models import Column, LegendItem, Panel
from bokeh.models.widgets import Button, ColorPicker, Select, Slider, TextInput
from bokeh.palettes import Category10_10  # pylint: disable=no-name-in-module

COLORS = cycle(Category10_10)

prettify = lambda p: p.replace("_", " ").capitalize()


class Series:
    labels = []
    id = 0

    def __init__(self, label, plot, renderer):
        self.id = Series.id
        Series.id += 1
        while label in self.labels:
            try:
                last_number = int(label.split(" ")[-1])
                last_number += 1
                label = label[: -len(str(last_number))] + str(last_number)
            except:
                label = label + " 1"
        self.labels.append(label)
        self.plot = plot
        self.glyph = renderer.glyph
        legend_item = LegendItem(label=label, renderers=[renderer])
        self.plot.legend.items.append(legend_item)
        self.legend_label = TextInput(title="Legend label", value=label)
        self.legend_label.on_change("value", self.update_legend_label)
        self.panel = Panel(child=Column(self.legend_label, width=360), title=label)
        self.panel.child.children.append(get_widgets(self.glyph))
        self.delete_button = Button(label="Delete glyph", button_type="danger")
        self.panel.child.children.append(self.delete_button)

    def update_legend_label(self, attr, old, new):
        legend_items = self.plot.legend.items
        for item in legend_items:
            if self.glyph in [r.glyph for r in item.renderers]:
                item.label["value"] = new
        legend_items = list(legend_items)
        self.plot.legend.items = []
        self.plot.legend.items = legend_items


def line_series(plot, **kw):
    """Adidiona um glyph do tipo line ao gráfico.

    Args:
        plot (bokeh.plotting.Figure): gráfico.
        kw: keyword-argument's para o glyph.

    Return:
        Series: objeto associado com o glyph no gráfico.
    """
    renderer = plot.line(line_color=next(COLORS), line_width=2, **kw)
    return Series("Line 1", plot, renderer)


def scatter_series(plot, **kw):
    """Adidiona um glyph do tipo scatter ao gráfico.

    Args:
        plot (bokeh.plotting.Figure): gráfico.
        kw: keyword-argument's para o glyph.

    Return:
        Series: objeto associado com o glyph no gráfico.
    """
    renderer = plot.scatter(color=next(COLORS), line_width=1, **kw)
    return Series("Scatter 1", plot, renderer)


def get_widgets(model):
    widgets_list = []
    for p, v in model.properties_with_values().items():
        if isinstance(v, dict):
            if "value" in v:
                v = v.get("value")
            else:
                continue
        if v is None:
            continue

        kw = dict(title=prettify(p), name=prettify(p), value=v, width=360)
        if "alpha" in p:
            w = Slider(start=0, step=0.05, end=1, **kw)
        elif "color" in p:
            if v in list(NamedColor):
                w = Select(options=list(NamedColor), **kw)
            else:
                kw.pop("value")
                w = ColorPicker(color=v, **kw)
        elif p.endswith("width"):
            w = Slider(start=0, step=0.2, end=5, **kw)
        elif "marker" in p:
            w = Select(options=list(MarkerType), **kw)
        elif p == "size":
            w = Slider(start=0, step=1, end=20, **kw)
        elif p.endswith("text") or p.endswith("label"):
            w = TextInput(**kw)
        else:
            continue
        if isinstance(w, ColorPicker):
            w.js_link("color", model, p)
        else:
            w.js_link("value", model, p)
        widgets_list.append(w)
    if widgets_list:
        return Column(*sorted(widgets_list, key=lambda w: w.name), width=380)
    return None
