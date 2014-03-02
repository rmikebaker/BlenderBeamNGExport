

bl_info = {
    "name": "Export Jbeam (.jbeam)",
    "author": "Mike Baker (rmikebaker)",
    "version": (0, 0, 1),
    "description": "Export Nodes and Beams for BeamNG (.jbeam)",
    "category": "Object"
    }

__version__ = '0.0.1'


import bpy
import os
import struct


class NGnode(object):
    def __init__(self, i, nodeName, x, y, z):
        self.i = i
        self.nodeName = nodeName
        self.x = x
        self.y = y
        self.z = z


class ExportJbeam(bpy.types.Operator):
    """Export Nodes and Beams to .jbeam file for BeamNG"""
    bl_idname = 'object.export_jbeam'
    bl_description = 'Export for use in BeamNG (.jbeam)'
    bl_label = 'Export Jbeam' + ' v.' + __version__

    # execute() is called by blender when running the operator.
    def execute(self, context):

        file = None
        
        # Need path for saving data to file
        filepath = bpy.path.abspath('//')
        if filepath == '':
            self.report({'ERROR'}, "You must save your objects to a .blend file first")        
            return {'FINISHED'}
                                               
        scene = context.scene

        # Save currently active object
        active = context.active_object

        selectedObjects = []
        for o in context.selected_objects:
            if (o.type == 'MESH'):
                o.select = False
                selectedObjects.append(o)
        
        try:
            for objsel in selectedObjects:
                # Make the active object be the selected one
                scene.objects.active = objsel
    
                # Want to be in Object mode
                bpy.ops.object.mode_set(mode='OBJECT')
    
                # Prefix for node names
                try:
                    nodePrefix = objsel['JbeamNodePrefix']
                except:
                    nodePrefix = 'n'
                    
                #-------------------------------------
                # Create a copy of the selected object
                #-------------------------------------
                
                tempName = objsel.name + '.JBEAM_TEMP'
                 
                # Create new mesh
                tempMesh = bpy.data.meshes.new(tempName)
             
                # Create new object associated with the mesh
                ob_new = bpy.data.objects.new(tempName, tempMesh)
             
                # Copy data block from the old object into the new object
                ob_new.data = objsel.data.copy()
                ob_new.scale = objsel.scale
                ob_new.location = objsel.location
                ob_new.rotation_axis_angle = objsel.rotation_axis_angle
                ob_new.rotation_euler = objsel.rotation_euler
                ob_new.rotation_mode = objsel.rotation_mode
                ob_new.rotation_quaternion = objsel.rotation_quaternion
                
                # Link new object to the given scene, select it, and
                # make it active
                scene.objects.link(ob_new)
                ob_new.select = True
                scene.objects.active = ob_new
             
                # Apply transforms
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
                # TODO: Can we copy modifiers from original object and then do this?
                #mesh = ob_new.to_mesh(scene, True, 'PREVIEW')
                
                # Sort vertices
                mesh = ob_new.data
                nodes = []
                for v in mesh.vertices:
                    node = NGnode(v.index,
                                  nodePrefix,
                                  round(v.co[0] + objsel.delta_location[0], 3),
                                  round(v.co[1] + objsel.delta_location[1], 3),
                                  round(v.co[2] + objsel.delta_location[2], 3))
                    nodes.append(node)
    
                sortedz = sorted(nodes, key=lambda NGnode: NGnode.z)
                sortedx = sorted(sortedz, key=lambda NGnode: NGnode.x, reverse=True)
                sortedNodes = sorted(sortedx, key=lambda NGnode: NGnode.y)                
                    
                # Export
                anewline = '\n'
                filename = objsel.name + '.jbeam'
                file = open(filepath + '/' + filename, 'wt')
    
                i = 0
                file.write('//--Nodes--')
                file.write(anewline)
                for v in sortedNodes:
                    file.write('[\"')
                    if v.x > 0:
                        v.nodeName = v.nodeName + 'l' + ('%s' % (i))
                    elif v.x < 0:
                        v.nodeName = v.nodeName + 'r' + ('%s' % (i))
                    else:
                        v.nodeName = v.nodeName + ('%s' % (i))
                    file.write(v.nodeName)
                    file.write('\",')
                    file.write('%s' % (round(v.x + objsel.delta_location[0], 3))) 
                    file.write(',') 
                    file.write('%s' % (round(v.y + objsel.delta_location[1], 3)))
                    file.write(',')
                    file.write('%s' % (round(v.z + objsel.delta_location[2], 3)))
                    file.write('],')
                    file.write(anewline)
                    i += 1
    
                file.write('//--Beams--')
                file.write(anewline)
                for e in mesh.edges:
                    nodeIndex1 = ([n.i for n in sortedNodes].index(e.vertices[0]))
                    file.write('[\"%s\"' % (sortedNodes[nodeIndex1].nodeName)) 
                    file.write(',') 
                    nodeIndex2 = ([n.i for n in sortedNodes].index(e.vertices[1]))
                    file.write('\"%s\"' % (sortedNodes[nodeIndex2].nodeName))
                    file.write('],')
                    file.write(anewline)
    
                file.flush()
                file.close()
    
                # Deselect our new object
                ob_new.select = False
                
                # Remove the new temp object
                scene.objects.unlink(ob_new)
                bpy.data.objects.remove(ob_new)
                
                if (mesh.users == 0):
                    mesh.user_clear()
                    
                bpy.data.meshes.remove(mesh)
                
                if (tempMesh.users == 0):
                    tempMesh.user_clear()
                    
                bpy.data.meshes.remove(tempMesh)
            
            # Restore selection status
            for o in selectedObjects:
                o.select = True
                    
            # Restore active object
            scene.objects.active = active
            
        except Exception as e:
            self.report({'ERROR'}, 'ERROR: ' + str(e))
            if file: file.close()
        
        # this lets blender know the operator finished successfully.
        return {'FINISHED'}                               

def register():
    bpy.utils.register_class(ExportJbeam)

def unregister():
    bpy.utils.unregister_class(ExportJbeam)

# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
