import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    id: root
    width: 420
    height: 520
    minimumWidth: 360
    minimumHeight: 440
    visible: true
    title: qsTr("Acc Hidden Profile")
    color: "#f5f5f5"

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Image {
            id: avatar
            anchors.horizontalCenter: parent.horizontalCenter
            width: 96
            height: 96
            source: "qrc:/images/avatar.svg"
            fillMode: Image.PreserveAspectFit
            smooth: true
            antialiasing: true
            Accessible.ignored: true
        }

        Text {
            id: nickname
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("微信用户")
            font.pixelSize: 20
            font.bold: true
            color: "#111111"
            wrapMode: Text.WordWrap
            Accessible.ignored: true
        }

        Text {
            id: bio
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("这是一段可见的正文内容。头像和昵称已从 Accessibility 树中隐藏，Inspect 等指明工具不应再看到这两个节点。")
            font.pixelSize: 14
            color: "#444444"
            lineHeight: 1.45
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.StaticText
            Accessible.name: text
            Accessible.description: qsTr("个人简介正文")
        }
    }
}
