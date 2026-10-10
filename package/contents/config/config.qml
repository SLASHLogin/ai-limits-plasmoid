// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick

import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory {
        name: i18n("General")
        // A ConfigCategory icon crosses into the settings dialog as a plain
        // string, which only resolves as a theme icon name — the package's
        // own mark cannot load there. This is the closest stock one: the
        // same ascending bars over a baseline.
        icon: "office-chart-bar"
        // The source is resolved against contents/ui, not the package root.
        source: "config/ConfigGeneral.qml"
    }
}
