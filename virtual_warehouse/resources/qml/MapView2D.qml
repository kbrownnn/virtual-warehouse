import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Controls.Material 2.14

Canvas {
    id: mapView2D
    width: contentView.width
    height: contentView.height
    anchors.top: contentView.top
    anchors.left: contentView.left
    visible: true;

    // handler to override for drawing
    onPaint: {
        var ctx = getContext("2d");
        // background
        ctx.fillStyle = "#4d4d4f"
        ctx.fillRect(0, 0, width, height);

        // Drawing items
        var min_x = ViewController.map.min_x;
        var min_y = ViewController.map.min_y;
        var params = getDrawParams();
        var item, heat;

        // Draw selected item
        var idx = ViewController.get_selected_idx();
        if (idx >= 0) {
            item = ViewController.model2D.get(idx);
            ctx.fillStyle = "red";
            ctx.fillRect(
                        (item.x - min_x) * params.coef + params.padding_x,
                        (item.y - min_y) * params.coef + params.padding_y,
                        item.width * params.coef,
                        item.length * params.coef);
        }

        // TODO: speed up drawing - sort by z coordinate?
        // Draw Floor first
        for (var row = 0; row < ViewController.model2D.rowCount(); row++) {
            if (row === idx) {
                continue;
            }

            item = ViewController.model2D.get(row);

            if (item.type === "floor") {
                ctx.fillStyle = item.color;
                ctx.fillRect(
                            (item.x - min_x) * params.coef + params.padding_x,
                            (item.y - min_y) * params.coef + params.padding_y,
                            item.width * params.coef,
                            item.length * params.coef);
            }
        }

        // Draw rest of the items
        var max = ViewController.model2D.max_heat;
        if (ViewController.model2D.level !== -1) {
            max = ViewController.model3D.max_heat;
        }

        for (row = 0; row < ViewController.model2D.rowCount(); row++) {
            if (row === idx) {
                continue;
            }

            item = ViewController.model2D.get(row);

            if (item.type !== "floor") {
                ctx.fillStyle = item.color;
                if (ViewController.is_heatmap) { // is_heatmap() in future
                    if (item.type === "rack") {
                        heat = ViewController.model2D.get_heat(row, max);
                        ctx.fillStyle = heat;
                    } else {
                        ctx.fillStyle = item.gray_color;
                    }
                }

                ctx.fillRect(
                            (item.x - min_x) * params.coef + params.padding_x,
                            (item.y - min_y) * params.coef + params.padding_y,
                            item.width * params.coef,
                            item.length * params.coef);
            }
        }
    }

    Rectangle {
        id: sideView
        height: parent.height * 0.6
        width: 200
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 20
        anchors.leftMargin: 20
        color: "transparent"

        ListView {
           id: sideViewList
           anchors.fill: sideView
           anchors.bottomMargin: -20
           clip: true
           spacing: 1

           model: ViewController.sidebar_model

           delegate: Item {
               id: sideViewItem
               height: Math.floor(sideView.height / sideViewList.count)
               width: sideView.width

               Rectangle {
                   id: sideViewRect
                   color: model.object.heat(ViewController.model3D.max_heat)
                   anchors.top:  parent.top
                   anchors.topMargin: 0
                   anchors.leftMargin: 0
                   anchors.left: parent.left
                   width: 40
                   height: parent.height
               }

               Rectangle {
                   id: sideViewLine
                   height: 1
                   width: 20
                   color: model.object.heat(ViewController.model3D.max_heat)

                   anchors.bottom:  sideViewRect.bottom
                   anchors.left: sideViewRect.right
               }

               Text {
                   id: sideViewItemHeight
                   text: model.object.z
                   anchors.left: sideViewLine.right
                   anchors.bottom:  sideViewLine.bottom
                   horizontalAlignment: Text.AlignLeft
                   anchors.bottomMargin: -4
                   anchors.leftMargin: 4
                   font.pixelSize: 12
                   color: model.object.heat(ViewController.model3D.max_heat)
               }
           }
        }
    }

    Rectangle {
        radius: 5
        border.width: 0

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: -5
        Behavior on height { NumberAnimation{} }
        height: (levelSwitch.checked ? 200 : 20) + 80
        width: levelSlider.width + 40
        visible: ViewController.is_heatmap && ViewController.is2D
        z: 10


        Rectangle {
            id: titleBackground
            color: Material.primary
            anchors.top: parent.top
            anchors.topMargin: -3
            width: parent.width + 1
            height: levelTitle.height + levelSwitch.height
            radius: parent.radius
            z: 1


            Text {
                id: levelTitle
                text: "Levels"
                color: "white"
                font.bold: true
                visible: levelSlider.visible
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: 4

            }

            Switch {
                id: levelSwitch
                padding: 0
                scale: 0.65
                display: AbstractButton.IconOnly
                checked: false
                anchors.top: levelTitle.bottom
                anchors.horizontalCenter: parent.horizontalCenter

                onClicked: {
                    if (checked) {
                        ViewController.model2D.level = levelSlider.value;
                    } else {
                        ViewController.model2D.level = -1;
                    }
                    mapView2D.requestPaint();
                }
            }
        }

        Rectangle {
            color: titleBackground.color
            height: titleBackground.radius
            anchors.left: titleBackground.left
            anchors.right: titleBackground.right
            anchors.bottom: titleBackground.bottom
        }

        Text {
            id: levelIndication
            color: Material.accent

            visible: levelSlider.visible
            anchors.top: titleBackground.bottom
            anchors.topMargin: 4
            anchors.horizontalCenter: levelSlider.horizontalCenter
            text: (levelSwitch.checked) ? Number(levelSlider.value).toString() : "All"
        }


        Slider {
            id: levelSlider
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 8
            Behavior on height { NumberAnimation{} }
            height: levelSwitch.checked ? 200 : 20

            visible: ViewController.is_heatmap && ViewController.is2D
            enabled: levelSwitch.checked

            live: true
            Material.theme: Material.Light
            // Material.accent: "white"
            orientation: Qt.Vertical
            snapMode: Slider.SnapAlways
            // Only model3D correctly set max Z coordinate right now
            to: ViewController.model3D.max_level
            from: 0
            value: -1
            stepSize: 1

            onMoved: {
                if (levelSwitch.checked) {
                    ViewController.model2D.level = value;
                    mapView2D.requestPaint();
                }
            }
        }


    }


    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        onPressed: {
            var min_x = ViewController.map.min_x;
            var min_y = ViewController.map.min_y;
            var params = getDrawParams();
            var x1, y1, x2, y2;

            for (var row = 0; row < ViewController.model2D.rowCount(); row++) {
                var item = ViewController.model2D.get(row);
                if (item.type === "rack") {
                    x1 = (item.x - min_x) * params.coef + params.padding_x;
                    y1 = (item.y - min_y) * params.coef + params.padding_y;
                    x2 = x1 + item.width * params.coef;
                    y2 = y1 + item.length * params.coef;
                    if (x1 <= mouseX && mouseX <= x2 &&
                            y1 <= mouseY && mouseY <= y2) {
                        ViewController.select_item(row);
                        // TODO: Speed up drawing - extra canvas, less items...
                        mapView2D.requestPaint()
                        return;
                    }
                }
            }

            ViewController.select_item(-1);
        }

        onPositionChanged: {
            var min_x = ViewController.map.min_x;
            var min_y = ViewController.map.min_y;
            var params = getDrawParams();
            var x1, y1, x2, y2;

            for (var row = 0; row < ViewController.model2D.rowCount(); row++) {
                var item = ViewController.model2D.get(row);
                if (item.type === "rack") {
                    x1 = (item.x - min_x) * params.coef + params.padding_x;
                    y1 = (item.y - min_y) * params.coef + params.padding_y;
                    x2 = x1 + item.width * params.coef;
                    y2 = y1 + item.length * params.coef;
                    if (x1 <= mouseX && mouseX <= x2 &&
                            y1 <= mouseY && mouseY <= y2) {
                        ViewController.hover_item(row);
                        return;
                    }
                }
            }
            ViewController.hover_item(-1);
        }
    }

    Connections {
        target: ViewController
        function onModelChanged() {
            mapView2D.requestPaint();
        }
        function onDrawModeChanged() {
            mapView2D.requestPaint();
        }
    }

    function getDrawParams() {
        // Get size coefficient and paddings
        var coef, padding_x = 20, padding_y = 20;

        var min_x = ViewController.map.min_x;
        var min_y = ViewController.map.min_y;

        var width = (ViewController.map.max_x - ViewController.map.min_x);
        var height = (ViewController.map.max_y - ViewController.map.min_y);

        var coef_x = (mapView2D.width - 2 * padding_x) / width;
        var coef_y = (mapView2D.height - 2 * padding_y) / height;

        if (coef_x < coef_y) {
            coef = coef_x;
            padding_y = (mapView2D.height - coef * height) / 2;
        } else {
            coef = coef_y;
            padding_x = (mapView2D.width - coef * width) / 2;
        }

        return {
            coef: coef,
            padding_x: padding_x,
            padding_y: padding_y,
        };
    }

    function getHeatColor(heat, string=true) {
        var h = Math.floor((1.0 - heat) * 240);
        if (string)
            return "hsl(" + h + ", 100%, 50%)";
        return Qt.hsla(h / 360.0, 1, 0.5, 1);


//        var h = Math.floor(heat * 255);
//        return "rgb( 0," + h + "," + h + ")";
    }
}

/*##^##
Designer {
    D{i:0;formeditorZoom:0.01}
}
##^##*/