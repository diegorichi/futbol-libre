package com.futbol.tv.ui.render;

import android.graphics.Canvas;
import android.graphics.Paint;

/** Draws the single soccer-ball loading indicator used by all TV states. */
public final class TvSoccerBallRenderer {
    private final float density;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

    public TvSoccerBallRenderer(float density) {
        this.density = density;
    }

    public void draw(Canvas canvas, float centerX, float centerY, float radius, float rotation) {
        canvas.save();
        canvas.rotate(rotation, dp(centerX), dp(centerY));
        paint.setTextSize(dp(radius * 2.16f));
        paint.setTextAlign(Paint.Align.CENTER);
        float baseline = dp(centerY) - (paint.ascent() + paint.descent()) / 2f;
        canvas.drawText("⚽", dp(centerX), baseline, paint);
        canvas.restore();
    }

    private float dp(float value) { return value * density; }
}
