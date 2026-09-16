package com.futbol.tv.model;

import org.json.JSONObject;

public final class Source {
    public final String id;
    public final String name;
    public final String url;
    public final String userAgent;
    public final String pageUrl;

    public Source(String id, String name, String url, String userAgent, String pageUrl) {
        this.id = id;
        this.name = name;
        this.url = url;
        this.userAgent = userAgent;
        this.pageUrl = pageUrl;
    }

    public static Source from(JSONObject json) {
        return new Source(
                json.optString("id", "source-1"),
                json.optString("name", "Fuente"),
                json.optString("url", ""),
                json.optString("user_agent", null),
                json.optString("page_url", null));
    }
}
