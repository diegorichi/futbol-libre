package com.futbol.tv.state;

/** State-pattern object: transition and Back behavior belong to the active state. */
public final class ScreenState {
    public enum ListMode { NONE, EVENTS, SOURCES }

    public interface BackHandler {
        void exit();
        void closePip();
        void showPreview();
        void stopPrimary();
        void releasePlayback();
        void clearPendingUpdate();
        void navigate(ScreenState target);
        void invalidate();
    }

    public interface BackAction {
        void apply(ScreenState target, BackHandler handler);
    }

    private final ScreenState backTarget;
    private final boolean exitsOnBack;
    private final boolean playback;
    private final boolean scrollable;
    private final ListMode listMode;
    private final boolean pip;
    private final BackAction backAction;

    ScreenState(ScreenState backTarget, boolean exitsOnBack, boolean playback,
                boolean scrollable, ListMode listMode, boolean pip, BackAction backAction) {
        this.backTarget = backTarget == null ? this : backTarget;
        this.exitsOnBack = exitsOnBack;
        this.playback = playback;
        this.scrollable = scrollable;
        this.listMode = listMode;
        this.pip = pip;
        this.backAction = backAction;
    }

    public ScreenState backTarget() { return backTarget; }
    public boolean exitsOnBack() { return exitsOnBack; }
    public boolean isPlayback() { return playback; }
    public boolean isScrollable() { return scrollable; }
    public boolean eventListVisible() { return listMode == ListMode.EVENTS; }
    public boolean sourceListVisible() { return listMode == ListMode.SOURCES; }
    public boolean isPipList() { return pip && listMode != ListMode.NONE; }
    public boolean isSearching() { return this == ScreenStates.SEARCHING_STATE; }
    public boolean isPreview() { return this == ScreenStates.PREVIEW_STATE; }
    public boolean isDual() { return this == ScreenStates.DUAL_STATE; }

    public void onBack(BackHandler handler) {
        backAction.apply(backTarget, handler);
    }
}
