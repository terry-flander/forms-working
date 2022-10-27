"""
 NEW VERSION OF ROUTINE FOR NEW DIS LAYOUT ->
    for each FIBER
        for each COMPONENT
            for each SENSOR TYPE
                SENSOR

 Routines required to transform form data into layout information.
 From the sensor position, calculates algorithms which can be 
 generated based on location and type.

 Returns four arrays

 1. Fiber layouts for all components
 2. Shear Algorithms
 3. Bending Moment Algorithms
 4. Deflection Algorithms
 
"""
import logging
from app.lib.util import setup_logger

debug_logger = setup_logger('debug', 'tmp/app_debug.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

def calculate_layout_v2(d):
    result = 'ok'

    layout = []
    girder_shear = []
    girder_bending_moment = []
    shear_no = 0
    bm_no = 0
    girder_deflection = []

    try:
        app_logger.info('calculate_layout_v2')
        bm_no = 0
        if bool(d):
            jinja_template = d["jinja_template"]
            fibers = d["fibers"]
            for f in fibers:
                fiberId = f['fiberId']
                components = get_components(f)
                for c in components:
                    componentId = get_component_id(c)
                    component_type = get_componentType(d, componentId)
                    if component_type != None:
                        structure = [s for s in d['structure'] if s.get('componentId') == componentId]
                        layout_c = calculate_component(fiberId, structure, component_type, c, jinja_template)
                        layout += layout_c
                        # Get Shear algorithma (3d_rosette)
                        shear = getShear(layout_c, shear_no)
                        for s in shear[0]:
                            girder_shear.append(s)
                        shear_no = shear[1]
                        # Get Bending Moment algorithms (strain pairs by x-pos)
                        bm = getBendingMoment(layout_c, bm_no)
                        for s in bm[0]:
                            girder_bending_moment.append(s)
                        bm_no = bm[1]

            # Use BM pairs to create deflection algorithms
            girder_deflection = getDeflection(girder_bending_moment)

    except Exception as ex:
        app_logger.error(ex)
        result = f'Unable to process: {ex}'

    return result, layout, girder_shear, girder_bending_moment, girder_deflection

def get_components(f):
    try:
        return f["fiberComponent"]
    except Exception:
        return []

def get_component_id(c):
    try:
        return c['componentId']['value']
    except Exception:
        return ''

def get_componentType(d, componentId):
    result = None
    try:
        # get the structure row for this componentId
        structure = [s for s in d['structure'] if s.get('componentId') == componentId]
        # get componentType from structure
        componentType = getComponentTypeKey(structure)
        # get componentType row for this componentType
        component_type = [c for c in d['componentTypes'] if c.get('componentType') == componentType]
        result = component_type[0]
    except Exception as ex:
        app_logger.info(f'No type for: {componentId} Error: {ex.message}')
    finally:
        if componentId != '' and result == None:
            app_logger.info(f'Unable to find: {componentId} in structure {structure}')
        return result

def getComponentTypeKey(structure):
    r = structure[0]['componentType']
    if type(r) == dict:
        result = r['value']
    else:
        result = r
    return result

def calculate_component(fiberId, structureArray, component_type, c, jinja_template):
    layout = []

    structure = structureArray[0]
    component = structure['componentId']
    length = 0
    height = 0
    left_margin = 0
    right_margin = 0
    bottom_margin = 0
    top_margin = 0
    try:
        length = get_value(component_type, 'length', 0)
        height = get_value(component_type, 'height', 0)
        left_margin = get_value(c, 'leftMargin', 0)
        right_margin = get_value(c, 'rightMargin', 0)
        bottom_margin = get_value(c, 'bottomMargin', 0)
        top_margin = get_value(c, 'topMargin', 0)

        right_margin = scaleIt(length - right_margin, 3)
        shear_sensors = scaleIt(height / 2, 3)
        midspan = scaleIt(length / 2, 3)
        componentId = component
        column_margin = scaleIt(height - top_margin - bottom_margin, 3)
    except:
        app_logger.info (f'component {component} missing or invalid value(s). Using defaults.')
        app_logger.info (f'length: {length} height: {height} left_margin: {left_margin} right_margin: {right_margin} top_margin: {top_margin} bottom_margin: {bottom_margin}')
 
 
    sensorTypes = c['sensorTypes']

    # Make list of non-strain sensor numbers to skip during auto-layout of strain 
    skipList = []
    for  t in sensorTypes:
        if t["position"]=='custom':
            if t['sensorType'] != 'rosette':
                k = t['typeFirst']
                while k <= t['typeLast']:
                    skipList.append(k)
                    k += 1
            else:
                k = t['typeFirst']
                while k <= t['typeFirst'] + 2:
                    skipList.append(k)
                    k += 1

    try:
        layout_sensor = {}
        for t in sensorTypes:
            layout_sensor = t
            side = t['side']
            first = t['typeFirst']
            last = t['typeLast']
            sensorType = t['sensorType']
            position = t['position']
            desc = ''
            fromTop = 0
            fromLeft = 0
            sensorSpacing = 0
            fromRight = 0
            angle = 0
            note = ''
            if sensorType == 'rosette':
                last = first + 2
            if position == 'custom':
                x = t['customX']
                y = t['customY']
                i = first
                while i <= last:
                    angle = 0
                    if sensorType == 'rosette':
                        if i==first:
                            angle = 0
                        elif i==last:
                            angle = 45
                        else:
                            angle = 90
                    fromTop = scaleIt(y, 3)
                    sensorSpacing = scaleIt(abs(x - fromLeft), 3)
                    fromLeft = x
                    fromRight = scaleIt(length - x, 3)
                    desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                    layout.append(sensorRow(
                        fiberId,  i, componentId, sensorType, x, y, side, angle, desc, 
                        fromTop, fromLeft, sensorSpacing, fromRight, note))
                    i += 1
            elif sensorType == 'strainHorizontal':
                x = left_margin
                count = 0
                i = first
                while i <= last:
                    if not i in skipList:
                        count += 1
                    i += 1
                # Prevent divide by zero -- Only possible if only single sensor to be positioned
                if count <= 2:
                    count = 2
                offset = scaleIt((right_margin - left_margin) / (count - 1), 3)
                ypos = 0
                if side == 'top':
                    ypos = top_margin
                else:
                    ypos = scaleIt(height - bottom_margin, 3)

                if position == 'R2L':
                    x = right_margin
                    offset = scaleIt((right_margin - left_margin) / (count - 1), 3) * -1

                fromTop = scaleIt(height - top_margin, 3)
                sensorSpacing = scaleIt(abs(x - fromLeft), 3)
                fromLeft = x
                fromRight = scaleIt(length - x, 3)
                note = 'first'
                desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m - first'
                i = first
                while i <= last:
                    if not i in skipList:
                        sensorSpacing = scaleIt(abs(x - fromLeft), 3)
                        fromLeft = x
                        fromRight = scaleIt(length - x, 3)
                        desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                        if i == last:
                            desc += " - last"
                            note = "last"
                        if x == midspan:
                            desc += ' - midspan'
                            note = "midspan"
                        layout.append(sensorRow(
                                fiberId, i, componentId, sensorType, x, ypos, side, angle, desc, 
                                fromTop, fromLeft, sensorSpacing, fromRight, note))
                        x = scaleIt(x + offset, 3)
                        note = ''
                    i += 1
            elif sensorType == 'strainVertical':
                ypos = top_margin
                count = 0
                i = first
                while i <= last:
                    if not i in skipList:
                        count += 1
                    i += 1
                offset = scaleIt(column_margin / (count - 1), 3)
                x = 0
                if side == 'left':
                    x = left_margin
                else:
                    x = scaleIt(length - right_margin, 3)

                if position == 'B2T':
                    ypos = scaleIt(height - bottom_margin,3)
                    offset = offset * -1

                fromLeft = x
                fromTop = ypos
                note = 'first'
                i = first
                while i <= last:
                    if not i in skipList:
                        fromBottom = scaleIt(height - ypos, 3)
                        sensorSpacing = scaleIt(abs(ypos - fromTop), 3)
                        fromTop = ypos
                        desc = 'from Left: ' + str(fromLeft) + ' mm - from Column Top: ' + str(fromTop) + ' m - from Column Bottom: ' + str(fromBottom) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                        if i == last:
                            desc += " - last"
                            note = "last"
                        layout.append(sensorRow(
                                fiberId, i, componentId, sensorType, x, ypos, side, angle, desc, 
                                fromLeft, fromTop, sensorSpacing, fromBottom, note))
                        ypos = scaleIt(ypos + offset, 3)
                        note = ''
                    i += 1
            elif sensorType == 'rosette':
                pos = right_margin
                if position == 'left':
                    pos = left_margin
                fromTop = scaleIt(shear_sensors, 3)
                sensorSpacing = scaleIt(abs(length - fromLeft), 3)
                fromLeft = pos
                fromRight = scaleIt(length - pos, 3)
                note = ''
                desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                i = first
                while i <= last:
                    angle = 90
                    if i==first:
                        angle = 0
                    elif i==last:
                        angle = 45
                    layout.append(
                        sensorRow(fiberId, i, componentId, sensorType, pos, shear_sensors, side, angle,
                            desc, fromTop, fromLeft, sensorSpacing, fromRight, note)
                            )
                    i += 1
    except Exception as ex:
        app_logger.error(f'{ex} skiplist: {skipList} with {layout_sensor}')

    return layout

def sensorRow (fiberId, sensor_id, componentId, sensorType, 
               x,  y, side, angle, desc, 
               fromTop, fromLeft, sensorSpacing, fromRight, note):
    return {
                "type": "sensor",
                "fiber": fiberId, 
                "sensor": sensor_id, 
                "component_id": componentId, 
                "sensor_type": sensorType, 
                "x": x, 
                "y": y, 
                "side": side, 
                "angle": angle, 
                "layout": desc, 
                "fromTop": fromTop, 
                "fromLeft": fromLeft, 
                "sensorSpacing": sensorSpacing, 
                'fromRight': fromRight, 
                'note': note
            }

def getShear (layout, shear_no):
    shear = []
    rosette = False
    for s in layout:
        if s['sensor_type'] == 'rosette':
            rosette = True
            if s['angle'] == 0:
                rosette_0 = s['sensor']
            elif s['angle'] == 45:
                rosette_45 = s['sensor']
            else:
                rosette_90 = s['sensor']
        else:
            if rosette == True:
                shear_no += 1
                shear.append({"type": "algorithm", \
                    "id": "SH" + padIt(shear_no, 2), \
                    "algorithm_type": "girder_shear", \
                    "fiber_id": s['fiber'], \
                    "component_id": s['component_id'], \
                    "sensor_type": "3d_rosette",\
                    "rosette_0": rosette_0, \
                    "rosette_45": rosette_45, \
                    "rosette_90": rosette_90 \
                     })
                rosette = False
    if rosette == True:
        shear_no += 1
        shear.append({"type": "algorithm", \
            "id": "SH" + padIt(shear_no, 2), \
            "algorithm_type": "girder_shear", \
            "fiber_id": s['fiber'], \
            "component_id": s['component_id'], \
            "sensor_type": "3d_rosette",\
            "rosette_0": rosette_0, \
            "rosette_45": rosette_45, \
            "rosette_90": rosette_90 \
                })      
    return shear, shear_no

def getBendingMoment (layout, bm_no):
    bending_moment = []
    index = 0
    for s in layout:
        index += 1
        # Look forward for matching x on same component
        if s['sensor_type'].startswith('strain'):
            for i in range(index + 1, len(layout)):
                if layout[i]['component_id'] == s['component_id'] \
                    and layout[i]['x'] == s['x']:
                    bm_no += 1
                    bending_moment.append({"type": "algorithm", \
                        "id": "BM" + padIt(bm_no, 2), \
                        "algorithm_type": "girder_bending_moment", \
                        "fiber_id": s['fiber'], \
                        "component_id": s['component_id'], \
                        "sensor_type": "sensor_pair",\
                        "sensor_top": s['sensor'], \
                        "sensor_bottom": layout[i]['sensor'] \
                        })
                    break
    return bending_moment, bm_no

# User bending_moment sensor pairs to create deflection arrays
def getDeflection (bending_moment):
    deflection = []
    def_no = 0
    component_id = ''
    fiber_id = ''
    top_sensors = []
    bottom_sensors = []
    for bm in bending_moment:
        if bm['component_id'] != component_id:
            if component_id != "":
                def_no += 1
                deflection.append({"type": "algorithm", \
                    "id": "D" + padIt(def_no, 2), \
                    "algorithm_type": "girder_deflection", \
                    "fiber_id": fiber_id, \
                    "component_id": bm['component_id'], \
                    "sensor_type": "sensor_pair_array",\
                    "sensors_top": top_sensors, \
                    "sensors_bottom": bottom_sensors})
            top_sensors = []
            bottom_sensors = []
            fiber_id = bm['fiber_id']
            component_id = bm['component_id']
        top_sensors.append(bm['sensor_top'])
        bottom_sensors.append(bm['sensor_bottom'])
    # Last One
    if component_id != "":
        def_no += 1
        deflection.append({"type": "algorithm", \
            "id": "D" + padIt(def_no, 2), \
            "algorithm_type": "girder_deflection", \
            "fiber_id": fiber_id, \
            "component_id": component_id, \
            "sensor_type": "sensor_pair_array",\
            "sensors_top": top_sensors, \
            "sensors_bottom": bottom_sensors})
    return deflection

def scaleIt(value, scale):
    result = value
    try:
        result = round(value, scale)
    except:
        app_logger.info(f'Unable to round: {value} scale {scale}')
    return result

def padIt(value, width):
    return ("0000" + str(value))[-width:]

def get_value(data, field_id, default_value):
    try:
        return data[field_id]
    except:
        return default_value


