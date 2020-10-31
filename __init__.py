bl_info = {
    "name": "Nexus Arduino Capture",
    "author": "Nexus Studio",
    "version": (0, 0, 1),
    "blender": (2, 90, 1),
    "location": "View 3D > Tool Shelf",
    "description": "Tools",
    "warning": "",
    "wiki_url": "",
    "category": "User"
    }

import re
import sys
import glob
import time
import serial
import threading

import bpy
from bpy.props import EnumProperty, BoolProperty
import bpy.utils.previews
from math import radians

arduino = serial.Serial()

class RotateCubeThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def get_serial_data(self):
        data = arduino.readline()[:-2] #the last bit gets rid of the new-line chars
        if data == b'0' or data == b'':
            data = b"0|0|0|0|0|0"
        try:
            data = data.decode("utf-8").split("|")

        except:
            print("Value error!!!")
        if data:
            result = []
            for item in data:
                result.append(int(item))

        return result

    def run(self):
        FPS = 1
        # arduino_prop = bpy.context.scene.arduino_prop.captured

        tick = time.time()
        loop = 0
        x = 0
        cube = bpy.data.objects["Cube"]

        while bpy.context.scene.arduino_prop.captured is True:
            # ax, ay, az, gx, gy, gz
            transform = self.get_serial_data()
            # cube.rotation_mode = 'XYZ'
            # cube.rotation_euler = (transform[3]/2000, transform[4]/2000, transform[5] /2000)
            print(transform)

            if not transform:
                print("buffer")
            else:
                #knob.rotation_euler = ( rotation_degrees[0] * 0.00875, rotation_degrees[1] * 0.00875, rotation_degrees[2] * 0.00875)
                # cube.location.y += 0
                pass
            tick = time.time()

            loop += 1
            x += 1

def enum_COMports_list(self, context):
    ports = serial_ports()
    list_ports = []

    for i, port in enumerate(ports):
        item = (port, port, '', i)
        list_ports.append(item)

    return list_ports

def serial_ports():
    """ return lists serial port names """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

class Start_Capture(bpy.types.Operator):

    bl_idname = "capture.start"
    bl_label = "Capture Start"

    def execute(self, context):

        arduino_prop = context.scene.arduino_prop

        arduino_prop.captured = True

        arduino.baudrate = 9600 #115200
        arduino.port = arduino_prop.COM_ports

        arduino.open()

        print(arduino)
        #Make thread
        thread = RotateCubeThread(1, "thread")
        thread.start()

        return {'FINISHED'}

class Stop_Capture(bpy.types.Operator):

    bl_idname = "capture.stop"
    bl_label = "Capture Stop"

    def execute(self, context):

        arduino_prop = context.scene.arduino_prop
        arduino_prop.captured = False
        arduino.close()

        return {'FINISHED'}

class CapturePanel(bpy.types.Panel):
    """ Arduino capture panel """

    bl_label = "Arduino Capture"
    bl_idname = "VIEW3D_PT_CapturePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Nexus"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout

        arduino_prop = context.scene.arduino_prop

        col = layout.column()
        col.label(text="COM ports")
        col.prop(arduino_prop, "COM_ports", text="")

        col = layout.column()

        row = col.row(align=True)
        row.enabled = not arduino_prop.captured
        row.operator("capture.start", icon="PLAY", text="Start capture")
        row = col.row(align=True)
        row.enabled = arduino_prop.captured
        row.operator("capture.stop", icon="CANCEL", text="Stop capture")



class ArduinoCaptureProp(bpy.types.PropertyGroup):
    COM_ports: EnumProperty(
        items=enum_COMports_list
    )
    captured: BoolProperty(
        name="Captured",
        description="capture start / stop",
        default=False
    )

classes = (
    ArduinoCaptureProp,
    Start_Capture,
    Stop_Capture,
    CapturePanel
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.arduino_prop = bpy.props.PointerProperty(type=ArduinoCaptureProp)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.arduino_prop

if __name__ == '__main__':
    register()
