// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
Kirigami.FormLayout {
    id: page

    property alias cfg_refreshInterval: refreshInterval.value
    property alias cfg_showUnsupported: showUnsupported.checked

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

    QQC2.Label {
        Layout.fillWidth: true
        Layout.maximumWidth: 520
        Kirigami.FormData.label: i18n("Data sources:")
        text: i18n("The widget reads local, credential-free JSON snapshots or commands configured in ~/.config/limit-widget. It never stores provider tokens in Plasma settings.")
        wrapMode: Text.WordWrap
        color: Kirigami.Theme.disabledTextColor
    }
}
