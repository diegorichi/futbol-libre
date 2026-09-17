package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvErrorRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvErrorRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.renderError(canvas); }
}
