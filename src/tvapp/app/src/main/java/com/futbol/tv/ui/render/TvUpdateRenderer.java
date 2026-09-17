package com.futbol.tv.ui.render;

import android.graphics.Canvas;

public final class TvUpdateRenderer implements TvStateRenderer {
    private final TvCanvasRenderer renderer;
    public TvUpdateRenderer(TvCanvasRenderer renderer) { this.renderer = renderer; }
    @Override public void render(Canvas canvas) { renderer.drawUpdate(canvas); }
}
