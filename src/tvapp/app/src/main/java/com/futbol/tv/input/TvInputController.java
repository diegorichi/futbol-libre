package com.futbol.tv.input;

import android.view.KeyEvent;

import com.futbol.tv.NavigationState;
import com.futbol.tv.model.Event;
import com.futbol.tv.model.Source;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.state.ScreenStates;
import com.futbol.tv.ui.layout.TvLayoutMetrics;
import com.futbol.tv.ui.layout.TvLayoutProfile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Dispatches input to the handler owned by the active screen state. */
public final class TvInputController {
    public interface Host {
        ScreenState state(); List<Event> events();
        int selectedEvent(); void setSelectedEvent(int value); int eventOffset(); void setEventOffset(int value);
        int selectedSource(); void setSelectedSource(int value); int sourceOffset(); void setSourceOffset(int value);
        int pipEvent(); void setPipEvent(int value); int pipEventOffset(); void setPipEventOffset(int value);
        int pipSource(); void setPipSource(int value); int pipSourceOffset(); void setPipSourceOffset(int value);
        int previewAction(); void setPreviewAction(int value); TvLayoutProfile layout(); int visibleRows(); float dragOffsetDp();
        float widthDp(); float heightDp(); void goTo(ScreenState state); void invalidate();
        void discoverServer(); void installPendingUpdate(); void showSources(); void preview(Source source);
        void openPipEventPicker(); void showPipSources(); void startPip(Source source); void promotePipToPrimary();
        void switchPrimary(Source source); void enterFullscreen(); void toggleVpnPreview(); void toggleVpnPlayback(); boolean vpnAvailable();
    }

    private interface StateInput {
        void tap(float x, float y); int scroll(float deltaY); void dpad(int keyCode); void confirm();
    }
    private interface OffsetReader { int read(); }

    private final Host host;
    private final Map<ScreenState, StateInput> handlers = new HashMap<>();
    private final Map<ScreenState, OffsetReader> offsets = new HashMap<>();

    public TvInputController(Host host) { this.host = host; registerHandlers(); }

    private void registerHandlers() {
        handlers.put(ScreenStates.ERROR_STATE, new StateInput() {
            public void tap(float x, float y) { host.discoverServer(); }
            public int scroll(float deltaY) { return 0; }
            public void dpad(int key) { if (isConfirm(key)) host.discoverServer(); }
            public void confirm() { host.discoverServer(); }
        });
        handlers.put(ScreenStates.UPDATE_STATE, new StateInput() {
            public void tap(float x, float y) { host.installPendingUpdate(); }
            public int scroll(float deltaY) { return 0; }
            public void dpad(int key) { }
            public void confirm() { host.installPendingUpdate(); }
        });
        handlers.put(ScreenStates.EVENTS_STATE, listState(false)); handlers.put(ScreenStates.SOURCES_STATE, listState(false));
        handlers.put(ScreenStates.PIP_EVENTS_STATE, listState(true)); handlers.put(ScreenStates.PIP_SOURCES_STATE, listState(true));
        handlers.put(ScreenStates.PREVIEW_STATE, previewState()); handlers.put(ScreenStates.PLAYER_STATE, playbackState());
        handlers.put(ScreenStates.DUAL_STATE, playbackState());
        offsets.put(ScreenStates.EVENTS_STATE, () -> host.eventOffset());
        offsets.put(ScreenStates.SOURCES_STATE, () -> host.sourceOffset());
        offsets.put(ScreenStates.PIP_EVENTS_STATE, () -> host.pipEventOffset());
        offsets.put(ScreenStates.PIP_SOURCES_STATE, () -> host.pipSourceOffset());
    }

    private StateInput active() { StateInput input = handlers.get(host.state()); return input == null ? idleState() : input; }
    private StateInput idleState() { return new StateInput() {
        public void tap(float x, float y) { } public int scroll(float deltaY) { return 0; }
        public void dpad(int key) { } public void confirm() { }
    }; }

    public void tap(float x, float y) { active().tap(x, y); }
    public int scroll(float deltaY) { return active().scroll(deltaY); }
    public void onDpad(int keyCode) { active().dpad(keyCode); }
    public void onConfirm() { active().confirm(); }
    public void onSwipe(boolean down) { onDpad(down ? KeyEvent.KEYCODE_DPAD_DOWN : KeyEvent.KEYCODE_DPAD_UP); }

    private StateInput listState(boolean pip) { return new StateInput() {
        public void tap(float x, float y) { tapList(x, y, pip); }
        public int scroll(float deltaY) { return scrollList(deltaY, pip); }
        public void dpad(int key) { dpadList(key, pip); }
        public void confirm() { confirmList(pip); }
    }; }

    private void tapList(float x, float y, boolean pip) {
        if (host.events().isEmpty()) return;
        ScreenState state = host.state();
        if (state.eventListVisible()) {
            int offset = pip ? host.pipEventOffset() : host.eventOffset();
            int item = TvLayoutMetrics.eventIndexAt(y, offset, host.dragOffsetDp(), host.layout().compact(), host.widthDp(), host.heightDp());
            if (item < 0 || item >= host.events().size()) return;
            if (pip) { host.setPipEvent(item); host.showPipSources(); } else { host.setSelectedEvent(item); host.showSources(); }
            return;
        }
        int event = pip ? host.pipEvent() : host.selectedEvent();
        if (event < 0 || event >= host.events().size()) return;
        int offset = pip ? host.pipSourceOffset() : host.sourceOffset();
        int item = TvLayoutMetrics.sourceIndexAt(y, offset, host.dragOffsetDp(), host.layout().compact());
        if (item < 0 || item >= host.events().get(event).sources.size()) return;
        Source source = host.events().get(event).sources.get(item);
        if (pip) { host.setPipSource(item); host.startPip(source); } else { host.setSelectedSource(item); host.preview(source); }
    }

    private int scrollList(float deltaY, boolean pip) {
        ScreenState state = host.state();
        if (!host.layout().compact() || host.events().isEmpty()) return 0;
        float row = state.eventListVisible()
                ? TvLayoutMetrics.compactEventRow(host.widthDp(), host.heightDp()) : TvLayoutMetrics.SOURCE_ROW_DP;
        int steps = Math.round(-deltaY / row); if (steps == 0) return 0;
        int old = listOffset(state);
        if (state.eventListVisible()) {
            int size = host.events().size(); int offset = clampOffset(old + steps, size);
            if (pip) { host.setPipEventOffset(offset); host.setPipEvent(NavigationState.clamp(offset + focus(), size)); }
            else { host.setEventOffset(offset); host.setSelectedEvent(NavigationState.clamp(offset + focus(), size)); }
        } else {
            int event = pip ? host.pipEvent() : host.selectedEvent(); int size = host.events().get(event).sources.size();
            int offset = clampOffset(old + steps, size);
            if (pip) { host.setPipSourceOffset(offset); host.setPipSource(NavigationState.clamp(offset + focus(), size)); }
            else { host.setSourceOffset(offset); host.setSelectedSource(NavigationState.clamp(offset + focus(), size)); }
        }
        host.invalidate(); return listOffset(state) - old;
    }

    private void dpadList(int key, boolean pip) {
        if (key != KeyEvent.KEYCODE_DPAD_UP && key != KeyEvent.KEYCODE_DPAD_DOWN || host.events().isEmpty()) return;
        int direction = key == KeyEvent.KEYCODE_DPAD_UP ? -1 : 1; ScreenState state = host.state();
        if (state.eventListVisible()) {
            int selected = pip ? host.pipEvent() : host.selectedEvent(); selected = NavigationState.clamp(selected + direction, host.events().size());
            if (pip) { host.setPipEvent(selected); host.setPipEventOffset(offset(selected, host.events().size())); }
            else { host.setSelectedEvent(selected); host.setEventOffset(offset(selected, host.events().size())); }
        } else {
            int event = pip ? host.pipEvent() : host.selectedEvent(); int size = host.events().get(event).sources.size();
            int selected = pip ? host.pipSource() : host.selectedSource(); selected = NavigationState.clamp(selected + direction, size);
            Source source = host.events().get(event).sources.get(selected);
            if (pip) { host.setPipSource(selected); host.setPipSourceOffset(offset(selected, size)); }
            else { host.setSelectedSource(selected); host.setSourceOffset(offset(selected, size)); host.preview(source); }
        }
        host.invalidate();
    }

    private void confirmList(boolean pip) {
        int event = pip ? host.pipEvent() : host.selectedEvent(); if (host.events().isEmpty() || event >= host.events().size()) return;
        List<Source> sources = host.events().get(event).sources; int selected = pip ? host.pipSource() : host.selectedSource();
        if (sources.isEmpty() || selected >= sources.size()) return;
        if (pip) host.startPip(sources.get(selected)); else host.preview(sources.get(selected)); host.invalidate();
    }

    private StateInput previewState() { return new StateInput() {
        public void tap(float x, float y) { }
        public int scroll(float deltaY) { return 0; }
        public void dpad(int key) {
            if (key != KeyEvent.KEYCODE_DPAD_LEFT && key != KeyEvent.KEYCODE_DPAD_RIGHT) return;
            int count = host.vpnAvailable() ? 3 : 2; int direction = key == KeyEvent.KEYCODE_DPAD_LEFT ? -1 : 1;
            host.setPreviewAction(Math.max(0, Math.min(count - 1, host.previewAction() + direction))); host.invalidate();
        }
        public void confirm() {
            if (host.previewAction() == 1) host.openPipEventPicker(); else if (host.previewAction() == 2) host.toggleVpnPreview();
            else { host.goTo(ScreenStates.PLAYER_STATE); host.enterFullscreen(); } host.invalidate();
        }
    }; }

    private StateInput playbackState() { return new StateInput() {
        public void tap(float x, float y) { } public int scroll(float deltaY) { return 0; }
        public void dpad(int key) {
            if (key == KeyEvent.KEYCODE_DPAD_UP || key == KeyEvent.KEYCODE_DPAD_DOWN) dpadPlayback(key == KeyEvent.KEYCODE_DPAD_UP ? -1 : 1);
            else if (host.state().isDual() && key == KeyEvent.KEYCODE_DPAD_RIGHT) host.promotePipToPrimary();
        }
        public void confirm() { }
    }; }

    private void dpadPlayback(int direction) {
        if (host.events().isEmpty()) return; Event event = host.events().get(host.selectedEvent()); if (event.sources.isEmpty()) return;
        int selected = NavigationState.clamp(host.selectedSource() + direction, event.sources.size()); host.setSelectedSource(selected); host.switchPrimary(event.sources.get(selected));
    }

    private int listOffset(ScreenState state) { OffsetReader reader = offsets.get(state); return reader == null ? 0 : reader.read(); }
    private int clampOffset(int value, int size) { return Math.max(0, Math.min(Math.max(0, size - host.visibleRows()), value)); }
    private int focus() { return Math.max(0, host.visibleRows() - 3); }
    private int offset(int selected, int size) { return NavigationState.offsetFor(selected, size, host.visibleRows(), focus()); }
    private boolean isConfirm(int key) { return key == KeyEvent.KEYCODE_DPAD_CENTER || key == KeyEvent.KEYCODE_ENTER; }
}
