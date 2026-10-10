// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
Kirigami.FormLayout {
    id: page

    property alias cfg_refreshInterval: refreshInterval.value
    property alias cfg_showUnsupported: showUnsupported.checked
    property alias cfg_hideEmptyProviders: hideEmptyProviders.checked
    property alias cfg_showExhaustedReset: showExhaustedReset.checked
    property alias cfg_resetTextFormat: resetTextFormat.currentValue
    // Not aliases: the checkbox list and the order buttons write these as
    // comma-separated strings.
    property string cfg_hiddenProviders: ""
    property string cfg_providerOrder: ""
    property alias cfg_codexbarPath: codexbarPath.text

    // The provider list is whatever the collector last reported, so providers
    // that only exist through CodexBar can be switched off here too.
    readonly property var knownProviders: {
        var seen = {};
        var list = [];
        var reported = Plasmoid.configuration.lastProviderList || "";
        String(reported).split(",").forEach(function (pair) {
            var split = pair.indexOf("=");
            var id = (split === -1 ? pair : pair.slice(0, split)).trim();
            var name = split === -1 ? "" : pair.slice(split + 1).trim();
            if (id.length > 0 && !seen[id]) {
                seen[id] = true;
                list.push({ id: id, name: name.length > 0 ? name : id });
            }
        });
        return list;
    }

    function isHidden(id) {
        return page.cfg_hiddenProviders.split(",").map(function (value) {
            return value.trim();
        }).indexOf(id) !== -1;
    }

    function setHidden(id, hidden) {
        var current = page.cfg_hiddenProviders.split(",").map(function (value) {
            return value.trim();
        }).filter(function (value) {
            return value.length > 0 && value !== id;
        });
        if (hidden) {
            current.push(id);
        }
        page.cfg_hiddenProviders = current.join(",");
    }

    // The ids in their pinned order: what the pin lists first, then the ids
    // it does not mention in the collector's order — so a newly reported
    // provider lands at the end instead of going missing.
    readonly property var orderedKnownIds: {
        var seen = {};
        var list = [];
        page.cfg_providerOrder.split(",").forEach(function (id) {
            var trimmed = id.trim();
            if (trimmed.length > 0 && !seen[trimmed]) {
                seen[trimmed] = true;
                list.push(trimmed);
            }
        });
        page.knownProviders.forEach(function (provider) {
            if (!seen[provider.id]) {
                seen[provider.id] = true;
                list.push(provider.id);
            }
        });
        return list;
    }

    function providerName(id) {
        for (var index = 0; index < page.knownProviders.length; index++) {
            if (page.knownProviders[index].id === id) {
                return page.knownProviders[index].name;
            }
        }
        return id;
    }

    // Moving a row writes the whole order, so the arrows always mean what
    // they show.
    function moveProvider(id, offset) {
        var ids = page.orderedKnownIds.slice();
        var index = ids.indexOf(id);
        var target = index + offset;
        if (index === -1 || target < 0 || target >= ids.length) {
            return;
        }
        ids[index] = ids[target];
        ids[target] = id;
        page.cfg_providerOrder = ids.join(",");
    }

    QQC2.SpinBox {
        id: refreshInterval
        Kirigami.FormData.label: i18n("Refresh interval:")
        from: 60
        to: 3600
        stepSize: 60
        editable: true
        textFromValue: function (value, locale) {
            return String(Math.round(value / 60)) + " minutes";
        }
        valueFromText: function (text, locale) {
            var minutes = Number(text.replace(/[^0-9.]/g, ""));
            return isNaN(minutes) ? 300 : Math.round(minutes * 60);
        }
    }

    QQC2.CheckBox {
        id: showUnsupported
        Kirigami.FormData.label: i18n("Providers:")
        text: i18n("Show unavailable providers")
        checked: true
    }

    QQC2.CheckBox {
        id: hideEmptyProviders
        Kirigami.FormData.label: i18n("Providers:")
        text: i18n("Hide providers with no usage yet in the panel")
    }

    QQC2.CheckBox {
        id: showExhaustedReset
        Kirigami.FormData.label: i18n("Display:")
        text: i18n("Show the closest reset when a 5h/weekly window is exhausted")
        checked: true
    }

    QQC2.ComboBox {
        id: resetTextFormat
        Kirigami.FormData.label: i18n("Popup reset text:")
        // "long", matching the main.xml default.
        currentIndex: 1
        model: [
            { value: "short", text: i18n("Short duration (30min)") },
            { value: "long", text: i18n("Long date (14 Oct 12:25)") },
            { value: "both", text: i18n("Both (30min 14 Oct 12:25)") }
        ]
        textRole: "text"
        valueRole: "value"
    }

    ColumnLayout {
        Kirigami.FormData.label: i18n("Show:")
        spacing: 2

        Repeater {
            model: page.orderedKnownIds
            delegate: RowLayout {
                id: orderedProvider
                required property var modelData
                required property int index
                spacing: 0

                QQC2.CheckBox {
                    text: page.providerName(orderedProvider.modelData)
                    checked: !page.isHidden(orderedProvider.modelData)
                    onToggled: page.setHidden(orderedProvider.modelData, !checked)
                }

                QQC2.ToolButton {
                    icon.name: "arrow-up"
                    enabled: orderedProvider.index > 0
                    onClicked: page.moveProvider(orderedProvider.modelData, -1)
                    Accessible.name: i18n("Move up")
                }

                QQC2.ToolButton {
                    icon.name: "arrow-down"
                    enabled: orderedProvider.index < page.orderedKnownIds.length - 1
                    onClicked: page.moveProvider(orderedProvider.modelData, 1)
                    Accessible.name: i18n("Move down")
                }
            }
        }

        QQC2.Label {
            visible: page.knownProviders.length === 0
            text: i18n("Open the widget once so it can report which providers are available.")
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.WordWrap
            Layout.maximumWidth: 400
        }
    }

    QQC2.TextField {
        id: codexbarPath
        Kirigami.FormData.label: i18n("CodexBar CLI:")
        Layout.minimumWidth: 320
        placeholderText: i18n("Leave empty to find codexbar on PATH")
    }

    QQC2.Label {
        Layout.fillWidth: true
        Layout.maximumWidth: 520
        Kirigami.FormData.label: i18n("Data sources:")
        text: i18n("The widget reads local, credential-free JSON snapshots or commands configured in ~/.config/limit-widget. It never stores provider tokens in Plasma settings.")
        wrapMode: Text.WordWrap
        color: Kirigami.Theme.disabledTextColor
    }
}
