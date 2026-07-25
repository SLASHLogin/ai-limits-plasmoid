import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami

Item {
    id: row

    required property var provider
    property bool compact: false

    readonly property var windows: provider && provider.windows && typeof provider.windows.length === "number"
        ? provider.windows
        : []
    readonly property bool hasValue: provider
        && typeof provider.remaining === "number"
        && typeof provider.limit === "number"
        && provider.limit > 0
    readonly property real ratio: hasValue
        ? Math.max(0, Math.min(1, provider.remaining / provider.limit))
        : 0

    implicitHeight: row.compact ? 24 : (row.windows.length > 1 ? 78 : 66)
    Layout.fillWidth: true
    Layout.minimumHeight: implicitHeight

    function windowSummary() {
        var values = row.windows.map(function (item) {
            var value = row.provider.id === "claude" && typeof item.usedPercentage === "number"
                ? item.usedPercentage
                : item.remaining;
            var displayed = typeof value === "number" ? String(Math.round(value)) : "—";
            var suffix = Number(item.limit) === 100 ? "%" : "";
            return (item.label || qsTr("Window")) + " " + displayed + suffix;
        }).join("  ·  ");
        return row.provider.id === "claude" ? qsTr("Used: ") + values : values;
    }

    function resetSummary() {
        var resets = [];
        var candidates = row.windows.length > 0 ? row.windows : [row.provider];
        for (var index = 0; index < candidates.length; index++) {
            var item = candidates[index];
            if (!item || typeof item.resetAt !== "string" || !item.resetAt) {
                continue;
            }
            var resetDate = new Date(item.resetAt);
            var timestamp = resetDate.getTime();
            if (isNaN(timestamp) || timestamp <= Date.now()) {
                continue;
            }
            var delta = timestamp - Date.now();
            var formatted = delta < 24 * 60 * 60 * 1000
                ? Qt.formatDateTime(resetDate, "HH:mm")
                : Qt.formatDateTime(resetDate, "d MMM HH:mm");
            var label = row.windows.length > 1 ? (item.label || qsTr("Window")) + " " : "";
            resets.push(label + formatted);
        }
        return resets.length > 0 ? qsTr("Next reset: ") + resets.join(" · ") : "";
    }

    Kirigami.Icon {
        id: providerIcon
        anchors.left: parent.left
        anchors.leftMargin: row.compact ? 0 : 2
        anchors.verticalCenter: parent.verticalCenter
        width: row.compact ? 16 : 28
        height: width
        source: Qt.resolvedUrl("../icons/" + (row.provider.symbol || "codex-symbolic.svg"))
        isMask: true
        color: Kirigami.Theme.textColor
        Accessible.name: row.provider.name || "AI provider"
    }

    ColumnLayout {
        anchors.left: providerIcon.right
        anchors.leftMargin: row.compact ? 7 : 12
        anchors.right: row.compact ? parent.right : usageButton.left
        anchors.rightMargin: row.compact ? 0 : 8
        anchors.verticalCenter: parent.verticalCenter
        spacing: row.compact ? 0 : 3

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            QQC2.Label {
                Layout.fillWidth: true
                text: row.provider.name || "AI provider"
                font.bold: !row.compact
                font.pixelSize: row.compact ? 11 : 13
                elide: Text.ElideRight
            }

            QQC2.Label {
                visible: row.hasValue
                text: row.windows.length > 1
                    ? row.windowSummary()
                    : (row.hasValue
                        ? String(row.provider.remaining) + " / " + String(row.provider.limit)
                        : qsTr("—"))
                font.bold: true
                font.pixelSize: row.windows.length > 1 ? 11 : (row.compact ? 11 : 13)
                horizontalAlignment: Text.AlignRight
                Accessible.name: row.hasValue ? text : qsTr("Limit unavailable")
            }
        }

        Rectangle {
            visible: !row.compact && row.hasValue && row.windows.length <= 1
            Layout.fillWidth: true
            Layout.preferredHeight: 3
            radius: 2
            color: Kirigami.Theme.textColor
            opacity: 0.14

            Rectangle {
                width: parent.width * row.ratio
                height: parent.height
                radius: parent.radius
                color: Kirigami.Theme.textColor
                opacity: 0.82
            }
        }

        QQC2.Label {
            visible: !row.compact
            Layout.fillWidth: true
            text: row.resetSummary() || (row.hasValue
                ? (row.provider.detail || qsTr("Remaining"))
                : (row.provider.detail || qsTr("No official remaining-limit data")))
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            elide: Text.ElideRight
            maximumLineCount: 1
        }
    }

    QQC2.Button {
        id: usageButton
        visible: !row.compact && !!row.provider.url
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: 54
        height: 28
        display: QQC2.AbstractButton.TextOnly
        flat: true
        text: i18n("Usage")
        Accessible.name: "Open " + row.provider.name + " usage website"
        onClicked: Qt.openUrlExternally(row.provider.url)
        QQC2.ToolTip.visible: usageButton.hovered
        QQC2.ToolTip.text: "Open " + row.provider.name + " usage website"
        QQC2.ToolTip.delay: 500
    }
}
