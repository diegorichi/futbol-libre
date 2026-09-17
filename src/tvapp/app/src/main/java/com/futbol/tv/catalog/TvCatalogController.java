package com.futbol.tv.catalog;

import android.os.Handler;

import com.futbol.tv.model.Event;
import com.futbol.tv.AppUpdateManager;
import com.futbol.tv.ServerClient;
import com.futbol.tv.StreamingCapabilities;

import java.util.List;

/** Owns catalog HTTP and remote APK updates. */
public final class TvCatalogController implements AutoCloseable {
    public interface Listener {
        void onEventsLoaded(List<Event> events, StreamingCapabilities capabilities, boolean initialLoad);
        void onEventsError(Exception error, boolean initialLoad);
        void onUpdateAvailable(AppUpdateManager.Release release);
        void onUpdateStarted();
        void onUpdateError(Exception error);
    }

    private final Handler main;
    private final ServerClient serverClient = new ServerClient();
    private final AppUpdateManager updateManager;
    private final Listener listener;
    private boolean updateChecked;

    public TvCatalogController(android.content.Context context, Handler main, Listener listener) {
        this.main = main;
        this.listener = listener;
        this.updateManager = new AppUpdateManager(context);
    }

    public void loadEvents(String baseUrl, boolean initialLoad) {
        serverClient.loadEvents(baseUrl, new ServerClient.EventsCallback() {
            @Override public void onSuccess(List<Event> events, StreamingCapabilities capabilities) {
                main.post(() -> listener.onEventsLoaded(events, capabilities, initialLoad));
            }

            @Override public void onError(Exception error) {
                main.post(() -> listener.onEventsError(error, initialLoad));
            }
        });
    }

    public void checkForUpdate(String baseUrl, int currentVersionCode) {
        if (updateChecked) return;
        updateChecked = true;
        updateManager.check(baseUrl, currentVersionCode, new AppUpdateManager.CheckCallback() {
            @Override public void onUpToDate() { }
            @Override public void onUpdateAvailable(AppUpdateManager.Release release) {
                main.post(() -> listener.onUpdateAvailable(release));
            }
            @Override public void onError(Exception error) { }
        });
    }

    public void installUpdate(AppUpdateManager.Release release) {
        if (release == null) {
            listener.onUpdateError(new IllegalStateException("No hay una actualización pendiente"));
            return;
        }
        updateManager.downloadAndInstall(release, new AppUpdateManager.InstallCallback() {
            @Override public void onStarted() { main.post(listener::onUpdateStarted); }
            @Override public void onError(Exception error) { main.post(() -> listener.onUpdateError(error)); }
        });
    }

    public void requestVpnStreamUrl(String baseUrl, String eventId, String sourceId, ServerClient.StreamUrlCallback callback) {
        serverClient.requestVpnStreamUrl(baseUrl, eventId, sourceId, callback);
    }

    @Override public void close() {
        serverClient.close();
        updateManager.close();
    }
}
