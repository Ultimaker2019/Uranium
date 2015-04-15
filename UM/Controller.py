from UM.InputDevice import InputDevice
from UM.View.View import View
from UM.Tool import Tool
from UM.Scene.Scene import Scene
from UM.Event import Event, MouseEvent, ToolEvent
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Signal import Signal, SignalEmitter
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry

import math

## Glue glass that holds the scene, (active) view(s), (active) tool(s) and possible user inputs.
#
#  The different types of views / tools / inputs are defined by plugins.
class Controller(SignalEmitter):
    def __init__(self, application):
        super().__init__() # Call super to make multiple inheritence work.
        self._active_tool = None
        self._tools = {}

        self._input_devices = {}

        self._active_view = None
        self._views = {}
        self._scene = Scene()
        self._application = application
        self._camera_tool = None
        self._selection_tool = None

        PluginRegistry.addType('view', self.addView)
        PluginRegistry.addType('tool', self.addTool)
        PluginRegistry.addType('input_device', self.addInputDevice)

    ##  Get the application.
    #   \returns Application
    def getApplication(self):
        return self._application

    ##  Add a view by name if it's not already added.
    #   \param name Unique identifier of view (usually the plugin name)
    #   \param view The view to be added
    def addView(self, view):
        name = view.getPluginId()
        if name not in self._views:
            self._views[name] = view
            view.setController(self)
            view.setRenderer(self._application.getRenderer())
            self.viewsChanged.emit()
        else:
            Logger.log('w', '%s was already added to view list. Unable to add it again.',name)

    ##  Request view by name. Returns None if no view is found.
    #   \param name Unique identifier of view (usually the plugin name)
    #   \return View if name was found, none otherwise.
    def getView(self, name):
        try:
            return self._views[name]
        except KeyError: #No such view  
            Logger.log('e', "Unable to find %s in view list",name)
            return None

    ##  Return all views.
    def getAllViews(self):
        return self._views

    ## Request active view. Returns None if there is no active view
    #  \return Tool if an view is active, None otherwise.
    def getActiveView(self):
        return self._active_view

    ##  Set the currently active view.
    #   \parma name The name of the view to set as active
    def setActiveView(self, name):
        try:
            self._active_view = self._views[name]
            self.activeViewChanged.emit()
        except KeyError:
            Logger.log('e', "No view named %s found", name)

    ##  Emitted when the list of views changes.
    viewsChanged = Signal()

    ##  Emitted when the active view changes.
    activeViewChanged = Signal()
        
    ##  Add an input device (eg; mouse, keyboard, etc) by name if it's not already addded.
    #   \param name Unique identifier of device (usually the plugin name)
    #   \param view The input device to be added
    def addInputDevice(self, device):
        name = device.getPluginId()
        if(name not in self._input_devices):
            self._input_devices[name] = device
            device.event.connect(self.event)
        else:
            Logger.log('w', '%s was already added to input device list. Unable to add it again.', name)

    ##  Request input device by name. Returns None if no device is found.
    #   \param name Unique identifier of input device (usually the plugin name)
    #   \return input device if name was found, none otherwise.
    def getInputDevice(self, name):
        try:
            return self._input_devices[name]
        except KeyError: #No such tool
            Logger.log('e', "Unable to find %s in input devices",name)
            return None

    ##  Remove an input device from the list of input devices.
    #   Does nothing if the input device is not in the list.
    #   \param name The name of the device to remove.
    def removeInputDevice(self, name):
        if name in self._input_devices:
            self._input_devices[name].event.disconnect(self.event)
            del self._input_devices[name]

    ##  Request tool by name. Returns None if no view is found.
    #   \param name Unique identifier of tool (usually the plugin name)
    #   \return tool if name was found, none otherwise.
    def getTool(self, name):
        try:
            return self._tools[name]
        except KeyError: #No such tool
            Logger.log('e', "Unable to find %s in tools",name)
            return None

    def getAllTools(self):
        return self._tools

    ##  Add an Tool (transform object, translate object) by name if it's not already addded.
    #   \param name Unique identifier of tool (usually the plugin name)
    #   \param tool Tool to be added
    #   \return Tool if name was found, None otherwise.    
    def addTool(self, tool):
        name = tool.getPluginId()
        if(name not in self._tools):
            self._tools[name] = tool
            tool.setController(self)
            self.toolsChanged.emit()
        else: 
            Logger.log('w', '%s was already added to tool list. Unable to add it again.', name)

    ## Request active tool. Returns None if there is no active tool
    #  \return Tool if an tool is active, None otherwise.
    def getActiveTool(self):
        return self._active_tool

    ##  Set the current active tool.
    #   \param name The name of the tool to set as active.
    def setActiveTool(self, name):
        try:
            if self._active_tool:
                self._active_tool.event(ToolEvent(ToolEvent.ToolDeactivateEvent))

            if name:
                self._active_tool = self._tools[name]
            else:
                self._active_tool = None

            if self._active_tool:
                self._active_tool.event(ToolEvent(ToolEvent.ToolActivateEvent))

            self.activeToolChanged.emit()
        except KeyError:
            Logger.log('e', 'No tool named %s found.', name)

    ##  Emitted when the list of tools changes.
    toolsChanged = Signal()

    ##  Emitted when the active tool changes.
    activeToolChanged = Signal()

    ##  Return the scene
    def getScene(self):
        return self._scene

    ## Process an event
    def event(self, event):
        # First, try to perform camera control
        if self._camera_tool and self._camera_tool.event(event):
            return

        # If we are not doing camera control, pass the event to the active tool.
        if self._active_tool and self._active_tool.event(event):
            return

        if self._selection_tool and self._selection_tool.event(event):
            return

        if event.type == Event.MouseReleaseEvent and MouseEvent.RightButton in event.buttons:
            self.contextMenuRequested.emit(event.x, event.y)

    contextMenuRequested = Signal()

    ##  Set the tool used for handling camera controls
    #   Camera tool is the first tool to recieve events
    def setCameraTool(self, tool):
        self._camera_tool = self.getTool(tool)

    ##  Set the tool used for performing selections
    #   Selection tool recieves its events after camera tool and active tool
    def setSelectionTool(self, tool):
        self._selection_tool = self.getTool(tool)
