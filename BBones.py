# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "BBones",
    "author": "Fork by Dziban, Based on the work by Alfonso Annarumma",
    "version": (1, 1, 2),
    "blender": (2, 80, 0),
    "location": "Header > Show Tools Settings > BBones",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "wiki_url": "",
    "category": "Sculpt",
}

import bpy
import bmesh
import math
import mathutils
from bpy.types import Menu, Panel, UIList, PropertyGroup, Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        IntProperty,
        CollectionProperty,
        BoolVectorProperty,
        FloatVectorProperty,
        PointerProperty,
        EnumProperty,
        )

def cone_between(x1, y1, z1, x2, y2, z2, r1,r2):
    
  dx = x2 - x1
  dy = y2 - y1
  dz = z2 - z1    
  dist = math.sqrt(dx**2 + dy**2 + dz**2)

  bpy.ops.mesh.primitive_cone_add(
      radius1 = r1, 
      radius2 = r2, 
      depth = dist,
      location = (dx/2 + x1, dy/2 + y1, dz/2 + z1)   
  ) 

  phi = math.atan2(dy, dx) 
  theta = math.acos(dz/dist) 

  bpy.context.object.rotation_euler[1] = theta 
  bpy.context.object.rotation_euler[2] = phi

def convert_envelope(arm, context):
    coords = []
    obs = []
    prop = context.scene.bbones
    for bone in arm.data.bones:      
        
        x1,y1,z1 = bone.tail_local+arm.location
        r1 = bone.tail_radius
        coord1 = (x1,y1,z1,r1)
        if coord1 not in coords:
            coords.append(coord1)
        
            bpy.ops.mesh.primitive_uv_sphere_add(
            radius = r1,
            location = bone.tail_local+arm.location,
            
            )
            obs.append(context.object.name)

        x2,y2,z2 = bone.head_local+arm.location
        r2 = bone.head_radius
        coord2 = (x2,y2,z2,r2)
        if coord2 not in coords:
            coords.append(coord2)
            bpy.ops.mesh.primitive_uv_sphere_add(
            radius = r2,
            location = bone.head_local+arm.location
            )
            obs.append(context.object.name)
        cone_between(x1, y1, z1, x2, y2, z2, r1,r2)

        obs.append(context.object.name)
 
    for ob in obs:
        bpy.context.collection.objects[ob].select_set(True)
    bpy.ops.object.join()
    
    obj = context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    cursor = context.scene.cursor.location
    context.scene.cursor.location = arm.location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    context.scene.cursor.location = cursor
    mesh = obj.data
    obj.data = mesh
    return obj

def RemoveDoubles (mesh,distance):
    
    bm = bmesh.new()   
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
    bm.to_mesh(mesh)
    mesh.update()
    bm.clear()

    bm.free()
    return mesh

def convert_skin(context):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """
    verts = []
    edges = []
    arm = context.object
    bones = arm.data.bones
    radius = []
    
    for b in bones:
        v1 = b.head_local
        r1 = b.head_radius
        v2 = b.tail_local
        r2 = b.tail_radius
        
        verts.append(v1)
        verts.append(v2)
        radius.append(r1)
        radius.append(r2)

        edges.append( (verts.index(verts[-1]),verts.index(verts[-2])))


    return verts, edges, radius

# =====================================================
#                       PROPERTIES
# =====================================================

class SCENE_PG_BBone_Tools(PropertyGroup):

    name: StringProperty(
            name="Name",
            default= "BBone",
            description="Name for the BBone Armature object"
            )

    distance: FloatProperty(
            name="Clean Limit",
            default=0.001,
            description="Distance from vertices to collpse to clean surface"
            )

# =====================================================
#                       OPERATORS
# =====================================================

class OBJECT_OT_AddBBone(bpy.types.Operator):
    """Add a simple BBone in Edit Mode"""
    bl_idname = "object.addbbone"
    bl_label = "Add BBone Armature"
    bl_options = {'REGISTER', 'UNDO'}

    

    def execute(self, context):
        prop = context.scene.bbones
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.armature_add()
        
        ob = context.object
        ob.name = prop.name+" (BBone Armature)" ###set The name of the Armature 

        ob.data.display_type = 'ENVELOPE'
        ob.show_in_front = True
        bpy.ops.object.mode_set(mode='EDIT')
        
        return {'FINISHED'}

class OBJECT_OT_Convert_BBone(bpy.types.Operator):
    """Convert or Update BBone Armature to BBone Skin or BBone Mesh Object"""
    bl_idname = "object.convert_bbone"
    bl_label = "Convert Envelope"
    bl_options = {'REGISTER', 'UNDO'}
    
    update : BoolProperty(default=False)
    envelope : BoolProperty(default=False)
    
    
    # generic transform props
    align_items = (
        ('WORLD', "World", "Align the new object to the world"),
        ('VIEW', "View", "Align the new object to the view"),
        ('CURSOR', "3D Cursor", "Use the 3D cursor orientation for the new object")
    )
    align: EnumProperty(
        name="Align",
        items=align_items,
        default='WORLD',
        update=AddObjectHelper.align_update_callback,
    )
    location: FloatVectorProperty(
        name="Location",
        subtype='TRANSLATION',
    )
    rotation: FloatVectorProperty(
        name="Rotation",
        subtype='EULER',
    )

    def execute(self, context):
        prop = context.scene.bbones
        arm = context.object
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        cursor = context.scene.cursor.location
        context.scene.cursor.location = context.object.location
        arm.display_type = 'WIRE'
        armname = arm.name.replace(" (BBone Armature)","")
        
        if self.envelope:            
            if not self.update:
                convert_envelope(arm, context)
                obj = context.object
                obj.name = armname+" (BBone Mesh)"
                obj.is_linked = True
                arm.envelope_ID = obj.name
                rem = obj.modifiers.new("Remesh", 'REMESH')
                rem.voxel_size = 0.017

            else:
                if 'EDIT' in context.mode:
                    bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                
                obj = convert_envelope(arm, context)
                
                _obj = context.collection.objects[arm.envelope_ID]
                _mesh = _obj.data
                
                _obj.data = obj.data
                
                context.collection.objects.unlink(obj)
                bpy.data.meshes.remove(_mesh)

            return {'FINISHED'}
        
        else:
            verts_loc, edges, radius = convert_skin(
                context
            )

            mesh = bpy.data.meshes.new("Skin")
            bm = bmesh.new()

            for v_co in verts_loc:
                bm.verts.new(v_co)

            bm.verts.ensure_lookup_table()
            for e_idx in edges:
                bm.edges.new([bm.verts[i] for i in e_idx])

            #bmesh.ops.split_edges(bm,edges=bm.edges)
            #bpy.ops.object.mode_set(mode = 'OBJECT')
            bm.to_mesh(mesh)
            mesh.update()
            if not self.update:
                # add the mesh as an object into the scene with this utility module
                from bpy_extras import object_utils
                object_utils.object_data_add(context, mesh, operator=self)
                
                context.scene.cursor.location = cursor
                
                obj = context.object
                obj.name =armname+"(BBone Skin)"
                obj.is_linked = True
                arm.envelope_ID = obj.name
                mod = obj.modifiers.new("Subdiv",'SUBSURF')
                mod.subdivision_type = 'SIMPLE'
                mod.levels = 2
                obj.modifiers.new("Skin",'SKIN')
            else:
                obj = context.scene.objects[arm.envelope_ID]
                _mesh = obj.data
                obj.data = mesh
                bpy.data.meshes.remove(_mesh)
                context.view_layer.objects.active = obj
                bpy.ops.mesh.customdata_skin_add()
                context.scene.cursor.location = cursor
                context.view_layer.objects.active = arm
            i = 0
            for r in radius:
                obj.data.skin_vertices[0].data[i].radius = r* 1.1,r* 1.1
                i+=1        
            
            #mesh = obj.data
            #mesh_ = RemoveDoubles (mesh, prop.distance)
            #mesh_ = mesh
            #obj.data = mesh_

            bpy.context.view_layer.objects.active = None
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.rip('INVOKE_DEFAULT')
            bpy.ops.object.skin_root_mark()

            #SELECT THE LOOSE VERTEX (skin spheres)

            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')  
 
            # bpy.ops.object.mode_set(mode='OBJECT')
            # for v in obj.data.vertices:
            #     if v.select:
            #         obj.data.skin_vertices[0].data[v.index].radius[0] = obj.data.skin_vertices[0].data[v.index].radius[0] * 1.1
            #         obj.data.skin_vertices[0].data[v.index].radius[1] = obj.data.skin_vertices[0].data[v.index].radius[1] * 1.1
            bpy.ops.object.mode_set(mode='OBJECT')

            #ADDING SPHERES AT HEAD AND TAILS
            mesh2 = bpy.data.meshes.new("Spheres")
            bm2 = bmesh.new()
            for v_co in verts_loc:
                bm2.verts.new(v_co)
            bm.verts.ensure_lookup_table()
            bm2.to_mesh(mesh2)
            mesh2.update()

            # add the mesh as an object into the scene with this utility module
            from bpy_extras import object_utils
            object_utils.object_data_add(context, mesh2, operator=self)

            #obj2 = bpy.data.objects.new('Spheres', mesh2)
                            
            context.scene.cursor.location = cursor
            obj2 = context.object
            context.view_layer.objects.active = obj2
            bpy.ops.mesh.customdata_skin_add()
            context.scene.cursor.location = cursor

            #bpy.context.scene.collection.objects.link(obj2)
            obj2.modifiers.new("Skin",'SKIN')

            i = 0
            for r in radius:
                obj2.data.skin_vertices[0].data[i].radius = r* 1.2,r* 1.2
                i+=1
            #REMOVE DOUBLES
            meshx = obj2.data
            mesh_ = RemoveDoubles (meshx, prop.distance)
            mesh_ = meshx
            obj2.data = mesh_

            obj.select_set(True)
            obj2.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.join()
    

            if not self.update:
                mod = obj.modifiers.new("Subdiv",'SUBSURF')
                mod.levels = 2
                #Adding Remesh Mod
                rem = obj.modifiers.new("Remesh", 'REMESH')
                rem.voxel_size = 0.017
                return {'FINISHED'}
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
            return {'FINISHED'}

class OBJECT_OT_LinkBBone(bpy.types.Operator):
    """Link BBone Armature to a Mesh""" 
    bl_idname = "object.linkbbone"
    bl_label = "Link BBone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #obj = context.object
        objs = context.selected_objects
        msh = ""
        if context.mode != 'OBJECT' :
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in objs:
            if obj.type == 'MESH':
                if "Remesh" not in obj.modifiers: # Make sure the mesh has remesh modifier, if not then add one.
                    rem = obj.modifiers.new("Remesh", 'REMESH')
                    rem.voxel_size = 0.017
                if "(BBone Mesh)" not in obj.name:
                    obj.name =  obj.name+" (BBone Mesh)"
                msh = obj.name
                
        for obj in objs:
            if obj.type == 'ARMATURE':
                obj.envelope_ID = msh #registring the mesh name as the envelope ID

                obj.data.display_type = 'ENVELOPE'
                obj.display_type = 'WIRE'
                obj.show_in_front = True
                #bpy.ops.object.mode_set(mode='EDIT_MESH')
        return {'FINISHED'}

class OBJECT_OT_UnlinkBBone(bpy.types.Operator):
    """Unlink BBone Armature from Mesh or Skin"""
    bl_idname = "object.unlinkbbone"
    bl_label = "Unlink BBone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj.type == 'ARMATURE':
            if context.mode != 'OBJECT' :
                bpy.ops.object.mode_set(mode='OBJECT')
            
            obj.envelope_ID = ""

            obj.data.display_type = 'ENVELOPE'
            obj.display_type = 'TEXTURED'
            obj.show_in_front = True
            #bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class OBJECT_OT_Remesh(bpy.types.Operator):
    """Remesh Linked Mesh"""
    bl_label = "Remesh BBone"
    bl_idname = "object.bbone_remesh"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self,context):
        obj = context.object
        if obj.type =='ARMATURE':
            id = obj.envelope_ID
            msh = bpy.data.objects[id]

            if "BBone Mesh" in obj.envelope_ID:
                obj.hide_set(True)
                obj.envelope_ID = ""
                obj.display_type = 'TEXTURED'
                obj.data.display_type = 'ENVELOPE'
                obj.show_in_front = True
                bpy.context.view_layer.objects.active = msh
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS',object=True,obdata=True)
                #bpy.ops.object.modifier_apply(modifier="Remesh")
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='SCULPT')
                context.window.workspace = bpy.data.workspaces['Sculpting']
            if "BBone Skin" in obj.envelope_ID:
                obj.hide_set(True)
                obj.envelope_ID = ""
                obj.display_type = 'TEXTURED'
                obj.data.display_type = 'ENVELOPE'
                obj.show_in_front = True
                bpy.context.view_layer.objects.active = msh
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS',object=True,obdata=True)
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='SCULPT')
                context.window.workspace = bpy.data.workspaces['Sculpting']
             
            return {'FINISHED'}
        if obj.type =='MESH':
            #id = obj.envelope_ID
            if "BBone Mesh" in obj.name:
                for arm in context.scene.objects: 
                    if arm.envelope_ID == obj.name:
                        arm.hide_set(True) 
                        arm.envelope_ID = ""
                        arm.display_type = 'TEXTURED'
                        arm.data.display_type = 'ENVELOPE'
                        arm.show_in_front = True
                context.view_layer.objects.active = obj
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS',object=True,obdata=True)
                #bpy.ops.object.modifier_apply(modifier="Remesh")
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='SCULPT')
                context.window.workspace = bpy.data.workspaces['Sculpting']
            if "BBone Skin" in obj.name:
                for arm in context.scene.objects: 
                    if arm.envelope_ID == obj.name:
                        arm.hide_set(True) 
                        arm.envelope_ID = ""
                        arm.display_type = 'TEXTURED'
                        arm.data.display_type = 'ENVELOPE'
                        arm.show_in_front = True
                context.view_layer.objects.active = obj
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS',object=True,obdata=True)
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='SCULPT')
                context.window.workspace = bpy.data.workspaces['Sculpting']
            return {'FINISHED'}

class OBJECT_OT_SymmetrizeArm(bpy.types.Operator):
    """Symmetrize Selected BBones while in Edit Mode"""
    bl_label = "Symmetrize Selected BBones"
    bl_idname = "object.symmetrize_bones"
    bl_options = {'REGISTER','UNDO'}

    def execute(self,context):
        bpy.ops.armature.autoside_names(type='XAXIS')
        bpy.ops.armature.symmetrize()
        return{'FINISHED'}

class DRAW_HT_UI(Panel):
    bl_label = "BBones"
    bl_idname = "BBONE_HT_DRAW_UI"
    bl_region_type = "WINDOW"
    bl_space_type = "VIEW_3D"

    def draw(self, context):
        prop = context.scene.bbones
        obj = context.object
        objs = context.selected_objects
        selectsize = len(objs)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        row = layout.row(align=True)

        row.operator("object.addbbone",
                        icon='OUTLINER_OB_ARMATURE',
                        text="Add New BBone Armature")
        row = layout.row(align=True)
        row.prop(prop, "name")
        row = layout.row(align=True)
        row.separator()

        row = layout.row(align=True)
        col = row.column(align=True)
        if obj:
            if selectsize == 1: # if there is only one selected object
                if obj.type == 'ARMATURE' and obj.envelope_ID != "":
                    col.label(text="Active BBone Armature:")
                    row = layout.row(align=True)
                    row.separator()
                if context.mode == 'EDIT_ARMATURE':
                    row = layout.row(align=True)
                    col = row.column(align=True)
                    env= col.operator("object.symmetrize_bones",
                                    icon='MOD_MIRROR',
                                    text="Symmetrize")

            row = layout.row(align=True)
            col = row.column(align=True)
            if selectsize == 2: # if there is only two selected objects
                if (objs[0].type == 'ARMATURE' and objs[1].type == 'MESH') or (objs[0].type == 'MESH' and objs[1].type == 'ARMATURE'): #If selected objects are armature and mesh
                    env = col.operator("object.linkbbone",
                                    icon='LINKED',
                                    text="Link Selected")
            elif obj.type == 'ARMATURE' and selectsize !=0:
                if obj.envelope_ID == "":
                    env = col.operator("object.convert_bbone",
                                    icon='MOD_SKIN',
                                    text="BBone Skin")
                    env.update = False
                    env.envelope = False
                
                if obj.envelope_ID != "":
                    if obj.envelope_ID in context.scene.objects:
                        env = col.operator("object.convert_bbone",
                                        icon='FILE_REFRESH',
                                        text="Update")
                        env.update = True
                        if "Skin" in obj.envelope_ID:
                            env.envelope = False
                        else:
                            env.envelope = True
                    if obj.envelope_ID in context.scene.objects:
                        env = col.operator("object.unlinkbbone",
                                        icon='UNLINKED',
                                        text="Unlink Armature")
                    row.separator()
                    col.label(text="Finalize:")
                    row.separator()
                    if obj.envelope_ID in context.scene.objects:

                        env = col.operator("object.bbone_remesh",
                                        icon='MOD_REMESH',
                                        text="Remesh")

                if obj.envelope_ID == "":        
                    col = row.column(align=True)
                    env = col.operator("object.convert_bbone",
                                    icon='MOD_SKIN',
                                    text="BBone Mesh")
                    env.envelope = True
                    env.update = False
            elif obj.type == 'MESH' and selectsize !=0:
                if 'Remesh' in obj.modifiers:
                    col.label(text="Finalize:")
                    row.separator()
                    if obj.is_linked:
                        env = col.operator("object.bbone_remesh",
                                        icon='MOD_REMESH',
                                        text="Remesh")
            else:
                row.label(text="Select or Add BBone Armature")
        else:
            row.label(text="Select or Add BBone Armature")

classes = (
    SCENE_PG_BBone_Tools,
    OBJECT_OT_Convert_BBone,
    OBJECT_OT_AddBBone,
    OBJECT_OT_LinkBBone,
    OBJECT_OT_UnlinkBBone,
    OBJECT_OT_SymmetrizeArm,
    OBJECT_OT_Remesh,
    DRAW_HT_UI,
    )

def menu_func(self, context):
    
    layout = self.layout
    layout.popover("BBONE_HT_DRAW_UI",)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.bbones = PointerProperty(type=SCENE_PG_BBone_Tools)
    bpy.types.Object.envelope_ID = StringProperty(default="")
    bpy.types.Object.is_linked = BoolProperty(default=False)
    bpy.types.VIEW3D_HT_tool_header.append(menu_func)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_HT_tool_header.remove(menu_func)
    del bpy.types.Scene.bbones
if __name__ == "__main__":
    register()
