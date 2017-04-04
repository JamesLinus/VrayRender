
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
import time

class V():
	
	sel_objects = []
	hide_objects = []
	buttonbool = True

def select_objects(objs):
	
	bpy.ops.object.select_all(action='DESELECT')
	for o in objs:
		o.select = True

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

	names =	 [i['attr'] for i in PLUGINS_ID[plugin_name].PluginParams ]
	types =	 [i['type'] for i in PLUGINS_ID[plugin_name].PluginParams ]
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

			exec_line =	 "''"
		elif type(data[i]) is str :

			exec_line = "'" + str(data[i]) + "'"
		else:

			exec_line =	 str(data[i])

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
		row.operator('exec.rendersettingload', text = "Load render settings, current filename: " + context.scene.rendersettingfilename, icon = 'FILESEL')
		row = layout.row()
		row.operator('exec.rendersettingsave', text = "Save render settings, current filename: " + context.scene.rendersettingfilename, icon = 'FILESEL')
			
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
		
		box = layout.box()
		row = box.row()
		row.operator('exec.renderhideobjects', icon = 'RENDER_STILL')
		row = box.row()
		row.prop(context.scene, 'Children', "Children Immediate")
		row.prop(context.scene, 'Parent', "Parent")

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
		
	def draw(self, context):
		layout = self.layout
		layout.prop(context.scene, 'rendersettingfilename', text = "filename")
		layout.separator()
		col = layout.column(align=True)
		#col.label("of this dialog box to cancel.")
	
	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)
		
class Exec_RenderSettingSave(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "exec.rendersettingsave"
	bl_label = "Render settings"
	bl_options = {'REGISTER', 'UNDO'}


	def execute(self, context):
		self.report({'INFO'}, context.scene.rendersettingfilename)
		render_settings_store(0,0)
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
	#"""Copy current render settings"""
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

#render selected objects
class Exec_RenderHideObjects(bpy.types.Operator):		
	"""Only selected objects are visible when rendering"""
	bl_idname = "exec.renderhideobjects"
	bl_label = "Render Selected objects"
	#bl_description = "Run the script in this slot."
	bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.	
	
	def execute(self, context):
		
		V.sel_objects = context.selected_objects
		for o in V.sel_objects:
			#selected object parent
			if context.scene.Parent:
				if o.parent is not None and o.parent.dupli_type is not None:
					o.parent.select = True
			if context.scene.Children:
				#select also immediate Children objects
				bpy.context.scene.objects.active = o
				bpy.ops.object.select_grouped(extend=True, type='CHILDREN')
		V.sel_objects = context.selected_objects
		#
		objs_scene = context.scene.objects
		objs_not_selected = list(set(objs_scene).symmetric_difference(V.sel_objects))




		#
		#bpy.ops.object.select_all(action='INVERT')
		V.hide_objects = []
		for o in objs_not_selected:
			if o.hide_render == False and o.type in ('MESH','CURVE','EMPTY'):
				o.hide_render = True
				V.hide_objects.append(o)

		#print ("hided objects:",V.hide_objects)	
		
		select_objects(V.sel_objects)
		V.buttonbool = not V.buttonbool
		bpy.ops.render.render()
		Exec_RenderUnHideObjects.execute(self, context)
		return {'FINISHED'}	

class Exec_RenderUnHideObjects(bpy.types.Operator):		
	"""Restore objects"""
	bl_idname = "exec.renderunhideobjects"
	bl_label = "UnHide Objects"
	
	
	def execute(self, context):
				
		for x, o in enumerate(V.hide_objects):
			o.hide_render = False
		select_objects(V.sel_objects)
		
		V.buttonbool = not V.buttonbool
			
		return {'FINISHED'}	
	
#set active camera
#bpy.context.scene.camera = bpy.context.scene.objects['Camera']

#render
#bpy.ops.render.render()

###########################################################
#Show image textures on 3d viewport
###########################################################
class Viewport(bpy.types.Operator):
	bl_idname = "viewport.set"
	bl_label = "Show textures"

	def execute(self, context):
		sce = context.scene
		create_textures(sce.Material_shadeless)
		return {'FINISHED'}

def Vray_Show_Textures(self, context):
	
	
	layout = self.layout
	row = layout.row(align=True)
	row.operator("viewport.set")
	row.prop(context.scene, "Material_shadeless", "Shadeless")

###############################################################
def outputnode_search(mat): #return node/None
	
	for node in mat.vray.ntree.nodes:
		print (mat.name, node)
		if node.bl_idname == 'VRayNodeOutputMaterial' and node.inputs[0].is_linked:
			return node

	print ("No material output node found")
	return None
			

def nodes_iterate(mat, node_type_search = False): #return image/nodeindex/None
	#node_type_search = True when searching nodetype for proxy save

	nodeoutput = outputnode_search(mat)
	if nodeoutput is None:
		return None
	#print ("Material: ",mat)

	nodelist = []
	nodelist.append(nodeoutput)
	nodecounter = 0

	while nodecounter < len(nodelist):

		basenode = nodelist[nodecounter]

		print ("basenode",basenode, mat)
		#search nodetype
		if node_type_search:
			if node_type_check(basenode.vray_plugin):
				return mat.vray.ntree.nodes.find(basenode.name)
		#search image texture
		elif hasattr(basenode, 'vray_plugin') and basenode.vray_plugin in ('TexBitmap','BitmapBuffer'):
			print ("Mat:",mat.name, "has bitmap texture")
			print ("basenode.name"	, basenode.name)

			if hasattr(basenode, 'texture'):
				if hasattr(basenode.texture, 'image'):
					image = basenode.texture.image
					print ("image=", image)
					return image

		inputlist = (i for i in basenode.inputs if i.is_linked)

		for input in inputlist:

			for nlinks in input.links:

				node = nlinks.from_node
				if node not in nodelist:
					nodelist.append(node)

		nodecounter +=1

	return None


def create_textures(shadeless):
	#print ("##################################")

	#filter out materials without nodetree
	materials = [m for m in bpy.data.materials if hasattr(m.vray.ntree, "name")]
	for mat in materials:

		image = nodes_iterate(mat)
		
		#3d viewport 
		mat.use_shadeless = shadeless
		mat.use_nodes = False
		mat.alpha = 0
		print ("Set material alpha to 0")

		#create image texture
		#print ("image:",image)
		if image:
			#print ("image is not none")
			#print (mat.name)
			#create image texture if needed
			
			if mat.name in bpy.data.textures:
				tex = bpy.data.textures[mat.name]
			else:
				tex = bpy.data.textures.new(mat.name,'IMAGE')

			tex.image = image
			tex.type = 'IMAGE'
			#mat.texture_slots.add()
			#mat.texture_slots[0].texture  = tex
			#mat.texture_slots[0].texture.type	= 'IMAGE'
			#mat.texture_slots[0].texture_coords = 'UV'
			#mat.texture_slots[0].texture.image = image
			#mat.add_texture(texture = tex, texture_coordinates = 'UV')
			mat.texture_slots.clear(0)
			mat.texture_slots.add()
			mat.texture_slots[0].texture = tex
			mat.texture_slots[0].use_map_alpha = True

###############################################################		

def register():
	
	#bpy.utils.register_module(__name__)
	
	
	bpy.types.Scene.ObjCam1 = bpy.props.StringProperty(update=ObjCam1_update)
	bpy.types.Scene.ObjCam2 = bpy.props.StringProperty(update=ObjCam2_update)
	bpy.types.Scene.ShowOptions = bpy.props.BoolProperty()
	bpy.types.Scene.UseCustomLayers = bpy.props.BoolVectorProperty(size = 2, update=use_custom_layers_update)
	bpy.types.Scene.rendersettingfilename = bpy.props.StringProperty(default = "1")
	
	bpy.types.Scene.Children = bpy.props.BoolProperty(default = True, description ='Include selected objects immediate childrens')
	bpy.types.Scene.Parent = bpy.props.BoolProperty(default = True, description ='Include parent objects if parent duplication is on')

	bpy.utils.register_class(Exec_RenderUnHideObjects)
	bpy.utils.register_class(Exec_RenderHideObjects)
	bpy.utils.register_class(Exec_RenderSettingsCopy)
	bpy.utils.register_class(Exec_CustomLayersSet)
	bpy.utils.register_class(Exec_RenderSettingsRead)
	bpy.utils.register_class(Exec_RenderSettingsStore)
	bpy.utils.register_class(Exec_SetActiveCamera)
	bpy.utils.register_class(Exec_Render)
	bpy.utils.register_class(Exec_RenderSettingSave)
	bpy.utils.register_class(Exec_RenderSettingLoad)
	bpy.utils.register_class(NodePanel)
	bpy.utils.register_class(MenuCopy)
	#bpy.utils.register_class(Exec_RenderHideObjects)
	#bpy.utils.register_class(Exec_RenderHideObjects)
	bpy.utils.register_class(Viewport)
	bpy.types.VRAY_MP_context_material.append(Vray_Show_Textures)
	bpy.types.Scene.Material_shadeless = bpy.props.BoolProperty(default=True)
	
def unregister():
	#bpy.utils.unregister_module(__name__)
	
	
	del bpy.types.Scene.Children
	del bpy.types.Scene.Parent
	
	bpy.utils.unregister_class(Exec_RenderUnHideObjects)
	bpy.utils.unregister_class(Exec_RenderHideObjects)
	bpy.utils.unregister_class(Exec_RenderSettingsCopy)
	bpy.utils.unregister_class(Exec_CustomLayersSet)
	bpy.utils.unregister_class(Exec_RenderSettingsRead)
	bpy.utils.unregister_class(Exec_RenderSettingsStore)
	bpy.utils.unregister_class(Exec_SetActiveCamera)
	bpy.utils.unregister_class(Exec_Render)
	bpy.utils.unregister_class(Exec_RenderSettingSave)
	bpy.utils.unregister_class(Exec_RenderSettingLoad)
	bpy.utils.unregister_class(NodePanel)
	bpy.utils.unregister_class(MenuCopy)
	
	bpy.utils.unregister_class(Viewport)
	bpy.types.VRAY_MP_context_material.remove(Vray_Show_Textures)
	del bpy.types.Scene.Material_shadeless
	
if __name__ == "__main__":
	register()
