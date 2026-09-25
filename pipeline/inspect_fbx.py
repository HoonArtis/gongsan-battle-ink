import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
for f in argv:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f, automatic_bone_orientation=False)
    for o in bpy.context.scene.objects:
        print('OBJ', o.name, o.type, tuple(round(x, 3) for x in o.scale))
        if o.type == 'ARMATURE':
            print('BONES', len(o.data.bones), [b.name for b in o.data.bones][:80])
            ad = o.animation_data
            if ad and ad.action: print('ACTION', ad.action.name, tuple(ad.action.frame_range))
    print('SCENE fps', bpy.context.scene.render.fps, bpy.context.scene.frame_start, bpy.context.scene.frame_end)
