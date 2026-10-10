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
    readonly property bool hideEmptyProviders: Plasmoid.configuration.hideEmptyProviders === true
    readonly property bool showExhaustedReset: Plasmoid.configuration.showExhaustedReset !== false
    // What the popup's reset hint contains: the short duration until the
    // reset, the absolute date, or both. Anything unknown falls back to the
    // absolute date, which is what the hint has always shown.
    readonly property string resetTextFormat: {
        var format = String(Plasmoid.configuration.resetTextFormat || "");
        return format === "short" || format === "both" ? format : "long";
    }
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

    // The user's pinned provider order, as an id→index lookup. Ids the pin
    // does not mention keep the collector's order, after the pinned ones.
    readonly property var providerOrder: {
        var result = {};
        var raw = String(Plasmoid.configuration.providerOrder || "");
        raw.split(",").forEach(function (id, index) {
            var trimmed = id.trim();
            if (trimmed.length > 0 && result[trimmed] === undefined) {
                result[trimmed] = index;
            }
        });
        return result;
    }
    readonly property var orderedProviders: providers.slice().sort(function (a, b) {
        var aIndex = root.providerOrder[String(a.id || "")];
        var bIndex = root.providerOrder[String(b.id || "")];
        if (aIndex === undefined && bIndex === undefined) {
            return 0;
        }
        if (aIndex === undefined) {
            return 1;
        }
        if (bIndex === undefined) {
            return -1;
        }
        return aIndex - bIndex;
    })

    property bool loading: false
    property string lastUpdated: ""
    property string errorText: ""
    property var providers: [
        defaultProvider("codex", "ChatGPT", "C", "codex-symbolic.svg", "https://chatgpt.com/settings/usage"),
        defaultProvider("claude", "Claude Code", "A", "claude-symbolic.svg", "https://claude.ai/settings/usage"),
        defaultProvider("copilot", "GitHub Copilot", "G", "copilot-symbolic.svg", "https://github.com/settings/copilot"),
        defaultProvider("mistral", "Mistral Vibe", "M", "mistral-symbolic.svg", "https://admin.mistral.ai/subscriptions")
    ]

    // A provider with nothing to show: no live sign-in, a plan without any
    // allowance, or an allowance nothing was consumed from yet — an untouched
    // window reads 100% the same way an absent one reads "—". A transient
    // failure is a started provider that could not be read, not an empty one,
    // so error rows stay visible.
    function providerIsEmpty(provider) {
        if (provider.state === "error" || provider.state === "rateLimited") {
            return false;
        }
        if (root.compactValue(provider) === "—") {
            return true;
        }
        // Every reported window untouched means no usage this period. A window
        // without numbers proves nothing — an unlimited plan's usage cannot be
        // measured, so one such window keeps the provider visible.
        var windows = provider.windows && typeof provider.windows.length === "number" ? provider.windows : [];
        var measurable = 0;
        for (var index = 0; index < windows.length; index++) {
            var windowPercent = root.remainingPercent(windows[index]);
            if (windowPercent !== null) {
                measurable++;
                if (windowPercent < 100) {
                    return false;
                }
            } else {
                return false;
            }
        }
        if (measurable === 0) {
            return root.remainingPercent(provider) === 100;
        }
        return true;
    }

    readonly property var displayedProviders: orderedProviders.filter(function (provider) {
        if (!root.providerVisible(provider)) {
            return false;
        }
        return root.showUnsupported || provider.state === "ok" || provider.state === "stale";
    })
    // The panel alone honors "hide providers with no usage yet" — the popup is
    // the place to look a provider up in, so it keeps listing every row.
    // Providers discovered through the optional CodexBar CLI are also shown in
    // the popup but kept out of the panel. There can be dozens of them, and
    // the panel representation grows with every row it draws, so including
    // them would push the rest of the panel off a normal-width screen.
    readonly property var panelProviders: orderedProviders.filter(function (provider) {
        if (!root.providerVisible(provider) || String(provider.id || "").indexOf("codexbar:") === 0) {
            return false;
        }
        return !root.hideEmptyProviders || !root.providerIsEmpty(provider);
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
    readonly property string compactSummary: orderedProviders.map(function (provider) {
        // As in the panel: an exhausted window makes the percentages
        // unusable, so the tooltip shows the time until the reset alone.
        var reset = root.panelReset(provider);
        if (reset) {
            return provider.name + ": " + reset;
        }
        var value = root.compactValue(provider);
        // The panel itself has no room for a word, so spell the direction out
        // wherever there is: an unlabelled "99%" reads as consumption.
        var body = value === "—" ? value : value + " " + i18n("left");
        return provider.name + ": " + body;
    }).join("  ·  ")
    // The width of what the panel actually draws — panelProviders, not every
    // provider — so hidden rows shrink the widget instead of stretching the
    // remaining ones across space they no longer need. The base and the gap
    // mirror compactRepresentation's RowLayout: 4 px of margin on each side
    // and 5 px between rows, so the drawing ends as far from the right edge
    // as it starts from the left.
    readonly property int compactWidth: 8 + panelProviders.reduce(function (width, provider) {
        return width + root.compactProviderWidth(provider);
    }, 0) + Math.max(0, panelProviders.length - 1) * 5;
    // The popup's fixed chrome around the provider rows: margins, header,
    // spacing, separator and footer. Keep in sync with fullRepresentation.
    readonly property int popupChromeHeight: 123;
    // The height the popup's rows need, so the popup can size itself to fit
    // them instead of cutting the last row's Usage button off.
    readonly property int rowsHeight: {
        var total = 0;
        for (var index = 0; index < displayedProviders.length; index++) {
            var provider = displayedProviders[index];
            var gauges = 0;
            var windows = provider.windows || [];
            for (var position = 0; position < windows.length; position++) {
                var window = windows[position];
                if (typeof window.remaining === "number" && typeof window.limit === "number" && window.limit > 0) {
                    gauges++;
                }
            }
            // Keep in sync with ProviderRow's implicitHeight.
            total += 54 + Math.max(1, gauges) * 7;
        }
        return total + Math.max(0, displayedProviders.length - 1) * 5;
    }

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
        var entries = [];
        if (provider && provider.windows && typeof provider.windows.length === "number") {
            for (var index = 0; index < provider.windows.length; index++) {
                var windowPercent = root.remainingPercent(provider.windows[index]);
                if (windowPercent !== null) {
                    entries.push({ percent: windowPercent, label: String(provider.windows[index].label || "") });
                }
            }
        }
        if (entries.length === 0) {
            var providerPercent = root.remainingPercent(provider);
            if (providerPercent !== null) {
                entries.push({ percent: providerPercent, label: "" });
            }
        }
        if (entries.length > 0) {
            // The first window is the session window. Weekly windows are labelled
            // "7d", including per-model caps such as Claude's "Opus 7d" and Codex's
            // "Spark 7d". Show the session value and the tightest weekly one, so a
            // model cap cannot hide behind the combined total.
            var weekly = [];
            for (var pick = 1; pick < entries.length; pick++) {
                if (/7d$/.test(entries[pick].label)) {
                    weekly.push(entries[pick].percent);
                }
            }
            if (weekly.length > 0) {
                return String(Math.round(entries[0].percent)) + "%/" + String(Math.round(Math.min.apply(null, weekly))) + "%";
            }
            // With no weekly window, a second window is a separate budget of
            // the same length — Mistral's Vibe Code allowance next to its API
            // allowance. Show both values, as the session/weekly pair does,
            // rather than only the tighter one.
            if (entries.length > 1) {
                var rest = entries.slice(1).map(function (entry) { return entry.percent; });
                return String(Math.round(entries[0].percent)) + "%/" + String(Math.round(Math.min.apply(null, rest))) + "%";
            }
            return String(Math.round(entries[0].percent)) + "%";
        }
        if (provider && typeof provider.detail === "string" && provider.detail.toLowerCase().indexOf("unlimited") !== -1) {
            return "100%";
        }
        return "—";
    }

    function compactProviderWidth(provider) {
        return 16 + 4 + Math.ceil(compactFontMetrics.advanceWidth(root.panelValue(provider))) + 4;
    }

    // The value the panel draws for one provider: the compact share, or —
    // when a rolling window is exhausted and the allowance cannot be used
    // at all — the time until the closest reset alone. The percentages then
    // carry no information.
    function panelValue(provider) {
        var reset = root.panelReset(provider);
        return reset ? reset : root.compactValue(provider);
    }

    // The time until the closest reset of an exhausted rolling window, in
    // the biggest unit that expresses it: "30min", "3d". An exhausted window
    // blocks the provider outright — with Claude and ChatGPT, either period
    // at 0% stops all usage — so naming the window adds nothing, and the
    // panel has no room for a word besides.
    function panelReset(provider) {
        var found = root.closestExhaustedReset(provider);
        if (!found) {
            return "";
        }
        return root.formatResetIn(found.reset - Date.now());
    }

    // The time until a reset, in the biggest unit that expresses it:
    // "3d", "6h", "30min", "15s". An absolute clock time would be longer
    // than the percentage it replaces, and less readable besides.
    function formatResetIn(deltaMs) {
        var minutes = deltaMs / 60000;
        if (minutes >= 60 * 24) {
            return i18n("%1d", Math.round(deltaMs / 86400000));
        }
        if (minutes >= 60) {
            return i18n("%1h", Math.round(minutes / 60));
        }
        if (minutes >= 1) {
            return i18n("%1min", Math.round(minutes));
        }
        return i18n("%1s", Math.max(1, Math.round(deltaMs / 1000)));
    }

    // The rolling-period windows arrive labelled "5h" and "7d"; the popup
    // shows them capitalised: "5H", "7D", "Opus 7D".
    function periodLabel(label) {
        return String(label || "").replace(/5h$/, "5H").replace(/7d$/, "7D");
    }

    // The closest upcoming reset among a provider's exhausted session/weekly
    // windows: { reset: timestamp, label: window label }, or null when no
    // rolling window is exhausted. The reset display only makes sense for
    // rolling 5h/7d-style limits: monthly allowances — Mistral's EUR windows
    // and Copilot's premium interactions — already carry their reset in the
    // row's reset line, so those providers are excluded.
    function closestExhaustedReset(provider) {
        if (!root.showExhaustedReset) {
            return null;
        }
        if (provider.id === "mistral" || provider.id === "copilot") {
            return null;
        }
        var windows = provider.windows || [];
        var now = Date.now();
        var closest = 0;
        var closestLabel = "";
        for (var index = 0; index < windows.length; index++) {
            var window = windows[index];
            if (window.unit !== "percent") {
                continue;
            }
            if (typeof window.resetAt !== "string" || !window.resetAt) {
                continue;
            }
            var remaining = root.remainingPercent(window);
            if (remaining === null || remaining > 0) {
                continue;
            }
            var reset = new Date(window.resetAt).getTime();
            if (isNaN(reset) || reset <= now) {
                continue;
            }
            if (closest === 0 || reset < closest) {
                closest = reset;
                closestLabel = String(window.label || "");
            }
        }
        if (closest === 0) {
            return null;
        }
        return { reset: closest, label: closestLabel };
    }

    // The popup's hint for an exhausted rolling window, e.g. "R 5H 14:30".
    // Whether it carries the short duration, the absolute date, or both is
    // the resetTextFormat setting; the taskbar always shows the duration.
    function exhaustedReset(provider) {
        var found = root.closestExhaustedReset(provider);
        if (!found) {
            return "";
        }
        var delta = found.reset - Date.now();
        var resetDate = new Date(found.reset);
        var long = delta < 24 * 60 * 60 * 1000
            ? Qt.formatDateTime(resetDate, "HH:mm")
            : Qt.formatDateTime(resetDate, "d MMM HH:mm");
        var time = long;
        if (root.resetTextFormat === "short") {
            time = root.formatResetIn(delta);
        } else if (root.resetTextFormat === "both") {
            time = root.formatResetIn(delta) + " " + long;
        }
        var windows = provider.windows || [];
        var label = windows.length > 1 && found.label ? root.periodLabel(found.label) + " " : "";
        return i18n("R %1", label + time);
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
                        text: root.panelValue(horizontalProvider.modelData)
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
                        text: root.panelValue(verticalProvider.modelData)
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
        // Tall enough for the rows the collector reports by default, so the
        // last row's Usage button is not cut off; further rows scroll.
        implicitHeight: Math.min(root.popupChromeHeight + root.rowsHeight, 480)
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
                    // 28×28, so it sits on the same centre line and at the
                    // same size as the provider rows' Usage buttons. A
                    // RowLayout sizes its children from the attached Layout
                    // properties — width and height are ignored in here.
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
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
                // The rows' width is bound to the popup's width, so horizontal
                // scrolling is never meaningful; keeping the bar off also
                // reclaims the height it would otherwise take from the rows.
                QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff

                ColumnLayout {
                    width: popup.width - 32
                    spacing: 5

                    Repeater {
                        model: root.displayedProviders
                        delegate: ProviderRow {
                            required property var modelData
                            provider: modelData
                            resetHint: root.exhaustedReset(modelData)
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
