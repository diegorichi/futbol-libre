package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvPipSourcesRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvPipSourcesRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.drawPipSources(canvas); }
}
