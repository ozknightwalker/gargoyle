"""
Gargoyle
~~~~~~~~
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('gargoyle').version
except Exception, e:
    VERSION = 'unknown'

from gargoyle.models import SwitchManager, Switch
from gargoyle.conditions import ConditionSet

from django.utils.importlib import import_module

import imp

__all__ = ('gargoyle', 'ConditionSet', 'autodiscover')

# A flag to tell us if autodiscover is running.  autodiscover will set this to
# True while running, and False when it finishes.
LOADING = False

gargoyle = SwitchManager(Switch, key='key', value='value', instances=True, auto_create=True)

def autodiscover():
    """
    Auto-discover INSTALLED_APPS gargoyle.py modules and fail silently when
    not present. This forces an import on them to register any api bits they
    may want.
    """

    # Bail out if autodiscover didn't finish loading from a previous call so
    # that we avoid running autodiscover again when the URLconf is loaded by
    # the exception handler to resolve the handler500 view.  This prevents an
    # admin.py module with errors from re-registering models and raising a
    # spurious AlreadyRegistered exception (see #8245).
    global LOADING
    if LOADING:
        return
    LOADING = True

    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an api.py inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for admin.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own admin registration.
        try:
            app_path = import_module(app).__path__
        except (AttributeError, ImportError):
            continue

        # Step 2: use imp.find_module to find the app's admin.py. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its admin.py doesn't exist
        try:
            imp.find_module('gargoyle', app_path)
        except ImportError:
            continue
        
        import_module("%s.gargoyle" % app)

    # load builtins
    import gargoyle.builtins

    # autodiscover was successful, reset loading flag.
    LOADING = False
