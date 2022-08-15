"""
 Routines required to transform form data into layout information.
 From the sensor position, calculates algorithms which can be 
 generated based on location and type.

 Returns four arrays

 1. Fiber layouts for all components
 2. Shear Algorithms
 3. Bending Moment Algorithms
 4. Deflection Algorithms
 
"""
def calculate_layout_v1(d):
    print('calculate_layout')
    layout = []
    girder_shear = []
    girder_bending_moment = []
    girder_deflection = []
    if bool(d):
        components = d["components"]
        jinja_template = d["jinja_template"]
        shear_no = 0
        bm_no = 0
        for c in components:
            if not c:
                layout_c = calculate_component(c, jinja_template)
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

    return layout, girder_shear, girder_bending_moment, girder_deflection

def calculate_component(c, jinja_template):
    if c['units']!='metric':
        lengthM = c['lengthMetersI']
        heightM = c['heightMetersI']
        depthM = c['depthMetersI']
    else:
        lengthM = c['lengthMetersM']
        heightM = c['heightMetersM']
        depthM = c['depthMetersM']
    left_margin = c['leftMargin']
    right_margin = scaleIt(lengthM - c['rightMargin'], 3)
    bottom_margin = c['bottomMargin']
    top_margin = c['topMargin']
    shear_sensors = scaleIt(heightM / 2, 3)
    midspan = scaleIt(lengthM / 2, 2)
    component = c['componentId']
    print(component)
    componentId = component
    side = c['side']
 
    layout = []
 
    sensorTypes = c['sensorTypes']

    # Make list of non-strain sensor numbers to skip during auto-layout of strain 
    skipList = []
    for  t in sensorTypes:
        if t["position"]=='custom':
            k = t['typeFirst']
            while k <= t['typeLast']:
                skipList.append(k)
                k += 1

    for t in sensorTypes:
        first = t['typeFirst']
        last = t['typeLast']
        sensorType = t['sensorType']
        position = t['position']
        desc = ''
        fromTop = 0
        fromLeft = 0
        sensorSpacing = 0
        fromRight = 0
        note = ''
        fiberNumber = c['fiberNumber']['value']
        if c.get('overrideFiberNumber') != None and c['overrideFiberNumber']['value'] != '':
            fiberNumber = c['overrideFiberNumber']['value']
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
                fromTop = scaleIt(y, 2)
                sensorSpacing = scaleIt(abs(x - fromLeft), 2)
                fromLeft = x
                fromRight = scaleIt(lengthM - x, 2)
                desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                layout.append(sensorRow(
                    fiberNumber,  i, componentId, sensorType, x, y, side, angle, desc, 
                    fromTop, fromLeft, sensorSpacing, fromRight, note))
                i += 1
        elif sensorType == 'strain':
            x = left_margin
            count = 0
            i = first
            while i <= last:
                if not i in skipList:
                    count += 1
                i += 1
            offset = scaleIt((right_margin - left_margin) / (count - 1), 3)
            ypos = 0
            if jinja_template == 'v1.1':
                if position.startswith('top'):
                    ypos = scaleIt(heightM - top_margin, 2)
                else:
                    ypos = bottom_margin
            else:
                if position.startswith('top'):
                    ypos = top_margin
                else:
                    ypos = scaleIt(heightM - bottom_margin, 2)

            if position == 'bottomR2L' or position == 'topR2L':
                x = right_margin
                offset = scaleIt((right_margin - left_margin) / (count - 1), 3) * -1

            fromTop = scaleIt(heightM - top_margin, 2)
            sensorSpacing = scaleIt(abs(x - fromLeft), 2)
            fromLeft = x
            fromRight = scaleIt(lengthM - x, 2)
            note = 'first'
            desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m - first'
            i = first
            while i <= last:
                if not i in skipList:
                    sensorSpacing = scaleIt(abs(x - fromLeft), 2)
                    fromLeft = x
                    fromRight = scaleIt(lengthM - x, 2)
                    desc = 'from Top: ' + str(fromTop) + ' mm - from Left End: ' + str(fromLeft) + ' m - from Right End: ' + str(fromRight) + ' m - Spacing: ' + str(sensorSpacing) + ' m'
                    if i == last:
                        desc += " - last"
                        note = "last"
                    if x == midspan:
                        desc += ' - midspan'
                        note = "midspan"
                    layout.append(sensorRow(
                            fiberNumber, i, componentId, sensorType, x, ypos, side, angle, desc, 
                            fromTop, fromLeft, sensorSpacing, fromRight, note))
                    x = scaleIt(x + offset, 3)
                    note = ''
                i += 1
        elif sensorType == 'rosette':
            print('add rosette')
            pos = right_margin
            if position == 'left':
                pos = left_margin
            fromTop = scaleIt(shear_sensors, 2)
            sensorSpacing = scaleIt(abs(lengthM - fromLeft), 2)
            fromLeft = pos
            fromRight = scaleIt(lengthM - pos, 2)
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
                    sensorRow(fiberNumber, i, componentId, sensorType, pos, shear_sensors, side, angle,
                          desc, fromTop, fromLeft, sensorSpacing, fromRight, note)
                        )
                i += 1
    return layout

def sensorRow (fiberNumber, sensor_id, componentId, sensorType, 
               x,  y, side, angle, desc, 
               fromTop, fromLeft, sensorSpacing, fromRight, note):
    return {
                "type": "sensor",
                "fiber": fiberNumber, 
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
                    "component_id": s['component_id'][-3:], \
                    "span": s['component_id'][0:3], \
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
            "component_id": s['component_id'][-3:], \
            "span": s['component_id'][0:3], \
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
        if s['sensor_type'] == 'strain':
            for i in range(index + 1, len(layout)):
                if layout[i]['component_id'] == s['component_id'] \
                    and layout[i]['x'] == s['x']:
                    bm_no += 1
                    bending_moment.append({"type": "algorithm", \
                        "id": "BM" + padIt(bm_no, 2), \
                        "algorithm_type": "girder_bending_moment", \
                        "fiber_id": s['fiber'], \
                        "component_id": s['component_id'][-3:], \
                        "span": s['component_id'][0:3], \
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
        if bm['component_id'] + bm['span'] != component_id:
            if component_id != "":
                def_no += 1
                deflection.append({"type": "algorithm", \
                    "id": "D" + padIt(def_no, 2), \
                    "algorithm_type": "girder_deflection", \
                    "fiber_id": fiber_id, \
                    "component_id": bm['component_id'], \
                    "span": bm['span'], \
                    "sensor_type": "sensor_pair_array",\
                    "sensors_top": top_sensors, \
                    "sensors_bottom": bottom_sensors})
            top_sensors = []
            bottom_sensors = []
            fiber_id = bm['fiber_id']
            component_id = bm['component_id'] + bm['span']
        top_sensors.append(bm['sensor_top'])
        bottom_sensors.append(bm['sensor_bottom'])
    # Last One
    if component_id != "":
        def_no += 1
        deflection.append({"type": "algorithm", \
            "id": "D" + padIt(def_no, 2), \
            "algorithm_type": "girder_deflection", \
            "fiber_id": fiber_id, \
            "component_id": component_id[-3:], \
            "span": component_id[0:3], \
            "sensor_type": "sensor_pair_array",\
            "sensors_top": top_sensors, \
            "sensors_bottom": bottom_sensors})
    return deflection

def scaleIt(value, scale):
    return round(value, scale)

def padIt(value, width):
    return ("0000" + str(value))[-width:]

