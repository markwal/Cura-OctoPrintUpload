# OctoPrintOutputDevice

import os.path
from io import StringIO
from time import time

from PyQt5 import QtNetwork
from PyQt5.QtCore import QFile, QUrl, QCoreApplication
from PyQt5.QtGui import QDesktopServices

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


from enum import Enum
class OutputStage(Enum):
    ready = 0
    writing = 1
    uploading = 2


class OctoPrintOutputDevice(OutputDevice):
    def __init__(self, name="OctoPrint", host="http://octopi.local", apiKey=""):
        super().__init__(name)

        self.setName(name)
        description = catalog.i18nc("@action:button", "Save to {0} ({1})").format(name, host)
        self.setShortDescription(description)
        self.setDescription(description)

        self._stage = OutputStage.ready
        self._host = host
        self._apiKey = apiKey

        self._qnam = QtNetwork.QNetworkAccessManager()
        self._qnam.authenticationRequired.connect(self._onAuthRequired)
        self._qnam.sslErrors.connect(self._onSslErrors)
        self._qnam.finished.connect(self._onNetworkFinished)

        self._stream = None
        self._cleanupRequest()

    def requestWrite(self, node, fileName = None, *args, **kwargs):
        if self._stage != OutputStage.ready:
            raise OutputDeviceError.DeviceBusyError()

        if fileName:
            fileName = os.path.splitext(fileName)[0] + '.gcode'
        else:
            fileName = "%s.gcode" % Application.getInstance().getPrintInformation().jobName
        self._fileName = fileName

        # create the temp file for the gcode
        self._stream = StringIO()
        self._stage = OutputStage.writing
        self.writeStarted.emit(self)

        # show a progress message
        message = Message(catalog.i18nc("@info:progress", "Saving to <filename>{0}</filename>").format(self.getName()), 0, False, -1)
        message.show()
        self._message = message

        # find the G-code for the active build plate to print
        active_build_plate_id = Application.getInstance().getBuildPlateModel().activeBuildPlate
        gcode_dict = getattr(Application.getInstance().getController().getScene(), "gcode_dict")
        gcode = gcode_dict[active_build_plate_id]

        # send all the gcode to self._stream
        lines = len(gcode)
        nextYield = time() + 0.05
        i = 0
        for line in gcode:
            i += 1
            self._stream.write(line)
            if time() > nextYield:
                self._onProgress(i / lines)
                QCoreApplication.processEvents()
                nextYield = time() + 0.05

        # self._stream now contains the gcode, now upload it
        self._stage = OutputStage.uploading
        self._stream.seek(0)

        # set up a multi-part post
        self._multipart = QtNetwork.QHttpMultiPart(QtNetwork.QHttpMultiPart.FormDataType)

        # add the form variables
        formvalues = {'select': 'false', 'print': 'false'}
        for key, value in formvalues.items():
            part = QtNetwork.QHttpPart()
            part.setHeader(QtNetwork.QNetworkRequest.ContentDispositionHeader,
                    'form-data; name="%s"' % key)
            part.setBody(value.encode())
            self._multipart.append(part)

        # add the file part
        part = QtNetwork.QHttpPart()
        part.setHeader(QtNetwork.QNetworkRequest.ContentDispositionHeader,
                'form-data; name="file"; filename="%s"' % fileName)
        part.setBody(self._stream.getvalue().encode())
        self._multipart.append(part)

        # send the post
        self._request = QtNetwork.QNetworkRequest(QUrl(self._host + "/api/files/local"))
        self._request.setRawHeader('User-agent'.encode(), 'Cura OctoPrintOutputDevice Plugin'.encode())
        self._request.setRawHeader('X-Api-Key'.encode(), self._apiKey.encode())
        self._reply = self._qnam.post(self._request, self._multipart)

        # connect the reply signals
        self._reply.error.connect(self._onNetworkError)
        self._reply.uploadProgress.connect(self._onUploadProgress)
        self._reply.downloadProgress.connect(self._onDownloadProgress)

    def _onProgress(self, progress):
        progress = (50 if self._stage == OutputStage.uploading else 0) + (progress / 2)
        if self._message:
            self._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _cleanupRequest(self):
        self._reply = None
        self._request = None
        self._multipart = None
        self._body_part = None
        if self._stream:
            self._stream.close()
        self._stream = None
        self._stage = OutputStage.ready
        self._fileName = None

    def _onNetworkFinished(self, reply):
        Logger.log("i", "_onNetworkFinished reply: %s", repr(reply.readAll()))
        Logger.log("i", "_onNetworkFinished reply.error(): %s", repr(reply.error()))

        self._stage = OutputStage.ready
        if self._message:
            self._message.hide()
        self._message = None

        self.writeFinished.emit(self)
        if reply.error():
            message = Message(catalog.i18nc("@info:status", "Could not save to {0}: {1}").format(self.getName(), str(reply.errorString())))
            message.show()
            self.writeError.emit(self)
        else:
            message = Message(catalog.i18nc("@info:status", "Saved to {0} as {1}").format(self.getName(), os.path.basename(self._fileName)))
            message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to OctoPrint."))
            message.actionTriggered.connect(self._onMessageActionTriggered)
            message.show()
            self.writeSuccess.emit(self)
        self._cleanupRequest()

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl(self._host))

    def _onAuthRequired(self, authenticator):
        Logger.log("e", "Not yet implemented: OctoPrint authentication other than api-key")

    def _onSslErrors(self, reply, errors):
        Logger.log("e", "Ssl errors: %s", repr(errors))

        errorString = ", ".join([str(error.errorString()) for error in errors])
        message = Message(catalog.i18nc("@info:status", "One or more SSL errors has occurred: {0}").format(errorString))
        message.show()

    def _onUploadProgress(self, bytesSent, bytesTotal):
        if bytesTotal > 0:
            self._onProgress(int(bytesSent * 100 / bytesTotal))

    def _onDownloadProgress(self, bytesReceived, bytesTotal):
        pass

    def _onNetworkError(self, errorCode):
        Logger.log("e", "_onNetworkError: %s", repr(errorCode))
        if self._message:
            self._message.hide()
        self._message = None
        message = Message(catalog.i18nc("@info:status", "There was a network error: {0}").format(errorCode))
        message.show()

    def _cancelUpload(self):
        if self._message:
            self._message.hide()
        self._message = None
        self._reply.abort()
