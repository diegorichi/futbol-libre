package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvLoadingRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvLoadingRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.renderBackground(canvas, renderer::drawLoading); }
}
