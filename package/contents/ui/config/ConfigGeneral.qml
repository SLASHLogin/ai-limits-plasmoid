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
    // Not an alias: the checkbox list writes this as a comma-separated string.
    property string cfg_hiddenProviders: ""
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

    ColumnLayout {
        Kirigami.FormData.label: i18n("Show:")
        spacing: 2

        Repeater {
            model: page.knownProviders
            delegate: QQC2.CheckBox {
                required property var modelData
                text: modelData.name
                checked: !page.isHidden(modelData.id)
                onToggled: page.setHidden(modelData.id, !checked)
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
