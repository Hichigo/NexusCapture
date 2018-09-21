bl_info = {
	"name": "Nexus Arduino Capture",
	"author": "Nexus Studio",
	"version": (0, 0, 1),
	"blender": (2, 79, 0),
	"location": "View 3D > Tool Shelf",
	"description": "Tools",
	"warning": "",
	"wiki_url": "",
	"category": "User"
	}

import sys
import glob
import serial
import bpy
from bpy.props import *
import bpy.utils.previews
from math import radians

arduino_data = serial.Serial()

def frameChange(passedScene):
	data = arduino_data.readline().strip()

	# rot_angle = float(data.decode())
	data = str(data.decode())
	data_YPR = [float(val) for val in data.split(',')]
	# print(data_split, type(data_split))

	bpy.context.active_object.rotation_euler = (radians(data_YPR[0]), radians(data_YPR[1]), radians(data_YPR[2]))
	#bpy.context.active_object.location.x = rot_angle


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

		arduino_data.baudrate = 115200 #9600
		arduino_data.port = arduino_prop.COM_ports

		arduino_data.open()

		print(arduino_data)
		bpy.app.handlers.scene_update_pre.append(frameChange)

		return {'FINISHED'}

class Stop_Capture(bpy.types.Operator):

	bl_idname = "capture.stop"
	bl_label = "Capture Stop"

	def execute(self, context):

		arduino_prop = context.scene.arduino_prop
		arduino_prop.captured = False
		bpy.app.handlers.scene_update_pre.remove(frameChange)
		arduino_data.close()

		return {'FINISHED'}

class CapturePanel(bpy.types.Panel):

	bl_label = "Arduino Capture"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_category = "Arduino Capture"

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
		row.operator("capture.stop", icon="MESH_PLANE", text="Stop capture")



class ArduinoCapture_Scene_prop(bpy.types.PropertyGroup):
	COM_ports = EnumProperty(
		items=enum_COMports_list
	)

	captured = BoolProperty(
		name="Captured",
		description="capture start / stop",
		default=False
	)

def register():
	bpy.utils.register_class(Start_Capture)
	bpy.utils.register_class(Stop_Capture)

	bpy.utils.register_module(__name__)

	bpy.types.Scene.arduino_prop = bpy.props.PointerProperty(type=ArduinoCapture_Scene_prop)

def unregister():
	bpy.utils.unregister_class(Start_Capture)
	bpy.utils.unregister_class(Stop_Capture)

	del bpy.types.Scene.arduino_prop

	bpy.utils.unregister_module(__name__)

if __name__ == '__main__':
	register()