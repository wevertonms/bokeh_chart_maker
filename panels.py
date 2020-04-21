from bokeh import models
from bokeh.models.widgets import Button, Select
from bokeh.layouts import column, row
from models import get_widgets


class AnnotationPanel:
    """Annotation's Panel."""

    def __init__(self, title, plot):
        self._annotations_tabs = models.Tabs()
        self._add_annotation_button = Button(
            label="Add", button_type="success", width=50, align="end"
        )
        self._select = Select(
            title="Annotation type", options=["Span", "Box"], width=320, value="Span",
        )
        self._add_annotation_button.on_click(self.add_annotation)
        self.panel = models.Panel(
            title=title,
            child=column(
                [
                    row(self._select, self._add_annotation_button),
                    self._annotations_tabs,
                ],
                sizing_mode="stretch_width",
            ),
        )
        self.plot = plot

    def add_annotation(self, event):
        kind = self._select.value
        if kind == "Span":
            annotation = Span(self.plot)  # , dimension="height"
        else:
            annotation = Box(self.plot)
        self.plot.add_layout(annotation.annotation)
        self._annotations_tabs.tabs.append(
            models.Panel(title=kind, child=column([annotation.controls]))
        )


class Annotation:
    _id = 0
    annotation = None
    renderer = None

    def __init__(self, plot, label):
        self._id += 1
        self.label = f"{label} {self._id}"
        self.plot = plot
        self.controls = get_widgets(self.annotation)
        legend_item = models.LegendItem(label=label, renderers=[self.renderer])
        self.plot.legend.items.append(legend_item)
        self.legend_label = models.TextInput(title="Legend label", value=label)
        self.legend_label.on_change("value", self.update_legend_label)
        self.controls.children.insert(0, self.legend_label)
        toggle_visible = models.Toggle(label="Visible", active=True, name="Visible")
        toggle_visible.js_link("active", self.annotation, "visible")
        self.controls.children.append(toggle_visible)
        # annotation_props = set(self.annotation.properties())
        # legend_label_props = set(self.legend_label.properties())
        # for p in annotation_props.intersection(legend_label_props):
        #     prop = getattr(self.annotation, p)
        #     prop.js_link("value", model, p)

    def update_legend_label(self, attr, old, new):
        legend_items = self.plot.legend.items
        for item in legend_items:
            if self.renderer.glyph in [r.glyph for r in item.renderers]:
                item.label["value"] = new
        legend_items = list(legend_items)
        self.plot.legend.items = []
        self.plot.legend.items = legend_items


class Span(Annotation):
    def __init__(self, plot, label="Span", **kw):
        self.annotation = models.Span(**kw)
        self.renderer = plot.line()
        super().__init__(plot, label)
        location = models.TextInput(title="Location", value="0")
        location.on_change("value", self.update_location)
        self.controls.children.append(location)
        dimension = models.Select(
            title="Dimension", options=["height", "width"], value="height"
        )
        dimension.js_link("value", self.annotation, "dimension")
        self.controls.children.append(dimension)

    def update_location(self, attr, old, new):
        self.annotation.location = float(new)


class Box(Annotation):
    def __init__(self, plot, label="Box", **kw):
        self.annotation = models.BoxAnnotation(**kw)
        self.renderer = plot.rect(**kw)
        super().__init__(plot, label)
