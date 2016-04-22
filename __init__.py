
bl_info = {
	"name": "Vray Render",
	"author": "JuhaW",
	"version": (1, 0, 0),
	"blender": (2, 76, 0),
	"location": "Tools",
	"description": "Store 2 render settings: Render dimensions and GI/DMC",
	"warning": "beta",
	"wiki_url": "",
	"category": "",
}


import sys
import bpy
from bpy.props import IntProperty, BoolProperty, BoolVectorProperty, StringProperty
import json
import os
from vb30.plugins import PLUGINS_ID



def render_settings_store(oldindex, currentindex):

	index = oldindex
	if oldindex == currentindex:
		index = currentindex

	#print ("stored cam:", index)
	#gi
	presets("save", index)
	#dmc
	dmc_import_export("save", index)
	

#DMC import/export

def dmc_import_export(loadsave, index):
	
	fname = bpy.context.scene.rendersettingfilename
	filename1 = fname + str(index) + "_DMCIS"
	plugin_name1 = 'SettingsImageSampler'
	filename2 = fname + str(index) + "_DMCSampler"
	plugin_name2 = 'SettingsDMCSampler'
	
	if loadsave == "load":
		io_import(filename1, plugin_name1)	
		io_import(filename2, plugin_name2)
	else:
		io_export(filename1, plugin_name1)	
		io_export(filename2, plugin_name2)	
	
	
def config_path_get():
	
	user_path = bpy.utils.resource_path('USER')
	config_path = os.path.join(user_path, "config")
	return config_path + "\\"

	
def plugin_get(plugin_name):

	names =  [i['attr'] for i in PLUGINS_ID[plugin_name].PluginParams ]
	types =  [i['type'] for i in PLUGINS_ID[plugin_name].PluginParams ]
	return names, types

	
def io_import(fname, dmc):
	
	items, types = plugin_get(dmc)
	dmc = 'bpy.context.scene.vray.' + dmc
	directory = config_path_get() + "vrayblender\\presets\\gi"
	
	full_path = os.path.join(directory, fname  + '.json')
	if os.path.isfile(full_path) == False:
		return None
	#print ("import json")
	try:
		with open(full_path, encoding='utf-8') as ofile:
			data = json.loads(ofile.read())
	except:
		print ("exception")

	for i in data:

		if data[i] == "":

			exec_line =  "''"
		elif type(data[i]) is str :

			exec_line = "'" + str(data[i]) + "'"
		else:

			exec_line =  str(data[i])

		setattr(eval(dmc),exec_line,0)


def io_export(filename, dmc):
	
	items, types = plugin_get(dmc)
	dmc = 'bpy.context.scene.vray.' + dmc
	directory = config_path_get() + "vrayblender\\presets\\gi"
	full_path = os.path.join(directory, filename + '.json')

	with open(full_path, 'w') as ofile:
		
		my_dict = {}

		for x,i in enumerate(items):

			setattr(eval(dmc), i, eval(dmc+'.'+i))

		for x, i in enumerate(items):
			
			value = eval(dmc + "." + str(i))
			if types[x] in('STRING','ENUM'):
				value = str(value)
			my_dict[str(i)] = value

		m = json.dumps(my_dict, sort_keys=True, ensure_ascii=False,indent = 4)
		ofile.write(m)

#-----------------------------------------------------------

#GI import/export
def presets(loadsave, renderindex):

	fname = bpy.context.scene.rendersettingfilename
	preset_name = fname + "_" + str(renderindex) + "_GI"
	if loadsave == "load":

		#Read Global illumination preset
		user_path = bpy.utils.resource_path('USER')
		config_path = os.path.join(user_path, "config")
		
		filepath= config_path + "\\vrayblender\\presets\\gi\\"
		filepath = filepath + preset_name + ".vrscene"

		#file exists ?
		if not os.path.isfile(filepath):
			print ("GI import/export error:")
			presets('save', renderindex)
			return

		bpy.ops.vray.preset_apply(menu_idname="VRayPresetMenuGI", filepath = filepath)

		#Read render dimension presets
		filepath= user_path + "\\scripts\\presets\\render\\"
		filepath = filepath + preset_name + ".py"
		bpy.ops.script.execute_preset(filepath = filepath, menu_idname="RENDER_MT_presets")

	else:
	
		#Save Global illumination preset
		bpy.ops.vray.preset_add_gi(name = preset_name)

		#Save render dimension presets
		bpy.ops.render.preset_add(name=preset_name)

	
def ObjCam1_update(self, context):
	
	context.scene.camera = bpy.context.scene.objects[self.ObjCam1]

def ObjCam2_update(self, context):

	context.scene.camera = bpy.context.scene.objects[self.ObjCam2]

def Set_Active_Camera(context,renderindex):
	#set active camera
	cam_name = context.scene.ObjCam1
	if renderindex == 2:
		cam_name = context.scene.ObjCam2
	context.scene.camera = bpy.context.scene.objects[cam_name]	
	
	#bpy.ops.view3d.viewnumpad(type='CAMERA')
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			area.spaces[0].region_3d.view_perspective = 'CAMERA'
	#print ("renderindex:",renderindex)

def Set_Layers(context, bool):	
	if not bool:
		bpy.context.scene.vray.Exporter.activeLayers = 'ACTIVE'
	else:
		bpy.context.scene.vray.Exporter.activeLayers = 'CUSTOM'

class MenuCopy(bpy.types.Menu):
	bl_idname = "menu.copy"
	bl_label = "Copy"
	
	print ("NodePanel Init")
	
	def draw(self, context):
		
		layout = self.layout
		row = layout.row()
		col = layout.column
		for i in range(1,3):
			menu = row.operator('exec.rendersettingscopy', text = "Copy current render settings to Cam" +str(i), icon = 'VRAY_LOGO')
			menu.index = i
			row = layout.row()
		row.operator('exec.rendersettingload', text = "Load render settings, filename: " + context.scene.rendersettingfilename, icon = 'FILESEL')
		row = layout.row()
		row.operator('exec.rendersettingfilename', text = "Set Filename of render settings", icon = 'FILESEL')
			
class NodePanel(bpy.types.Panel):
	bl_label = "Vray Render"
	bl_space_type = 'VIEW_3D'
	bl_region_type = "TOOLS"
	#bl_category = "Trees"
	
	renderindex = bpy.props.IntProperty()
	renderindex = 1
	#init 2d array 2,5 to store visible layers
	layers = [[False]*20 for i in range(2)]
	
	print ("NodePanel Init")
	
	def draw(self, context):
		
		layout = self.layout
		row = layout.row()
		col = layout.column
		#row = layout.row(align=True)

		for i in range (1,3):
			#row.alignment = 'LEFT'
			#row.label("", icon = 'RADIOBUT_ON' if NodePanel.renderindex ==i else 'RADIOBUT_OFF')

			row.prop_search(bpy.context.scene, "ObjCam"+str(i), bpy.context.scene, "objects", text ='', icon = 'CAMERA_DATA')  #, text ="Cam"+str(i))
			
			render = row.operator('exec.render', text = "",icon ='RENDER_STILL')
			render.renderindex = i
			render = row.operator('exec.setactivecamera', text = "", icon = 'REC'  if NodePanel.renderindex ==i else 'RADIOBUT_OFF')
			render.renderindex = i
			row = layout.row()
			
		
		VRayScene = context.scene.vray
		VRayExporter = VRayScene.Exporter
			
		#row.operator('exec.rendersettingsstore', text = "Store render settings Cam" + str(NodePanel.renderindex), icon = 'REC')

		row = layout.row()
		row.prop(context.scene, 'UseCustomLayers', index = NodePanel.renderindex-1, text = "Use custom layers")
		row.menu("menu.copy", icon='DOWNARROW_HLT', text="")
		
		split= layout.split()
		col= split.column()
		if context.scene.UseCustomLayers[NodePanel.renderindex-1]:
			col.prop(VRayExporter, 'customRenderLayers', text="")
			col.operator('exec.customlayersset', icon = 'TRIA_UP')
		#row.operator('exec.rendersettingsread', icon = 'HAND')
		#row = layout.row()
		'''
		row.prop(context.scene,'ShowOptions', text = "Show Options")
		if context.scene.ShowOptions:
			for i in range (1,3):
				row = layout.row()
				button = row.operator('exec.rendersettingscopy', text = "Copy current render settings to Cam" +str(i), icon = 'VRAY_LOGO')
				button.index = i
		'''
		#row.operator('exec.rendersettingsstore', text = "" , icon = 'DOWNARROW_HLT')
		
		#DOWNARROW_HLT

class Exec_RenderSettingLoad(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "exec.rendersettingload"
	bl_label = "Render settings"
	bl_options = {'REGISTER', 'UNDO'}


	def execute(self, context):
		
		#gi
		presets("load", str(NodePanel.renderindex))	
		#dmc
		dmc_import_export("load", NodePanel.renderindex)
		self.report({'INFO'}, "Settings loaded: " + context.scene.rendersettingfilename)
		return {'FINISHED'}

	
		
class Exec_RenderSettingFilename(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "exec.rendersettingfilename"
	bl_label = "Render settings"
	bl_options = {'REGISTER', 'UNDO'}


	def execute(self, context):
		self.report({'INFO'}, context.scene.rendersettingfilename)
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		layout.prop(context.scene, 'rendersettingfilename', text = "filename")
		layout.separator()
		col = layout.column(align=True)
		#col.label("of this dialog box to cancel.")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)


class Exec_Render(bpy.types.Operator):		
	"""Render and set camera view with current Render Dimensions/GI/DMC settings"""
	bl_idname = "exec.render"
	bl_label = "Render"
	
	renderindex = bpy.props.IntProperty()
	
	
	print ("exec_render operator init")
	
	
	def execute(self, context):
		
		print ("Render index:",self.renderindex)
		print ("self:",self)
		
		Set_Layers(context, context.scene.UseCustomLayers[NodePanel.renderindex-1])
		Set_Active_Camera(context,self.renderindex)
		
		#gi
		presets("load", str(NodePanel.renderindex))	
		#dmc
		dmc_import_export("load" , self.renderindex)
		
		bpy.ops.render.render()
		
		return {'FINISHED'}
	

class Exec_SetActiveCamera(bpy.types.Operator):		
	"""Set camera view and read Render Dimensions/GI/DMC settings"""
	bl_idname = "exec.setactivecamera"
	bl_label = "Active camera"
	
	renderindex = bpy.props.IntProperty()
	def execute(self, context):
		
		#oldindex, currentindex
		render_settings_store(NodePanel.renderindex, self.renderindex)

		index = self.renderindex
		if NodePanel.renderindex == self.renderindex:
			index = NodePanel.renderindex
		# layers
		NodePanel.layers[NodePanel.renderindex - 1] = context.scene.vray.Exporter.customRenderLayers[:]

		Set_Layers(context, context.scene.UseCustomLayers[NodePanel.renderindex-1])
		Set_Active_Camera(context,self.renderindex)
		NodePanel.renderindex = self.renderindex

		#gi
		presets("load", str(NodePanel.renderindex))	
		#dmc
		dmc_import_export("load", NodePanel.renderindex)
		#print ("layers before active camera:")
		#print ("set1 layer is:", NodePanel.layers[0][:])
		#print ("set2 layer is:", NodePanel.layers[1][:])
		
		#layers
		context.scene.vray.Exporter.customRenderLayers = NodePanel.layers[self.renderindex-1][:]
		#print ("renderindex:",NodePanel.renderindex)
		#print ("layers after active camera:")
		#print ("set1 layer is:", NodePanel.layers[0][:])
		#print ("set2 layer is:", NodePanel.layers[1][:])
		
		#print ("Exec_Render.var:", Exec_Render.renderindex)
		#print (self.renderindex)
		return {'FINISHED'}


class Exec_RenderSettingsStore(bpy.types.Operator):		
	"""Store render resolution/GI/DMC settings of current camera"""
	bl_idname = "exec.rendersettingsstore"
	bl_label = "Store render settings"
	
	def execute(self, context):
	
	#store all render settings, render dimensions, gi, dmc
		render_settings_store()
		
		#layers
		NodePanel.layers[NodePanel.renderindex-1] = context.scene.vray.Exporter.customRenderLayers[:]
		
		return {'FINISHED'}		

class Exec_RenderSettingsRead(bpy.types.Operator):		
	"""Create an empty object at the location and rotation of the selected objects"""
	bl_idname = "exec.rendersettingsread"
	bl_label = "Read render settings"
	
	#renderindex = bpy.props.IntProperty()
	def execute(self, context):
		
		#self.R[0].resolution_percentage = bpy.context.scene.render.resolution_percentage
		
		print (Exec_RenderSettingsStore.R[0].resolution_percentage)
		
		return {'FINISHED'}		


class Exec_CustomLayersSet(bpy.types.Operator):		
	"""Set current visible layers to custom layers"""
	bl_idname = "exec.customlayersset"
	bl_label = "Set current visible layers"
	
	
	def execute(self, context):
		
		context.scene.vray.Exporter.customRenderLayers = context.scene.layers
		
		return {'FINISHED'}		
		
class Exec_RenderSettingsCopy(bpy.types.Operator):		
	"""Copy current render settings"""
	bl_idname = "exec.rendersettingscopy"
	bl_label = "Copy current settings to Cam"
	
	index = bpy.props.IntProperty()
	
	def execute(self, context):
		
		#gi
		presets("save", str(self.index))	
		#dmc
		dmc_import_export("save", self.index)
		
		return {'FINISHED'}		

def use_custom_layers_update(self, context):
	
	Set_Layers(context, context.scene.UseCustomLayers[NodePanel.renderindex-1])
	
	pass		
	
#set active camera
#bpy.context.scene.camera = bpy.context.scene.objects['Camera']

#render
#bpy.ops.render.render()


def register():
	
	bpy.utils.register_module(__name__)
		
	bpy.types.Scene.ObjCam1 = bpy.props.StringProperty(update=ObjCam1_update)
	bpy.types.Scene.ObjCam2 = bpy.props.StringProperty(update=ObjCam2_update)
	bpy.types.Scene.ShowOptions = bpy.props.BoolProperty()
	bpy.types.Scene.UseCustomLayers = bpy.props.BoolVectorProperty(size = 2, update=use_custom_layers_update)
	bpy.types.Scene.rendersettingfilename = bpy.props.StringProperty(default = "1")
	

def unregister():
	bpy.utils.unregister_module(__name__)
	

if __name__ == "__main__":
	register()
