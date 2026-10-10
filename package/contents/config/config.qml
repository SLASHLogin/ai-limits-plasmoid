// SPDX-FileCopyrightText: 2026 SLASHLogin
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick

import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory {
        name: i18n("General")
        // The product mark, the same one the popup's header carries.
        icon: Qt.resolvedUrl("../icons/ailimits-symbolic.svg")
        // The source is resolved against contents/ui, not the package root.
        source: "config/ConfigGeneral.qml"
    }
}
