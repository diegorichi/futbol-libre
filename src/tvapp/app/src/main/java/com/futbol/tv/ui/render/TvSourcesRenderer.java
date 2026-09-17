package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvSourcesRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvSourcesRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.renderBackground(canvas, renderer::drawSources); }
}
