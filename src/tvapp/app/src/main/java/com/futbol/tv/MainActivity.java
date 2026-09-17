package com.futbol.tv;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.os.Handler;
import android.view.KeyEvent;
import android.view.View;
import android.content.res.Configuration;
import android.widget.FrameLayout;
import android.widget.Toast;

import androidx.media3.ui.PlayerView;

import com.futbol.tv.model.Event;
import com.futbol.tv.model.Source;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.state.ScreenStates;
import com.futbol.tv.state.TvNavigationController;
import com.futbol.tv.ui.layout.TvLayoutProfile;
import com.futbol.tv.input.TvInputController;
import com.futbol.tv.catalog.TvCatalogController;
import com.futbol.tv.catalog.TvCatalogControllerListener;
import com.futbol.tv.discovery.ServerDiscoveryController;
import com.futbol.tv.playback.TvPlaybackCoordinator;

import java.util.ArrayList;
import java.util.List;

/** Minimal remote-first TV UI: events -> sources -> preview -> fullscreen. */
@androidx.media3.common.util.UnstableApi
public class MainActivity extends Activity implements TvScreenView.Host, TvInputController.Host, TvCatalogControllerListener.Host, ScreenState.BackHandler {
    private final Handler main = new Handler();
    private FrameLayout root;
    private TvScreenView screen;
    private PlayerView playerView;
    private PlayerView pipView;
    private TvPlaybackCoordinator playback;
    private TvCatalogController catalog;
    private AppUpdateManager.Release pendingUpdate;
    private String updateStatus = "Descarga e instalación con confirmación de Android";
    private ServerDiscoveryController discovery;
    private String serverBase;
    private final List<Event> events = new ArrayList<>();
    private final TvNavigationController navigation = new TvNavigationController();
    private TvInputController input;
    private int selectedEvent = 0;
    private int eventOffset = 0;
    private int selectedSource = 0;
    private int sourceOffset = 0;
    private int pipEvent = 0;
    private int pipEventOffset = 0;
    private int pipSource = 0;
    private int pipSourceOffset = 0;
    private int previewAction = 0;
    private StreamingCapabilities streaming = StreamingCapabilities.disabled();
    private boolean resumePlaybackOnStart;
    private final Runnable refreshTask = new Runnable() {
        @Override public void run() {
            // Nunca cambiar la pantalla mientras se reproduce un stream. El
            // refresco del catálogo queda limitado a la pantalla de eventos.
            if (serverBase != null && navigation.current() == ScreenStates.EVENTS_STATE) loadEvents(false);
            main.postDelayed(this, 60000);
        }
    };

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        root = new FrameLayout(this);
        playerView = new PlayerView(this);
        playerView.setUseController(false);
        playerView.setVisibility(View.GONE);
        root.addView(playerView, new FrameLayout.LayoutParams(-1, -1));
        pipView = new PlayerView(this);
        pipView.setUseController(false);
        pipView.setVisibility(View.GONE);
        pipView.setOnTouchListener((view, event) -> {
            if (navigation.current() != ScreenStates.DUAL_STATE || !screen.isCompactLayout()) return false;
            if (event.getAction() == android.view.MotionEvent.ACTION_UP) {
                promotePipToPrimary();
            }
            return true;
        });
        root.addView(pipView, new FrameLayout.LayoutParams(-1, -1));
        catalog = new TvCatalogController(this, main, new TvCatalogControllerListener(this));
        playback = new TvPlaybackCoordinator(this, playerView, pipView, catalog, main,
                () -> screen.invalidate());
        discovery = new ServerDiscoveryController(this, main, new ServerDiscoveryController.Listener() {
            @Override public void onServerFound(String baseUrl) { connect(baseUrl); }

            @Override public void onDiscoveryError(Exception error) {
                navigation.goTo(ScreenStates.ERROR_STATE);
                screen.invalidate();
            }
        });
        screen = new TvScreenView(this, this);
        input = new TvInputController(this);
        root.addView(screen, new FrameLayout.LayoutParams(-1, -1));
        setContentView(root);

        String explicit = getIntent().getStringExtra("server_url");
        if (explicit == null || explicit.trim().isEmpty()) {
            explicit = BuildConfig.SERVER_URL;
        }
        if (explicit != null && !explicit.trim().isEmpty()) {
            connect(explicit);
        } else {
            discoverServer();
        }
    }

    @Override public void discoverServer() {
        serverBase = null;
        navigation.goTo(ScreenStates.SEARCHING_STATE);
        screen.invalidate();
        discovery.start(isEmulator());
    }

    private boolean isEmulator() {
        return Build.FINGERPRINT.startsWith("generic") || Build.MODEL.contains("Emulator") || Build.MODEL.contains("Android SDK");
    }

    private void connect(String base) {
        serverBase = base.replaceAll("/$", "");
        discovery.stop();
        main.removeCallbacks(refreshTask);
        main.postDelayed(refreshTask, 60000);
        loadEvents(true);
    }

    private void loadEvents(boolean showLoading) {
        if (showLoading) {
            navigation.goTo(ScreenStates.SEARCHING_STATE);
            screen.invalidate();
        }
        catalog.loadEvents(serverBase, showLoading);
    }

    @Override public void installPendingUpdate() {
        if (pendingUpdate == null) { navigation.goTo(ScreenStates.EVENTS_STATE); screen.invalidate(); return; }
        updateStatus = "Descargando actualización...";
        screen.invalidate();
        catalog.installUpdate(pendingUpdate);
    }

    @Override public void preview(Source source) {
        navigation.goTo(ScreenStates.PREVIEW_STATE);
        previewAction = 0;
        playback.preview(source);
        screen.invalidate();
    }

    @Override public void toggleVpnPreview() {
        if (!vpnAvailable() || events.isEmpty()) return;
        Event event = events.get(selectedEvent);
        Source source = event.sources.get(selectedSource);
        playback.toggleVpnPreview(serverBase, event, source);
    }

    @Override public void openPipEventPicker() {
        if (events.size() < 2) {
            Toast.makeText(this, "No hay un segundo evento disponible", Toast.LENGTH_SHORT).show();
            return;
        }
        pipEvent = pipEvent == selectedEvent ? (selectedEvent + 1) % events.size() : pipEvent;
        pipEventOffset = NavigationState.offsetFor(pipEvent, events.size(), screen.visibleRows(), listFocusPosition());
        navigation.goTo(ScreenStates.PIP_EVENTS_STATE);
        screen.invalidate();
    }

    @Override public void showPipSources() {
        if (events.get(pipEvent).sources.isEmpty()) return;
        pipSource = 0;
        pipSourceOffset = 0;
        navigation.goTo(ScreenStates.PIP_SOURCES_STATE);
        screen.invalidate();
    }

    @Override public void startPip(Source source) {
        playback.startPip(source);
        navigation.goTo(ScreenStates.DUAL_STATE);
        screen.invalidate();
    }

    @Override public void promotePipToPrimary() {
        if (!playback.swap()) {
            Toast.makeText(this, "Esperá a que PiP termine de cargar", Toast.LENGTH_SHORT).show();
            return;
        }
        int event = selectedEvent; selectedEvent = pipEvent; pipEvent = event;
        int source = selectedSource; selectedSource = pipSource; pipSource = source;
    }

    @Override public void showSources() {
        if (events.isEmpty()) return;
        selectedSource = 0;
        sourceOffset = 0;
        playback.releaseAll();
        navigation.goTo(ScreenStates.SOURCES_STATE);
        screen.invalidate();
    }

    private void back() { navigation.back(this); }

    @Override public void exit() { finish(); }
    @Override public void closePip() { playback.closePip(); }
    @Override public void showPreview() { playback.showPreview(); }
    @Override public void stopPrimary() { playback.stopPrimary(); }
    @Override public void releasePlayback() { playback.releaseAll(); }
    @Override public void clearPendingUpdate() { pendingUpdate = null; }
    @Override public void navigate(ScreenState target) { navigation.goTo(target); }
    @Override public void invalidate() { screen.invalidate(); }

    private int listFocusPosition() { return Math.max(0, screen.visibleRows() - 3); }

    private void refreshListOffsets() {
        eventOffset = NavigationState.offsetFor(selectedEvent, events.size(), screen.visibleRows(), listFocusPosition());
        sourceOffset = events.isEmpty() ? 0 : NavigationState.offsetFor(selectedSource, events.get(selectedEvent).sources.size(), screen.visibleRows(), listFocusPosition());
        pipEventOffset = NavigationState.offsetFor(pipEvent, events.size(), screen.visibleRows(), listFocusPosition());
        pipSourceOffset = events.isEmpty() ? 0 : NavigationState.offsetFor(pipSource, events.get(pipEvent).sources.size(), screen.visibleRows(), listFocusPosition());
    }

    @Override public void replaceEvents(List<Event> loaded, StreamingCapabilities capabilities, boolean initialLoad) {
        events.clear();
        events.addAll(loaded);
        streaming = capabilities == null ? StreamingCapabilities.disabled() : capabilities;
        selectedEvent = NavigationState.clamp(selectedEvent, events.size());
        eventOffset = NavigationState.offsetFor(selectedEvent, events.size(), screen.visibleRows(), listFocusPosition());
    }
    @Override public void setPendingUpdate(AppUpdateManager.Release release) { pendingUpdate = release; }
    @Override public void setUpdateStatus(String status) { updateStatus = status; }
    @Override public void checkForUpdate() { catalog.checkForUpdate(serverBase, BuildConfig.APP_VERSION_CODE); }
    @Override public void showToast(String message) { Toast.makeText(this, message, Toast.LENGTH_SHORT).show(); }

    @Override public ScreenState state() { return navigation.current(); }
    @Override public void setSelectedEvent(int value) { selectedEvent = value; }
    @Override public void setEventOffset(int value) { eventOffset = value; }
    @Override public void setSelectedSource(int value) { selectedSource = value; }
    @Override public void setSourceOffset(int value) { sourceOffset = value; }
    @Override public void setPipEvent(int value) { pipEvent = value; }
    @Override public void setPipEventOffset(int value) { pipEventOffset = value; }
    @Override public void setPipSource(int value) { pipSource = value; }
    @Override public void setPipSourceOffset(int value) { pipSourceOffset = value; }
    @Override public void setPreviewAction(int value) { previewAction = value; }
    @Override public TvLayoutProfile layout() { return screen.layoutProfile(); }
    @Override public int visibleRows() { return screen.visibleRows(); }
    @Override public float dragOffsetDp() { return screen.dragOffsetDp(); }
    @Override public float widthDp() { return screen.getWidth() / screen.getResources().getDisplayMetrics().density; }
    @Override public float heightDp() { return screen.getHeight() / screen.getResources().getDisplayMetrics().density; }
    @Override public void goTo(ScreenState nextState) { navigation.goTo(nextState); }
    @Override public void switchPrimary(Source source) { playback.switchPrimary(source); }
    @Override public void enterFullscreen() { playback.enterFullscreen(); }
    @Override public List<Event> events() { return events; }
    @Override public int selectedEvent() { return selectedEvent; }
    @Override public int eventOffset() { return eventOffset; }
    @Override public int selectedSource() { return selectedSource; }
    @Override public int sourceOffset() { return sourceOffset; }
    @Override public int pipEvent() { return pipEvent; }
    @Override public int pipEventOffset() { return pipEventOffset; }
    @Override public int pipSource() { return pipSource; }
    @Override public int pipSourceOffset() { return pipSourceOffset; }
    @Override public int previewAction() { return previewAction; }
    @Override public boolean vpnAvailable() { return streaming.vpnEnabled && streaming.vpnAvailable; }
    @Override public boolean vpnActive() { return playback.vpnActive(); }
    @Override public boolean previewLoading() { return playback.previewLoading(); }
    @Override public String playerMessage() { return playback.playerMessage(); }
    @Override public String updateVersion() { return pendingUpdate == null ? "" : pendingUpdate.versionName; }
    @Override public String updateStatus() { return updateStatus; }
    @Override public void onBack() { back(); }
    @Override public void onTouch(float x, float y) { input.tap(x, y); }
    @Override public void onEventTap(int index, boolean forPip) {
        if (index < 0 || index >= events.size()) return;
        if (forPip) {
            pipEvent = index;
            showPipSources();
        } else {
            selectedEvent = index;
            showSources();
        }
    }
    @Override public void onSourceTap(int index, boolean forPip) {
        if (forPip) {
            if (pipEvent >= 0 && pipEvent < events.size() && index >= 0 && index < events.get(pipEvent).sources.size()) {
                pipSource = index;
                startPip(events.get(pipEvent).sources.get(index));
            }
        } else if (selectedEvent >= 0 && selectedEvent < events.size()
                && index >= 0 && index < events.get(selectedEvent).sources.size()) {
            selectedSource = index;
            preview(events.get(selectedEvent).sources.get(index));
        }
    }
    @Override public void onSwipe(boolean down) {
        input.onSwipe(down);
    }

    @Override public void onPlaybackControl(int control) {
        if (control == 0) input.onDpad(KeyEvent.KEYCODE_DPAD_UP);
        else if (control == 1) input.onDpad(KeyEvent.KEYCODE_DPAD_DOWN);
        else if (control == 2) {
            navigation.goTo(ScreenStates.PLAYER_STATE);
            playback.enterFullscreen();
            screen.invalidate();
        } else if (control == 3) {
            if (navigation.current() == ScreenStates.PREVIEW_STATE) toggleVpnPreview();
            else toggleVpnPlayback();
        } else if (control == 4) {
            openPipEventPicker();
        }
    }

    @Override public void toggleVpnPlayback() {
        if (!vpnAvailable() || events.isEmpty()) return;
        Event event = events.get(selectedEvent);
        Source source = event.sources.get(selectedSource);
        playback.toggleVpnPlayback(serverBase, event, source);
    }

    @Override public int onScroll(float deltaY) { return input.scroll(deltaY); }

    @Override public void onDpad(int keyCode) { input.onDpad(keyCode); }

    @Override public void onConfirm() { input.onConfirm(); }

    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getAction() == KeyEvent.ACTION_DOWN
                && (navigation.current() == ScreenStates.PLAYER_STATE || navigation.current() == ScreenStates.DUAL_STATE)
                && (event.getKeyCode() == KeyEvent.KEYCODE_DPAD_UP
                || event.getKeyCode() == KeyEvent.KEYCODE_DPAD_DOWN
                || (navigation.current() == ScreenStates.DUAL_STATE && event.getKeyCode() == KeyEvent.KEYCODE_DPAD_RIGHT))) {
            onDpad(event.getKeyCode());
            return true;
        }
        return super.dispatchKeyEvent(event);
    }

    @Override public void onBackPressed() { back(); }

    @Override public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        playback.onConfigurationChanged();
        refreshListOffsets();
        screen.invalidate();
    }

    @Override protected void onStop() {
        super.onStop();
        resumePlaybackOnStart = navigation.current() == ScreenStates.PLAYER_STATE || navigation.current() == ScreenStates.DUAL_STATE;
        if (resumePlaybackOnStart) {
            playback.pauseAll();
        }
    }

    @Override protected void onStart() {
        super.onStart();
        if (resumePlaybackOnStart && (navigation.current() == ScreenStates.PLAYER_STATE || navigation.current() == ScreenStates.DUAL_STATE)) {
            playback.resumeAll();
        }
        resumePlaybackOnStart = false;
    }

    @Override protected void onDestroy() {
        main.removeCallbacks(refreshTask);
        discovery.close();
        playback.release();
        catalog.close();
        super.onDestroy();
    }


}
