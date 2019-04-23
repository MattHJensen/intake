#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2019, Anaconda, Inc. and Intake contributors
# All rights reserved.
#
# The full license is in the LICENSE file, distributed with this software.
#-----------------------------------------------------------------------------

import os
from functools import partial

import intake
import panel as pn

from ..base import Base, MAX_WIDTH, enable_widget, ICONS


class FileSelector(Base):
    """
    Panel interface for picking files

    The current path is stored in .path and the current selection is stored in
    .url.

    Parameters
    ----------
    filters: list of string
        extentions that are included in the list of files - correspond to
        catalog extensions.
    done_callback: func, opt
        called when the object's main job has completed. In this case,
        selecting a file.

    Attributes
    ----------
    url: str
        path to local catalog file
    children: list of panel objects
        children that will be used to populate the panel when visible
    panel: panel layout object
        instance of a panel layout (row or column) that contains children
        when visible
    watchers: list of param watchers
        watchers that are set on children - cleaned up when visible
        is set to false.
    """
    def __init__(self, filters=['yaml', 'yml'], done_callback=None,  **kwargs):
        self.filters = filters
        self.panel = pn.Column(name='Local', width_policy='max', margin=0)
        self.done_callback = done_callback
        super().__init__(**kwargs)

    def setup(self):
        self.path_text = pn.widgets.TextInput(value=os.getcwd() + os.path.sep,
                                              width_policy='max')
        self.validator = pn.pane.SVG(None, width=25)
        self.main = pn.widgets.MultiSelect(size=15, width_policy='max')
        self.home = pn.widgets.Button(name='🏠', width=40, height=30)
        self.up = pn.widgets.Button(name='‹', width=30, height=30)

        self.make_options()

        self.watchers = [
            self.path_text.param.watch(self.validate, ['value']),
            self.path_text.param.watch(self.make_options, ['value']),
            self.home.param.watch(self.go_home, 'clicks'),
            self.up.param.watch(self.move_up, 'clicks'),
            self.main.param.watch(self.move_down, ['value'])
        ]

        self.children = [
            pn.Row(self.home, self.up, self.path_text, self.validator, margin=0),
            self.main
        ]

    @property
    def path(self):
        path = self.path_text.value
        return path if path.endswith(os.path.sep) else path + os.path.sep

    @property
    def selected(self):
        return self.main.value[0] if len(self.main.value) > 0 else []

    @property
    def url(self):
        """Path to local catalog file"""
        if self.selected is not None:
            return os.path.join(self.path, self.selected)

    def move_up(self, arg=None):
        self.path_text.value = os.path.dirname(self.path.rstrip(os.path.sep)) + os.path.sep

    def go_home(self, arg=None):
        self.path_text.value = os.getcwd() + os.path.sep

    def validate(self, arg=None):
        """Check that inputted path is valid - set validator accordingly"""
        if os.path.isdir(self.path):
            self.validator.object = None
        else:
            self.validator.object = ICONS['error']

    def make_options(self, arg=None):
        if self.done_callback:
            self.done_callback(False)
        out = []
        if os.path.isdir(self.path):
            for f in sorted(os.listdir(self.path)):
                if f.startswith('.'):
                    continue
                elif os.path.isdir(os.path.join(self.path, f)):
                    out.append(f + os.path.sep)
                elif any(f.endswith(ext) for ext in self.filters):
                    out.append(f)

        self.main.value = []
        self.main.options = dict(zip(out, out))

    def move_down(self, *events):
        for event in events:
            if event.name == 'value' and len(event.new) > 0:
                fn = event.new[0]
                if fn.endswith(os.path.sep):
                    self.path_text.value = self.path + fn
                    self.make_options()
                elif os.path.isfile(self.url) and self.done_callback:
                    self.done_callback(True)

    def __getstate__(self):
        return {
            'path': self.path,
            'selected': self.selected
        }

    def __setstate__(self, state):
        self.path_text.value = state['path']
        self.main.value = state['selected']
        return self

class URLSelector(Base):
    """
    Panel interface for inputting a URL to a remote catalog

    The inputted URL is stored in .url.

    Attributes
    ----------
    url: str
        url to remote files (including protocol)
    children: list of panel objects
        children that will be used to populate the panel when visible
    panel: panel layout object
        instance of a panel layout (row or column) that contains children
        when visible
    watchers: list of param watchers
        watchers that are set on children - cleaned up when visible
        is set to false.
    """
    def __init__(self, **kwargs):
        self.panel = pn.Row(name='Remote',
                            width_policy='max', margin=0)
        super().__init__(**kwargs)

    def setup(self):
        self.main = pn.widgets.TextInput(
            placeholder="Full URL with protocol",
            width_policy='max')
        self.children = ['URL:', self.main]

    @property
    def url(self):
        """URL to remote files (including protocol)"""
        return self.main.value

    def __getstate__(self):
        return {'url': self.url}

    def __setstate__(self, state):
        self.main.value = state['url']
        return self

class CatAdder(Base):
    """Panel for adding new cats from local file or remote

    Parameters
    ----------
    done_callback: function with cat as input
        function that is called when the "Add Catalog" button is clicked.

    Attributes
    ----------
    cat_url: str
        url to remote files or path to local files. Depends on active tab
    cat: catalog
        catalog object initialized from from cat_url
    children: list of panel objects
        children that will be used to populate the panel when visible
    panel: panel layout object
        instance of a panel layout (row or column) that contains children
        when visible
    watchers: list of param watchers
        watchers that are set on children - cleaned up when visible
        is set to false.
    """
    tabs = None

    def __init__(self, done_callback=None, **kwargs):
        self.done_callback = done_callback
        self.panel = pn.Column(name='Add Catalog',
                               width_policy='max',
                               max_width=MAX_WIDTH,
                               margin=0)
        self.widget = pn.widgets.Button(name='Add Catalog',
                                        disabled=True,
                                        width_policy='min')
        self.fs = FileSelector(done_callback=partial(enable_widget, self.widget))
        self.url = URLSelector()
        super().__init__(**kwargs)

    def setup(self):
        self.selectors = [self.fs, self.url]
        self.tabs = pn.Tabs(*map(lambda x: x.panel, self.selectors))
        self.validator = pn.pane.SVG(None, width=25)

        self.watchers = [
            self.widget.param.watch(self.add_cat, 'clicks'),
            self.tabs.param.watch(self.tab_change, 'active'),
            self.fs.main.param.watch(self.remove_error, 'value'),
            self.url.main.param.watch(self.remove_error, 'value'),
        ]

        self.children = [self.tabs, pn.Row(self.widget, self.validator)]

    @property
    def cat_url(self):
        """URL to remote files or path to local files. Depends on active tab."""
        return self.selectors[self.tabs.active].url

    @property
    def cat(self):
        """Catalog object initialized from from cat_url"""
        # might want to do some validation in here
        return intake.open_catalog(self.cat_url)

    def add_cat(self, arg=None):
        """Add cat and close panel"""
        try:
            self.done_callback(self.cat)
            self.visible = False
        except Exception as e:
            self.validator.object = ICONS['error']
            raise e

    def remove_error(self, *args):
        """Remove error from the widget"""
        self.validator.object = None

    def tab_change(self, event):
        """When tab changes remove error, and enable widget if on url tab"""
        self.remove_error()
        if event.new == 1:
            self.widget.disabled = False

    def __getstate__(self):
        return {
            'visible': self.visible,
            'local': self.fs.__getstate__(),
            'remote': self.url.__getstate__(),
            'active': self.tabs.active if self.tabs else 0
        }

    def __setstate__(self, state):
        self.fs.__setstate__(state['local'])
        self.url.__setstate__(state['remote'])
        self.visible = state.get('visible', True)
        if self.visible:
            self.tabs.active = state['active']
        return self
