package com.futbol.tv.ui.render;

import android.graphics.Canvas;

import com.futbol.tv.state.ScreenState;
import com.futbol.tv.state.ScreenStates;

import java.util.HashMap;
import java.util.Map;

/** Selects rendering behavior from the active ScreenState. */
public final class TvCanvasStateRenderer {
    private final Map<ScreenState, TvStateRenderer> renderers = new HashMap<>();

    public TvCanvasStateRenderer(TvCanvasRenderer renderer) {
        renderers.put(ScreenStates.SEARCHING_STATE, new TvLoadingRenderer(renderer));
        renderers.put(ScreenStates.ERROR_STATE, new TvErrorRenderer(renderer));
        renderers.put(ScreenStates.UPDATE_STATE, new TvUpdateRenderer(renderer));
        renderers.put(ScreenStates.EVENTS_STATE, new TvEventsRenderer(renderer, false));
        renderers.put(ScreenStates.SOURCES_STATE, new TvSourcesRenderer(renderer));
        renderers.put(ScreenStates.PIP_EVENTS_STATE, new TvEventsRenderer(renderer, true));
        renderers.put(ScreenStates.PIP_SOURCES_STATE, new TvPipSourcesRenderer(renderer));
        renderers.put(ScreenStates.PREVIEW_STATE, new TvPreviewRenderer(renderer));
    }

    public void render(Canvas canvas, ScreenState state) {
        TvStateRenderer action = renderers.get(state);
        if (action != null) action.render(canvas);
    }
}
