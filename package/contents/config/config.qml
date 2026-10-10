// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick

import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory {
        name: i18n("General")
        icon: "view-statistics"
        // The source is resolved against contents/ui, not the package root.
        source: "config/ConfigGeneral.qml"
    }
}
