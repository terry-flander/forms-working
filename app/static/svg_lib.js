/* 
    SVG routines for drawing asset components, sensors, and fibres and adding dimenstions, etc.
    (Scalable Vector Graphics https://developer.mozilla.org/en-US/docs/Web/SVG)

*/
function add_fiber(fiber_id, count) {
    let textx = 0;
    let texty = 60 + (count * 210);

    addText(textx, texty, fiber_id, 'font-size: 24; font-family: sans-serif; fill: black; stroke: none; text-anchor: left', '');
}

function add_component(component_id, type, count, length, height) {
    let rectx = 50;
    let recty = 100 + (count * 210);
    let textx = 100;
    let texty = 60 + (count * 210);
    let clength = 900;
    let cwidth = 90;
    let abutment = new RegExp('^Abutment');
    if (abutment.test(type)) {
        clength = 400;
        cwidth = 100;
    }

    // addRectangle(rectx - 25, recty - 10, 950, 105, '#b0b0b0', '');
    addRectangle(rectx, recty, clength, cwidth, '#a0a0a0', '');
    addDimension(rectx, recty, clength, cwidth, true, length, '');
    addDimension(rectx, recty, clength, cwidth, false, height, '');
    addText(textx, texty, component_id, 'font-size: 24; font-family: sans-serif; fill: black; stroke: none; text-anchor: left', '');
}

function add_sensor(fiber_id, x, y, number, type, angle, count, scalex, scaley, origin, side) {
    let sensorx = ((x * 100) + 50) * scalex;
    let sensory = ((190 - (origin * 100) * scaley) + (count * 210));
    let textx = ((x * 100) + 50) * scalex;
    let texty = ((190 - (origin * 100) * scaley) + 30 + (count * 210));
    let textxyoffset = texty + 20;
    let anglex = 0;
    let angley = 0;
    let posx = textx + 10;
    let posy = texty + 20;
    if (origin > 0.1 && type == 'strain') {
        texty = sensory - 20;
        posy = texty - 20;
        textxyoffset = texty - 20;
    }
    let font = 18;
    if (type == "temperature") {
        anglex = 10;
    } else if (type == "strain") {
        anglex = 20;
    } else {
        font = 12;
        if (angle == 0) {
            anglex = 10;
            texty -= 5;
        } else if (angle == 90) {
            angley = -10;
            texty -= 50;
        } else {
            anglex = 12;
            angley = -12;
            textx += 20;
            texty -= 40;
        }
    }
    let sensor_id = fiber_id + number;
    if (type == 'rosette' && angle != 0) {
        sensor_id += '-skip';
    }
    let color = 'black';
    if (side === 'top') {
        color = 'blue';
    } else if (side === 'bottom_down') {
        color = 'orange';
    } else if (side === 'bottom_up') {
        color = 'green';
    }

    sensor = addLine(sensor_id, sensorx, sensory, sensorx + anglex, sensory + angley, 'stroke: ' + color + '; stroke-width: 5; fill: none');
    addText(textx, texty, number, 'font-size: ' + font + '; font-family: sans-serif; fill: black; stroke: none; text-anchor: middle', '');
    if (type == 'rosette' && angle == 0) {
        addText(sensorx + 50, sensory, '(' + x + 'm, ' + y + 'm)', 'font-size: 10; font-family: sans-serif; fill: black; stroke: none; text-anchor: middle', '');
    } else if (type != 'rosette') {
        addText(textx, textxyoffset, '(' + x + 'm, ' + y + 'm)', 'font-size: 10; font-family: sans-serif; fill: black; stroke: none; text-anchor: middle', '');
    }
}

function add_image(src, count, x, y) {
    let svgns = "http://www.w3.org/2000/svg";
    let container = document.getElementById( 'cont' );
    let r = document.createElementNS(svgns, 'image');
    let posx = (900) + 150;
    let posy = ((y * 100) + 30) + (count * 210);
    r.setAttributeNS(null, 'x',posx);
    r.setAttributeNS(null, 'y',posy);
    r.setAttributeNS(null, 'height',"150px");
    r.setAttributeNS(null, 'width',"150px");
    r.setAttributeNS(null, 'href', src);
    container.appendChild(r);
}

function draw_fiber(fiber_id) {
    let container = document.getElementById( 'cont' );
    let last_sensor = null;
    for (let i = 1; i <= 25; i++) {
        let this_id = fiber_id + i;
        let this_sensor = document.getElementById(this_id);
        if (this_sensor != null) {
            if (last_sensor != null) {
                let x1 = last_sensor.getAttribute('x1');
                let y1 = last_sensor.getAttribute('y1');
                let x2 = this_sensor.getAttribute('x1');
                let y2 = this_sensor.getAttribute('y1');
                if (y1 == y2) {
                    addLine(last_sensor.id, x1, y1, x2, y2, 'stroke: green; stroke-width: 2; fill: none');
                } else {
                    addLine(last_sensor.id, x1, y1, x1, y2, 'stroke: green; stroke-width: 2; fill: none');
                    addLine(last_sensor.id, x1, y2, x2, y2, 'stroke: green; stroke-width: 2; fill: none');
                }
                container.appendChild(last_sensor);
                container.appendChild(this_sensor);
            }
            last_sensor = this_sensor;
        }
    }
}

function addRectangle(x, y, width, height, fill, style) {
    let svgns = "http://www.w3.org/2000/svg";
    let container = document.getElementById( 'cont' );
    let r = document.createElementNS(svgns, 'rect');
    r.setAttributeNS(null, 'x',x);
    r.setAttributeNS(null, 'y',y);
    if (style == '') {
        style = 'width: ' + width + '; height: ' + height + '; fill: ' + fill + '; stroke-width: 0; stroke: none';
    }
    r.setAttributeNS(null, 'style', style);
    container.appendChild(r);
}

function addLine(id, x1, y1, x2, y2, style) {
    let svgns = "http://www.w3.org/2000/svg";
    let container = document.getElementById( 'cont' );
    let l = document.createElementNS(svgns, 'line');
    l.setAttributeNS( null, 'id', id);
    l.setAttributeNS(null, 'x1', x1);
    l.setAttributeNS(null, 'y1', y1);
    l.setAttributeNS(null, 'x2', x2);
    l.setAttributeNS(null, 'y2', y2);
    l.setAttributeNS(null, 'style', style);
    container.appendChild(l);
    return l;
}

function addText(x, y, text, style, rotate) {
    let svgns = "http://www.w3.org/2000/svg";
    let container = document.getElementById( 'cont' );
    let t = document.createElementNS(svgns, 'text');
    t.setAttributeNS(null, 'x', x);
    t.setAttributeNS(null, 'y', y);
    t.textContent=text
    t.setAttributeNS(null, 'style', style);
    if (rotate != '') {
        t.setAttributeNS(null, 'transform', rotate);
    }
    container.appendChild(t);
}

function addDimension(x, y, length, width, horizontal, text, style) {
    if (horizontal) {
        x2 = x + length;
        y = y - 20;
        y2 = y;
        xt = x + (length / 2);
        yt = y - 20;
    } else {
        x = x - 20;
        x2 = x;
        y2 = y + width;
        xt = y + (width / 2);
        yt = (x - 30) * -1;
    }
    if (style == '') {
        style = 'stroke: grey; stroke-width: 1; fill: none';
    }
    addLine('dim' + x + y, x, y, x2, y2, style);
    addArrowHeads(x, y, length, width, horizontal);
    let rotate = '';
    if (!horizontal) {
        rotate = 'rotate(90)';
    }
    addText(xt, yt, text + ' m', 'font-size: 24; font-family: sans-serif; fill: orange; stroke: none; text-anchor: middle', rotate);
    if (horizontal) {
        addLine('mid' + xt, xt, yt - 10, xt, yt + width + 30, 'stroke: grey; stroke-width: 1; stroke-dasharray: "50", fill: none');
        addText(xt, yt + 35, 'midspan', 'font-size: 14; font-family: sans-serif; fill: grey; stroke: none; text-anchor: middle', '');
    }
}

function addArrowHeads(x, y, length, width, horizontal) {
    if (horizontal) {
        addLine('arrowl' + x, x, y, x + 10, y - 10, 'stroke: grey; stroke-width: 1; fill: none');
        addLine('arrowr' + x, x, y, x + 10, y + 10, 'stroke: grey; stroke-width: 1; fill: none');
        x = x + length;
        addLine('arrowl' + x, x, y, x - 10, y - 10, 'stroke: grey; stroke-width: 1; fill: none');
        addLine('arrowr' + x, x, y, x - 10, y + 10, 'stroke: grey; stroke-width: 1; fill: none');
    } else {
        addLine('arrowl' + x, x, y, x - 10, y + 10, 'stroke: grey; stroke-width: 1; fill: none');
        addLine('arrowr' + x, x, y, x + 10, y + 10, 'stroke: grey; stroke-width: 1; fill: none');
        y = y + width;
        addLine('arrowl' + y, x, y, x + 10, y - 10, 'stroke: grey; stroke-width: 1; fill: none');
        addLine('arrowr' + y, x, y, x - 10, y - 10, 'stroke: grey; stroke-width: 1; fill: none');
    }
}
