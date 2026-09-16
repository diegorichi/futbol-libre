package com.futbol.tv;

import com.futbol.tv.model.Event;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** HTTP boundary for the futbol-server API. */
public final class ServerClient {
    public interface EventsCallback {
        void onSuccess(List<Event> events, StreamingCapabilities streaming);
        void onError(Exception error);
    }

    public interface StreamUrlCallback {
        void onSuccess(String url, String proxyUrl);
        void onError(Exception error);
    }

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public void loadEvents(String baseUrl, EventsCallback callback) {
        executor.execute(() -> {
            try {
                String body = get(baseUrl.replaceAll("/$", "") + "/api/v1/events");
                JSONObject payload = new JSONObject(body);
                JSONArray array = payload.optJSONArray("events");
                List<Event> result = new ArrayList<>();
                if (array != null) {
                    for (int i = 0; i < array.length(); i++) result.add(Event.from(array.getJSONObject(i)));
                }
                callback.onSuccess(result, StreamingCapabilities.from(payload.optJSONObject("streaming") == null ? new JSONObject() : payload.optJSONObject("streaming")));
            } catch (Exception error) {
                callback.onError(error);
            }
        });
    }

    public void requestVpnStreamUrl(String baseUrl, String eventId, String sourceId, StreamUrlCallback callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(baseUrl.replaceAll("/$", "") + "/api/v1/stream-url");
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(15000);
                connection.setRequestMethod("POST");
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                byte[] body = new JSONObject().put("event_id", eventId).put("source_id", sourceId).toString().getBytes();
                connection.getOutputStream().write(body);
                int status = connection.getResponseCode();
                if (status < 200 || status >= 300) throw new IllegalStateException("El servidor no pudo resolver la URL VPN (HTTP " + status + ")");
                JSONObject response = new JSONObject(readResponse(connection));
                callback.onSuccess(response.getString("url"), response.optString("proxy_url", ""));
                connection.disconnect();
            } catch (Exception error) {
                callback.onError(error);
            }
        });
    }

    public void close() { executor.shutdownNow(); }

    private static String get(String address) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(8000);
        connection.setRequestMethod("GET");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
            StringBuilder result = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) result.append(line);
            return result.toString();
        } finally { connection.disconnect(); }
    }

    private static String readResponse(HttpURLConnection connection) throws Exception {
        try (InputStream input = connection.getInputStream()) {
            byte[] buffer = new byte[4096];
            StringBuilder result = new StringBuilder();
            int count;
            while ((count = input.read(buffer)) != -1) result.append(new String(buffer, 0, count));
            return result.toString();
        }
    }
}
