# Cura-OctoPrintUpload
Plugin for Cura 2.3.1 that adds a Save to OctoPrint button that allows upload to OctoPrint in one step.

## Cura Compatibility
This plugin has been tested with Cura 2.3.1 and appears to mostly work. Cura development doesn't try very hard to maintain compatibility with any third party plugin (let alone with its own plugins), so this will likely break on the next release of Cura.

Also, this plugin is still using an already deprecated (created and deprecated before the first official release of Cura 2.3) way of storing its settings, so at some point in the future we'll probably have to re-enter the OctoPrint server name and API key when the plugin is updated to use the new settings stack.

## Other OctoPrint related plugins for Cura
Aldo Hoeben also has an [OctoPrint plugin](https://github.com/fieldOfView/OctoPrintPlugin) that uploads and prints and also monitors the print in Cura, but if all you want to do is upload and monitor the print using OctoPrint's UI then this (Cura-OctoPrintUpload) is the plugin for you.

## Installation

With Cura not running, unpack the zip file from the [release](https://github.com/markwal/Cura-OctoPrintUpload/releases/latest) to this specific folder:

### Windows
C:\\Users\\[YourLoginNameHere]\\AppData\\Local\\cura\\plugins\\Cura-OctoPrintUpload

### Mac
~/Library/Application Support/Cura/plugins/Cura-OctoPrintUpload

Be careful, the unzipper often tacks on the name of the zip as a folder at the bottom and you don't want it nested.  You want the files to show up in that folder.

## Running from source
Alternatively you can run from the source directly. It'll make it easy to update in the future. Use git to clone this repository into the folders given above.

## Configuration
Boot up Cura, choose the following from the Menu Bar: Extensions->OctoPrint->Servers.  Click "Add" and tell it the url to your OctoPrint instance (i.e. http://octo.local) and give it the API key from OctoPrint (it's in Settings->API).

## Use
After you load up a model and it has sliced, click the down arrow button on the "Save to File" button on the lower right hand corner.  Choose "Save to OctoPrint" and then click the "Save to OctoPrint" button.

After the save completes successfully, a little popup will show up at the bottom with a button that will pop open a browser pointing to OctoPrint so you can print and monitor.
