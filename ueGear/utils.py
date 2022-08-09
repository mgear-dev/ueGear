import maya.cmds as cmds


def get_unreal_engine_transform_for_maya_node(node_name):

		def _xyz_list_build(param):
			xyz_list = param[:]
			xyz_list[0] = param[0]
			xyz_list[1] = param[2]
			xyz_list[2] = param[1]

			return xyz_list

		attr_dict = dict()
		attr_dict['translation'] = cmds.xform(node_name, q=True, ws=True, t=True)
		attr_dict['rotation'] = cmds.xform(node_name, q=True, ws=True, ro=True)
		attr_dict['scale'] = cmds.xform(node_name, q=True, ws=True, s=True)
		attr_dict['rotatePivot'] = cmds.xform(node_name, q=True, ws=True, rp=True)
		attr_dict['scalePivot'] = cmds.xform(node_name, q=True, ws=True, sp=True)

		up_axis = cmds.upAxis(query=True, ax=True)
		if up_axis.lower() == 'y':
			attr_dict['translation'] = _xyz_list_build(attr_dict['translation'])
			attr_dict['rotation'] = _xyz_list_build(attr_dict['rotation'])
			attr_dict['scale'] = _xyz_list_build(attr_dict['scale'])
			attr_dict['rotatePivot'] = _xyz_list_build(attr_dict['rotatePivot'])
			attr_dict['scalePivot'] = _xyz_list_build(attr_dict['scalePivot'])

		return attr_dict
