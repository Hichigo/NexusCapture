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
from math import acos, radians
from mathutils import Vector, Matrix

import bpy
from bpy.props import EnumProperty, BoolProperty


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
        else:
            data = data.decode("utf-8").split("|")

        if data:
            result = []
            for item in data:
                result.append(int(item))

        return result

    def to_rad(self, val):
        ay = val / 16384.0
        ay = max(min(ay, 1.0), -1.0)

        if ay >= 0:
            angle = 90 - 57.29577951308232087679815481410517033*acos(ay)
        else:
            angle = 57.29577951308232087679815481410517033*acos(-ay) - 90

        return radians(angle)# * 3.1415 / 180

    def to_location(self, val):
        pass


    def run(self):
        bpy.context.scene.capture_object.rotation_mode = 'XYZ'

        while bpy.context.scene.arduino_prop.captured is True:
            time.sleep(.1)
            # ax, ay, az, gx, gy, gz
            # попробовать вычислять разницу между углом объекта и этими данными (gx, gy, gz)
            transform = self.get_serial_data()

            angle_ax = self.to_rad(transform[0])
            angle_ay = self.to_rad(transform[1])
            angle_az = self.to_rad(transform[2])

            # x = self.to_rad(transform[3])

            if not transform:
                print("buffer")
            else:
                print(transform[2])
                cube = bpy.context.scene.capture_object
                loc, rot, scale = cube.matrix_world.decompose()

                loc = Matrix.Translation(cube.location)

                scale_mat = Matrix.Scale(1, 4)
                scale_mat[0][0] = scale.x
                scale_mat[1][1] = scale.y
                scale_mat[2][2] = scale.z

                normal_hit = Vector((angle_ax, angle_ay, angle_az)).normalized()


                rot_by_normal = normal_hit.rotation_difference(Vector((0,0,1)))
                rot_by_normal.invert()
                rot_by_normal = rot_by_normal.to_euler().to_matrix().to_4x4()

                rot = rot_by_normal

                mat_w = loc @ rot @ scale_mat

                cube.matrix_world = mat_w
                # bpy.context.scene.capture_object.rotation_euler = Vector((angle_ax, angle_ay, angle_az))

                # bpy.context.scene.capture_object.location.x += x

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

class StartCapture(bpy.types.Operator):
    """ Operator start capture """
    bl_idname = "capture.start"
    bl_label = "Capture Start"

    def execute(self, context):

        arduino_prop = context.scene.arduino_prop

        arduino_prop.captured = True

        arduino.baudrate = 115200#9600
        arduino.port = arduino_prop.COM_ports

        arduino.open()

        print(arduino)
        #Make thread
        thread = RotateCubeThread(1, "thread")
        thread.start()

        return {'FINISHED'}

class StopCapture(bpy.types.Operator):
    """ Operator stop capture """
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
        col.prop(context.scene, "capture_object", text="")

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
    StartCapture,
    StopCapture,
    CapturePanel,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.arduino_prop = bpy.props.PointerProperty(type=ArduinoCaptureProp)
    bpy.types.Scene.capture_object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        # poll=scene_mychosenobject_poll
    )

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.arduino_prop
    del bpy.types.Scene.capture_object

if __name__ == '__main__':
    register()
