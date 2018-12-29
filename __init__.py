from . import OctoPrintPlugin

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
    plugin = OctoPrintPlugin.OctoPrintExtension()
    return {
        "extension": plugin,
        "output_device": plugin
    }
