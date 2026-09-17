package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvPreviewRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvPreviewRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.drawPreview(canvas); }
}
