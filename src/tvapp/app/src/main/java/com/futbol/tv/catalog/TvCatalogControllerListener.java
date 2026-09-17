package com.futbol.tv.catalog;

import com.futbol.tv.model.Event;
import com.futbol.tv.AppUpdateManager;
import com.futbol.tv.StreamingCapabilities;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.state.ScreenStates;

import java.util.List;

/** Adapts catalog callbacks to screen state without putting them in Activity. */
public final class TvCatalogControllerListener implements TvCatalogController.Listener {
    public interface Host {
        ScreenState state();
        void replaceEvents(List<Event> events, StreamingCapabilities capabilities, boolean initialLoad);
        void setPendingUpdate(AppUpdateManager.Release release);
        void clearPendingUpdate();
        void setUpdateStatus(String status);
        void goTo(ScreenState state);
        void invalidate();
        void checkForUpdate();
        void showToast(String message);
    }

    private final Host host;

    public TvCatalogControllerListener(Host host) { this.host = host; }

    @Override public void onEventsLoaded(List<Event> events, StreamingCapabilities capabilities, boolean initialLoad) {
        if (!initialLoad && host.state() != ScreenStates.EVENTS_STATE) return;
        host.replaceEvents(events, capabilities, initialLoad);
        if (initialLoad) host.goTo(ScreenStates.EVENTS_STATE);
        host.invalidate();
        host.checkForUpdate();
    }

    @Override public void onEventsError(Exception error, boolean initialLoad) {
        if (!initialLoad && host.state() != ScreenStates.EVENTS_STATE) return;
        host.goTo(ScreenStates.ERROR_STATE);
        host.invalidate();
        host.showToast("No se pudo cargar el servidor");
    }

    @Override public void onUpdateAvailable(AppUpdateManager.Release release) {
        if (host.state() != ScreenStates.EVENTS_STATE) return;
        host.setPendingUpdate(release);
        host.setUpdateStatus(release.changelog.isEmpty() ? "Hay una nueva versión disponible" : release.changelog);
        host.goTo(ScreenStates.UPDATE_STATE);
        host.invalidate();
    }

    @Override public void onUpdateStarted() {
        host.clearPendingUpdate();
        host.goTo(ScreenStates.EVENTS_STATE);
        host.invalidate();
    }

    @Override public void onUpdateError(Exception error) {
        host.clearPendingUpdate();
        host.goTo(ScreenStates.EVENTS_STATE);
        host.showToast("No se pudo actualizar la app");
        host.invalidate();
    }

}
