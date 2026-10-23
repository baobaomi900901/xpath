import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    width: 1100; height: 820
    minimumWidth: 900; minimumHeight: 700
    visible: true
    title: "Qt " + qtVersion + " 靶场 - Quick / QML"
    font.family: "Microsoft YaHei UI"
    font.pixelSize: 14
    property string menuResult: "菜单测试: 尚未选择菜单项"
    property bool dragPageVisited: false
    function resetForm() {
        nameField.text = ""; passwordField.text = ""; emailField.text = ""
        ageField.value = 25; cityField.currentIndex = 0
        for (var i = 0; i < cityChecks.count; ++i) cityChecks.itemAt(i).checked = false
        for (var j = 0; j < hobbyChecks.count; ++j) hobbyChecks.itemAt(j).checked = false
        male.checked = true; remarkField.text = ""; agreement.checked = false
    }
    function resetFromMenu() { resetForm(); menuResult = "菜单测试: 重置表单" }
    function aboutFromMenu() { menuResult = "菜单测试: 关于靶场"; about.open() }
    menuBar: MenuBar {
        Menu {
            title: "文件"
            Action { text: "重置表单"; onTriggered: root.resetFromMenu() }
            MenuSeparator {}
            Action { text: "退出"; onTriggered: root.close() }
        }
        Menu {
            title: "编辑"
            Action { text: "重置表单"; onTriggered: root.resetFromMenu() }
            Menu { title: "更多操作"; Action { text: "关于靶场"; onTriggered: root.aboutFromMenu() } }
        }
    }
    Dialog {
        id: saved; objectName: "saveDialog"
        title: "提示"; modal: true; anchors.centerIn: parent
        standardButtons: Dialog.Ok
        Label { text: "提交成功"; Accessible.role: Accessible.StaticText; Accessible.name: text }
    }
    Dialog {
        id: about; title: "关于靶场"; modal: true; anchors.centerIn: parent
        standardButtons: Dialog.Ok
        Label { text: "Qt " + qtVersion + " Quick / QML RPA 靶场" }
    }
    Component {
        id: dynamicMenu
        Menu {
            objectName: "dynamicPopup"
            Action { text: "重置表单"; onTriggered: root.resetFromMenu() }
            Menu { title: "更多操作"; Action { text: "关于靶场"; onTriggered: root.aboutFromMenu() } }
            onClosed: destroy()
        }
    }
    header: TabBar {
        id: tabs; objectName: "tabs"
        onCurrentIndexChanged: {
            if (currentIndex === 2 && !root.dragPageVisited) {
                root.dragPageVisited = true
                Qt.callLater(function() { dragState.reset() })
            }
        }
        TabButton { text: "表单控件" }
        TabButton { text: "表格数据" }
        TabButton { text: "拖拽测试" }
    }
    StackLayout {
        anchors.fill: parent; anchors.margins: 20; currentIndex: tabs.currentIndex
        ScrollView {
            id: formScroll; clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: formScroll.availableWidth; spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "用户信息表单"; font.pixelSize: 22; font.bold: true; Layout.fillWidth: true }
                    Button { Accessible.onPressAction: clicked(); objectName: "popupMenu"; text: "展开 Qt 菜单 ▼"; onClicked: { var menu = dynamicMenu.createObject(this); menu.popup(0, height) } }
                }
                Label { text: root.menuResult }
                GridLayout {
                    columns: 2; rowSpacing: 10; columnSpacing: 24; Layout.fillWidth: true
                    Label { text: "姓名"; Layout.preferredWidth: 145 }
                    TextField { id: nameField; objectName: "name"; Layout.fillWidth: true; Accessible.name: "姓名" }
                    Label { text: "密码" }
                    TextField { id: passwordField; objectName: "password"; echoMode: TextInput.Password; Layout.fillWidth: true; Accessible.name: "密码" }
                    Label { text: "邮箱" }
                    TextField { id: emailField; objectName: "email"; Layout.fillWidth: true; Accessible.name: "邮箱" }
                    Label { text: "年龄" }
                    SpinBox { id: ageField; objectName: "age"; from: 18; to: 80; value: 25; editable: true; Accessible.name: "年龄" }
                    Label { text: "城市（单选）" }
                    ComboBox { id: cityField; objectName: "city"; model: ["北京","上海","广州","深圳","杭州"]; Accessible.name: "城市（单选）" }
                    Label { text: "城市（多选）" }
                    RowLayout {
                        Accessible.role: Accessible.Grouping; Accessible.name: "城市（多选）"
                        Repeater { id: cityChecks; model: ["北京","上海","广州","深圳","杭州"]
                            CheckBox { text: modelData; objectName: "cityCheck" + index; Accessible.name: text } }
                    }
                    Label { text: "性别（单选）" }
                    RowLayout {
                        Accessible.role: Accessible.Grouping; Accessible.name: "性别（单选）"
                        RadioButton { id: male; text: "男"; checked: true }
                        RadioButton { text: "女" }
                        RadioButton { text: "其他" }
                    }
                    Label { text: "兴趣爱好（多选）" }
                    RowLayout {
                        Accessible.role: Accessible.Grouping; Accessible.name: "兴趣爱好（多选）"
                        Repeater { id: hobbyChecks; model: ["阅读","运动","音乐","旅行"]
                            CheckBox { text: modelData; objectName: "hobby" + index; Accessible.name: text } }
                    }
                    Label { text: "备注" }
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 85
                        color: "white"; border.color: "#b9c3ce"
                        ScrollView {
                            anchors.fill: parent; anchors.margins: 1
                            TextArea { id: remarkField; objectName: "remark"; wrapMode: TextEdit.Wrap; Accessible.name: "备注" }
                        }
                    }
                    Label { text: "协议" }
                    CheckBox { id: agreement; objectName: "agreement"; text: "同意用户协议" }
                }
                RowLayout {
                    Button { Accessible.onPressAction: clicked(); objectName: "save"; text: "保存"; onClicked: saved.open() }
                    Button { Accessible.onPressAction: clicked(); objectName: "reset"; text: "重置"; onClicked: root.resetForm() }
                }
            }
        }
        ColumnLayout {
            spacing: 12
            Label { text: "员工数据表格"; font.pixelSize: 22; font.bold: true }
            // Seven columns rendered by QML delegates, intentionally distinct
            // from the native item-view accessibility in the Widgets build.
            Rectangle {
                id: table; Layout.fillWidth: true; Layout.fillHeight: true
                color: "#ffffff"; border.color: "#ced8e3"
                property var widths: [0.06,0.12,0.12,0.10,0.10,0.26,0.24]
                Row {
                    id: tableHeader; width: parent.width; height: 38
                    Repeater {
                        model: ["ID","姓名","部门","城市","状态","邮箱","入职日期"]
                        Rectangle {
                            width: table.width * table.widths[index]; height: 38; color: "#eaf1f9"
                            Label { anchors.fill: parent; anchors.leftMargin: 9; verticalAlignment: Text.AlignVCenter; text: modelData; font.bold: true }
                        }
                    }
                }
                ListView {
                    objectName: "employeeTable"; anchors.top: tableHeader.bottom; anchors.bottom: parent.bottom
                    width: parent.width; clip: true; model: employees.rows
                    ScrollBar.vertical: ScrollBar {}
                    Accessible.name: "员工数据表格"; Accessible.role: Accessible.List
                    delegate: Rectangle {
                        id: employeeRow
                        property var cells: modelData
                        width: table.width; height: 34; color: index % 2 ? "#f5f8fc" : "#ffffff"
                        Row {
                            Repeater {
                                model: employeeRow.cells
                                Label {
                                    width: table.width * table.widths[index]; height: 34
                                    leftPadding: 9; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                                    text: modelData; Accessible.role: Accessible.StaticText; Accessible.name: text
                                }
                            }
                        }
                    }
                }
            }
            Label { text: employees.pageInfo }
            RowLayout {
                Button { Accessible.onPressAction: clicked(); text: "首页"; enabled: employees.page > 1; onClicked: employees.setPage(1) }
                Button { Accessible.onPressAction: clicked(); text: "上一页"; enabled: employees.page > 1; onClicked: employees.setPage(employees.page - 1) }
                Repeater { model: employees.pageNumbers
                    Button { Accessible.onPressAction: clicked(); text: modelData; enabled: employees.page !== modelData; onClicked: employees.setPage(modelData) } }
                Button { Accessible.onPressAction: clicked(); objectName: "nextPage"; text: "下一页"; enabled: employees.page < 50; onClicked: employees.setPage(employees.page + 1) }
                Button { Accessible.onPressAction: clicked(); objectName: "lastPage"; text: "末页"; enabled: employees.page < 50; onClicked: employees.setPage(50) }
            }
        }
        ColumnLayout {
            spacing: 16
            Label { text: "拖拽 drag-target，记录位移、锚点、移动次数和耗时；delay_after 由调用方统计。" }
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 20
                ColumnLayout {
                    Layout.preferredWidth: 340; Layout.alignment: Qt.AlignTop
                    Label { text: dragState.summary; lineHeight: 1.4 }
                    Label { text: dragState.status; Layout.topMargin: 12 }
                    Button { Accessible.onPressAction: clicked(); objectName: "resetTarget"; text: "重置位置"; onClicked: dragState.reset() }
                    Button { Accessible.onPressAction: clicked(); objectName: "hideTarget"; text: "隐藏 drag-target"; enabled: dragState.visible; onClicked: dragState.hide() }
                    Button { Accessible.onPressAction: clicked(); objectName: "copyResult"; text: "复制当前结果"; onClicked: dragState.copy() }
                }
                Rectangle {
                    id: arena; objectName: "dragArena"
                    Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 360; Layout.minimumHeight: 340
                    color: "#edf4fc"; border.color: "#c7d8ee"; clip: true
                    onWidthChanged: dragState.setArea(width, height)
                    onHeightChanged: dragState.setArea(width, height)
                    Loader {
                        id: targetLoader; objectName: "targetLoader"
                        active: dragState.visible
                        x: dragState.left; y: dragState.top; width: 120; height: 80
                        sourceComponent: Rectangle {
                            objectName: "drag-target"; color: "#2474d2"; radius: 6
                            Accessible.role: Accessible.Button; Accessible.name: "drag-target"
                            Label { anchors.centerIn: parent; text: "drag-target"; color: "white"; Accessible.ignored: true }
                            MouseArea {
                                anchors.fill: parent
                                onPressed: function(mouse) { dragState.begin(mouse.x, mouse.y) }
                                onPositionChanged: function(mouse) { if (pressed) { var p = mapToItem(arena, mouse.x, mouse.y); dragState.move(p.x, p.y) } }
                                onReleased: function(mouse) { var p = mapToItem(arena, mouse.x, mouse.y); dragState.move(p.x, p.y); dragState.end() }
                                onCanceled: dragState.end()
                            }
                        }
                    }
                }
            }
        }
    }
    footer: Label { text: "Qt " + qtVersion + " · Quick Controls 2 / QML"; padding: 8; color: "#526173" }
}
