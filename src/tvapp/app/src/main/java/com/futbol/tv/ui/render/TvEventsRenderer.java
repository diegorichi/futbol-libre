package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvEventsRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    private final boolean pip;
    public TvEventsRenderer(TvCanvasRenderer renderer, boolean pip) { this.renderer = renderer; this.pip = pip; }
    @Override public void render(Canvas canvas) { renderer.renderBackground(canvas, c -> renderer.drawEvents(c, pip)); }
}
