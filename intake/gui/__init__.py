#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2018, Anaconda, Inc. and Intake contributors
# All rights reserved.
#
# The full license is in the LICENSE file, distributed with this software.
#-----------------------------------------------------------------------------
from distutils.version import LooseVersion


def do_import():
    error = too_old = False
    try:
        import panel as pn
        too_old = LooseVersion(pn.__version__) < LooseVersion("0.9.5")
    except ImportError as e:
        error = e

    if too_old or error:
        class GUI(object):
            def __repr__(self):
                raise RuntimeError("Please install panel to use the GUI `conda "
                                   "install -c conda-forge panel>=0.8.0`. Import "
                                   "failed with error: %s" % error)
        return GUI

    try:
        from .gui import GUI
        css = """
        .scrolling {
          overflow: scroll;
        }
        """
        pn.config.raw_css.append(css)  # add scrolling class from css (panel GH#383, GH#384)
        pn.extension()

    except Exception as e:

        class GUI(object):
            def __repr__(self):
                raise RuntimeError("Initialisation of GUI failed, even though "
                                   "panel is installed. Please update it "
                                   "to a more recent version (`conda install -c"
                                   " conda-forge panel>=0.9.5`).")
    return GUI


class InstanceMaker(object):

    def __init__(self):
        self._instance = None

    def _instantiate(self):
        if self._instance is None:
            GUI = do_import()
            self._instance = GUI()

    def __getattr__(self, attr, *args, **kwargs):
        self._instantiate()
        return getattr(self._instance, attr, *args, **kwargs)

    def __getitem__(self, item):
        self._instantiate()
        return self._instance[item]

    def __repr__(self):
        self._instantiate()
        return repr(self._instance)

    def __dir__(self):
        self._instantiate()
        return dir(self._instance)
