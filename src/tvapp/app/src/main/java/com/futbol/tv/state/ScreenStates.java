package com.futbol.tv.state;

/** Registry of the application screen-state objects. */
public final class ScreenStates {
    private ScreenStates() { }

    private static final ScreenState.BackAction EXIT = (target, handler) -> handler.exit();
    private static final ScreenState.BackAction NAVIGATE = (target, handler) -> {
        handler.navigate(target);
        handler.invalidate();
    };
    public static final ScreenState SEARCHING_STATE = new ScreenState(null, false, false, false, ScreenState.ListMode.NONE, false, NAVIGATE);
    public static final ScreenState EVENTS_STATE = new ScreenState(SEARCHING_STATE, true, false, true, ScreenState.ListMode.EVENTS, false, EXIT);
    public static final ScreenState SOURCES_STATE = new ScreenState(EVENTS_STATE, false, false, true, ScreenState.ListMode.SOURCES, false, NAVIGATE);
    public static final ScreenState PREVIEW_STATE = new ScreenState(SOURCES_STATE, false, false, false, ScreenState.ListMode.NONE, false, (target, handler) -> {
        handler.stopPrimary();
        handler.releasePlayback();
        NAVIGATE.apply(target, handler);
    });
    public static final ScreenState PLAYER_STATE = new ScreenState(PREVIEW_STATE, false, true, false, ScreenState.ListMode.NONE, false, (target, handler) -> {
        handler.showPreview();
        NAVIGATE.apply(target, handler);
    });
    public static final ScreenState ERROR_STATE = new ScreenState(null, true, false, false, ScreenState.ListMode.NONE, false, EXIT);
    public static final ScreenState PIP_EVENTS_STATE = new ScreenState(PREVIEW_STATE, false, false, true, ScreenState.ListMode.EVENTS, true, NAVIGATE);
    public static final ScreenState PIP_SOURCES_STATE = new ScreenState(PIP_EVENTS_STATE, false, false, true, ScreenState.ListMode.SOURCES, true, NAVIGATE);
    public static final ScreenState DUAL_STATE = new ScreenState(PLAYER_STATE, false, true, false, ScreenState.ListMode.NONE, false, (target, handler) -> {
        handler.closePip();
        NAVIGATE.apply(target, handler);
    });
    public static final ScreenState UPDATE_STATE = new ScreenState(EVENTS_STATE, false, false, false, ScreenState.ListMode.NONE, false, (target, handler) -> {
        handler.clearPendingUpdate();
        NAVIGATE.apply(target, handler);
    });

}
