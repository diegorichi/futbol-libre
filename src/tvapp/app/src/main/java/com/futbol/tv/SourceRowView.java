package com.futbol.tv;

import com.futbol.tv.ui.layout.TvVisualTokens;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.View;

import com.futbol.tv.model.Source;

public final class SourceRowView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;
    private Source source;
    private boolean selected;

    public SourceRowView(Context context) { super(context); density = getResources().getDisplayMetrics().density; setMinimumHeight(dp(56)); }
    public void bind(Source source, boolean selected) { this.source = source; this.selected = selected; setContentDescription(source.name); invalidate(); }
    private int dp(float value) { return (int) (value * density + 0.5f); }
    @Override protected void onDraw(Canvas c) {
        if (source == null) return;
        float width = getWidth() / density;
        paint.setColor(selected ? TvVisualTokens.SURFACE : Color.TRANSPARENT);
        c.drawRoundRect(new RectF(dp(0), dp(1), getWidth(), getHeight() - dp(1)), dp(10), dp(10), paint);
        paint.setColor(Color.WHITE); paint.setTextSize(dp(18)); paint.setTypeface(selected ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        String name = source.name;
        while (name.length() > 1 && paint.measureText(name + "…") > dp(width - 48)) name = name.substring(0, name.length() - 1);
        c.drawText(name.equals(source.name) ? name : name + "…", dp(24), dp(36), paint);
    }
}
