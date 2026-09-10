// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    // The collector ships inside the package so a KDE Store install works without
    // anything on PATH. It is run through python3 rather than executed directly,
    // because KPackage installs do not reliably preserve the executable bit.
    readonly property string helperCommand: {
        var path = Qt.resolvedUrl("../tools/limit-widget-helper").toString();
        path = decodeURIComponent(path.replace(/^file:\/\//, ""));
        return "python3 '" + path.replace(/'/g, "'\\''") + "' --json";
    }
    readonly property bool horizontalPanel: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
    readonly property int refreshSeconds: Math.max(60, Number(Plasmoid.configuration.refreshInterval) || 300)
    readonly property bool showUnsupported: Plasmoid.configuration.showUnsupported !== false
    // Ids the user has switched off, as a lookup rather than a repeated scan
    // of a comma-separated string for every provider on every repaint.
    readonly property var hiddenProviders: {
        var result = {};
        var raw = String(Plasmoid.configuration.hiddenProviders || "");
        raw.split(",").forEach(function (id) {
            var trimmed = id.trim();
            if (trimmed.length > 0) {
                result[trimmed] = true;
            }
        });
        return result;
    }

    function providerVisible(provider) {
        return !root.hiddenProviders[String(provider.id || "")];
    }

    property bool loading: false
    property string lastUpdated: ""
    property string errorText: ""
    property var providers: [
        defaultProvider("codex", "Codex / ChatGPT", "C", "codex-symbolic.svg", "https://chatgpt.com/settings/usage"),
        defaultProvider("claude", "Claude Code", "A", "claude-symbolic.svg", "https://claude.ai/settings/usage"),
        defaultProvider("copilot", "GitHub Copilot", "G", "copilot-symbolic.svg", "https://github.com/settings/copilot")
    ]

    readonly property var displayedProviders: providers.filter(function (provider) {
        if (!root.providerVisible(provider)) {
            return false;
        }
        return root.showUnsupported || provider.state === "ok" || provider.state === "stale";
    })
    // Providers discovered through the optional CodexBar CLI are shown in the
    // popup but kept out of the panel. There can be dozens of them, and the
    // panel representation grows with every row it draws, so including them
    // would push the rest of the panel off a normal-width screen.
    readonly property var panelProviders: providers.filter(function (provider) {
        return root.providerVisible(provider) && String(provider.id || "").indexOf("codexbar:") !== 0;
    })
    readonly property string statusLine: {
        var known = providers.filter(function (provider) {
            return typeof provider.remaining === "number" && typeof provider.limit === "number";
        }).length;
        if (root.loading) {
            return i18n("Updating limits…");
        }
        if (root.errorText) {
            return root.errorText;
        }
        return String(known) + " / " + String(providers.length) + " available";
    }
    readonly property string compactSummary: providers.map(function (provider) {
        var value = root.compactValue(provider);
        // The panel itself has no room for a word, so spell the direction out
        // wherever there is: an unlabelled "99%" reads as consumption.
        return provider.name + ": " + (value === "—" ? value : value + " " + i18n("left"));
    }).join("  ·  ")
    readonly property int compactWidth: 16 + providers.reduce(function (width, provider) {
        return width + root.compactProviderWidth(provider);
    }, 0) + Math.max(0, providers.length - 1) * 6;

    // Used in the widget picker and Plasma's generic applet UI. The custom
    // compact panel representation below intentionally does not render it.
    Plasmoid.icon: "view-statistics"
    toolTipMainText: i18n("AI limits")
    toolTipSubText: root.compactSummary + " — " + root.statusLine
    Plasmoid.status: root.loading ? PlasmaCore.Types.ActiveStatus : PlasmaCore.Types.PassiveStatus

    function defaultProvider(id, name, shortName, symbol, url) {
        return {
            "id": id,
            "name": name,
            "shortName": shortName,
            "symbol": symbol,
            "url": url,
            "state": "unsupported",
            "remaining": null,
            "limit": null,
            "detail": i18n("No local usage source configured")
        };
    }

    function formatTimestamp(value) {
        if (typeof value !== "string" || !value) {
            return "";
        }
        // The helper emits UTC with microsecond precision. ECMAScript's ISO
        // parser only defines three fractional digits, so trim before handing
        // it to Date; the result then renders in the local zone and locale.
        var parsed = new Date(value.replace(/(\.\d{3})\d+/, "$1"));
        if (isNaN(parsed.getTime())) {
            return value;
        }
        return parsed.toLocaleString(Qt.locale(), Locale.ShortFormat);
    }

    function remainingPercent(item) {
        if (!item) {
            return null;
        }
        // Claude and Codex report consumption as usedPercentage. Invert it
        // explicitly so every compact value means allowance remaining.
        if (typeof item.usedPercentage === "number") {
            return Math.max(0, Math.min(100, 100 - item.usedPercentage));
        }
        if (typeof item.remaining !== "number" || typeof item.limit !== "number" || item.limit <= 0) {
            return null;
        }
        return Math.max(0, Math.min(100, item.remaining / item.limit * 100));
    }

    function compactValue(provider) {
        var percentages = [];
        if (provider && provider.windows && typeof provider.windows.length === "number") {
            for (var index = 0; index < provider.windows.length; index++) {
                var windowPercent = root.remainingPercent(provider.windows[index]);
                if (windowPercent !== null) {
                    percentages.push(windowPercent);
                }
            }
        }
        if (percentages.length === 0) {
            var providerPercent = root.remainingPercent(provider);
            if (providerPercent !== null) {
                percentages.push(providerPercent);
            }
        }
        if (percentages.length > 0) {
            if (provider.id === "claude" && percentages.length > 1) {
                // Claude has one session window plus a weekly window per capped
                // model. Show the session value and the tightest weekly one, so
                // an Opus or Sonnet cap cannot hide behind the combined total.
                var weekly = Math.min.apply(null, percentages.slice(1));
                return String(Math.round(percentages[0])) + "%/" + String(Math.round(weekly)) + "%";
            }
            return String(Math.round(Math.min.apply(null, percentages))) + "%";
        }
        if (provider && typeof provider.detail === "string" && provider.detail.toLowerCase().indexOf("unlimited") !== -1) {
            return "100%";
        }
        return "—";
    }

    function compactProviderWidth(provider) {
        return 16 + 4 + Math.ceil(compactFontMetrics.advanceWidth(root.compactValue(provider))) + 4;
    }

    FontMetrics {
        id: compactFontMetrics
        font.pixelSize: 10
    }

    function refresh() {
        root.loading = true;
        root.errorText = "";
        helperSource.disconnectSource(root.helperCommand);
        helperSource.connectSource(root.helperCommand);
    }

    function acceptData(sourceName, data) {
        if (sourceName !== root.helperCommand) {
            return;
        }

        var stdout = data["stdout"] || "";
        if (!stdout) {
            root.loading = false;
            root.errorText = data["stderr"] || i18n("Helper is unavailable");
            return;
        }

        try {
            var payload = JSON.parse(String(stdout));
            if (!payload.providers || !Array.isArray(payload.providers)) {
                throw new Error("Invalid provider payload");
            }
            root.providers = payload.providers;
            // Record what exists so the settings page can offer a checkbox for
            // providers it could not otherwise enumerate, such as any that only
            // appear through CodexBar.
            // "," separates entries and "=" separates id from name, so strip
            // both from the name rather than let a vendor label corrupt the list.
            Plasmoid.configuration.lastProviderList = payload.providers.map(function (provider) {
                var label = String(provider.name || provider.id).replace(/[,=]/g, " ").trim();
                return String(provider.id) + "=" + label;
            }).join(",");
            root.lastUpdated = payload.fetchedAt || "";
            root.loading = false;
            root.errorText = "";
        } catch (error) {
            root.loading = false;
            root.errorText = i18n("Could not read usage data");
        }
    }

    Plasma5Support.DataSource {
        id: helperSource
        engine: "executable"
        connectedSources: []
        onNewData: function (sourceName, data) {
            root.acceptData(sourceName, data);
            disconnectSource(sourceName);
        }
    }

    Timer {
        id: refreshTimer
        interval: root.refreshSeconds * 1000
        repeat: true
        running: true
        onTriggered: root.refresh()
    }

    Component.onCompleted: root.refresh()

    compactRepresentation: Item {
        id: compact
        implicitWidth: root.horizontalPanel ? root.compactWidth : 38
        implicitHeight: root.horizontalPanel ? 28 : 94
        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: implicitHeight
        Accessible.name: "AI limits: " + root.compactSummary

        Rectangle {
            anchors.fill: parent
            radius: 5
            color: Kirigami.Theme.textColor
            opacity: compactMouse.containsMouse ? 0.12 : 0.06
        }

        RowLayout {
            visible: root.horizontalPanel
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 5

            Repeater {
                model: root.panelProviders
                delegate: RowLayout {
                    id: horizontalProvider
                    required property var modelData
                    Layout.preferredWidth: root.compactProviderWidth(horizontalProvider.modelData)
                    Layout.fillHeight: true
                    spacing: 3

                    Kirigami.Icon {
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                        source: Qt.resolvedUrl("../icons/" + horizontalProvider.modelData.symbol)
                        isMask: true
                        color: Kirigami.Theme.textColor
                        Accessible.name: horizontalProvider.modelData.name
                    }

                    QQC2.Label {
                        text: root.compactValue(horizontalProvider.modelData)
                        font.pixelSize: 10
                        color: Kirigami.Theme.textColor
                    }
                }
            }
        }

        ColumnLayout {
            visible: !root.horizontalPanel
            anchors.fill: parent
            anchors.margins: 4
            spacing: 2

            Repeater {
                model: root.panelProviders
                delegate: RowLayout {
                    id: verticalProvider
                    required property var modelData
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 3

                    Kirigami.Icon {
                        Layout.preferredWidth: 15
                        Layout.preferredHeight: 15
                        source: Qt.resolvedUrl("../icons/" + verticalProvider.modelData.symbol)
                        isMask: true
                        color: Kirigami.Theme.textColor
                        Accessible.name: verticalProvider.modelData.name
                    }

                    QQC2.Label {
                        text: root.compactValue(verticalProvider.modelData)
                        font.pixelSize: 9
                        color: Kirigami.Theme.textColor
                    }
                }
            }
        }

        MouseArea {
            id: compactMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.expanded = !root.expanded
        }
    }

    fullRepresentation: Item {
        id: popup
        implicitWidth: 382
        implicitHeight: 356
        Layout.minimumWidth: implicitWidth
        Layout.minimumHeight: implicitHeight

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Kirigami.Icon {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    source: "view-statistics"
                    isMask: true
                    color: Kirigami.Theme.textColor
                    Accessible.name: i18n("AI limits")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    QQC2.Label {
                        text: i18n("AI limits")
                        font.bold: true
                        font.pixelSize: 17
                    }
                    QQC2.Label {
                        text: root.statusLine
                        color: Kirigami.Theme.disabledTextColor
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                QQC2.Button {
                    id: refreshButton
                    text: i18n("Refresh")
                    icon.name: "view-refresh"
                    display: QQC2.AbstractButton.IconOnly
                    enabled: !root.loading
                    Accessible.name: i18n("Refresh AI limits")
                    onClicked: root.refresh()
                }
            }

            QQC2.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ColumnLayout {
                    width: popup.width - 32
                    spacing: 5

                    Repeater {
                        model: root.displayedProviders
                        delegate: ProviderRow {
                            required property var modelData
                            provider: modelData
                        }
                    }

                    QQC2.Label {
                        visible: root.displayedProviders.length === 0
                        Layout.fillWidth: true
                        text: i18n("No providers are enabled for display.")
                        color: Kirigami.Theme.disabledTextColor
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Kirigami.Theme.textColor
                opacity: 0.12
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                QQC2.Label {
                    Layout.fillWidth: true
                    text: root.lastUpdated
                        ? i18n("Updated %1", root.formatTimestamp(root.lastUpdated))
                        : i18n("Waiting for usage data")
                    color: Kirigami.Theme.disabledTextColor
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }
            }
        }
    }
}
