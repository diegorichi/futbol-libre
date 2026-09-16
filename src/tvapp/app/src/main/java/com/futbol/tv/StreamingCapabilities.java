package com.futbol.tv;

import org.json.JSONObject;

public final class StreamingCapabilities {
    public final boolean vpnEnabled;
    public final boolean vpnAvailable;
    public final String proxyUrl;
    public final double ttlHours;

    private StreamingCapabilities(boolean vpnEnabled, boolean vpnAvailable, String proxyUrl, double ttlHours) {
        this.vpnEnabled = vpnEnabled;
        this.vpnAvailable = vpnAvailable;
        this.proxyUrl = proxyUrl;
        this.ttlHours = ttlHours;
    }

    public static StreamingCapabilities from(JSONObject json) {
        return new StreamingCapabilities(
                json.optBoolean("vpn_enabled", false),
                json.optBoolean("vpn_available", false),
                json.optString("vpn_proxy_url", ""),
                json.optDouble("vpn_url_ttl_hours", 0));
    }

    public static StreamingCapabilities disabled() {
        return new StreamingCapabilities(false, false, "", 0);
    }
}
