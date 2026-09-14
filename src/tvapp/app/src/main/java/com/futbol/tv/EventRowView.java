package com.futbol.tv;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.View;

import com.futbol.tv.model.Event;

/** Native RecyclerView row; drawing remains lightweight and focus-friendly for TV. */
public final class EventRowView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;
    private Event event;
    private boolean selected;
    private final boolean compact;

    public EventRowView(Context context) {
        super(context);
        density = getResources().getDisplayMetrics().density;
        compact = getResources().getConfiguration().smallestScreenWidthDp < 600;
        setMinimumHeight(dp(compact ? 88 : 96));
    }

    public void bind(Event event, boolean selected) {
        this.event = event;
        this.selected = selected;
        invalidate();
    }

    private int dp(float value) { return (int) (value * density + 0.5f); }
    private void text(Canvas c, String value, float x, float y, float size, int color, boolean bold) {
        paint.setColor(color); paint.setTextSize(dp(size));
        paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        c.drawText(value, dp(x), dp(y), paint);
    }
    private String fit(String value, float maxWidth, float size) {
        paint.setTextSize(dp(size));
        if (paint.measureText(value) <= dp(maxWidth)) return value;
        while (value.length() > 1 && paint.measureText(value + "…") > dp(maxWidth)) value = value.substring(0, value.length() - 1);
        return value + "…";
    }
    private String[] parts() {
        int separator = event.title.indexOf(':');
        if (separator > 0 && separator < event.title.length() - 1) {
            return new String[] { event.title.substring(0, separator).trim(), event.title.substring(separator + 1).trim() };
        }
        return new String[] { "", event.title };
    }

    @Override protected void onDraw(Canvas c) {
        if (event == null) return;
        float width = getWidth() / density;
        float baseline = compact ? 40 : 43;
        paint.setColor(selected ? Color.rgb(25, 57, 77) : Color.TRANSPARENT);
        c.drawRoundRect(new RectF(dp(0), dp(1), getWidth() - dp(0), getHeight() - dp(1)), dp(10), dp(10), paint);
        String time = event.startsAt.length() >= 16 ? event.startsAt.substring(11, 16) : "--:--";
        text(c, time, compact ? 24 : 24, baseline, compact ? 17 : 19, Color.rgb(94, 234, 212), true);
        String sources = event.sources.size() + " fuente" + (event.sources.size() == 1 ? "" : "s");
        paint.setTextSize(dp(compact ? 13 : 16));
        float sourceWidth = paint.measureText(sources) / density;
        float matchX = compact ? 92 : 170;
        float maxWidth = width - matchX - sourceWidth - 20;
        String[] parts = parts();
        if (parts[1].matches("(?s).*\\s+(?i:vs\\.?)\\s+.*")) {
            String[] teams = parts[1].split("\\s+(?i:vs\\.?)\\s+", 2);
            float size = compact ? 16 : 16;
            text(c, fit(teams[0], maxWidth, size), matchX, baseline - 13, size, Color.WHITE, selected);
            text(c, "VS", matchX, baseline + 3, compact ? 12 : 13, Color.rgb(94, 234, 212), true);
            text(c, fit(teams.length > 1 ? teams[1] : "", maxWidth, size), matchX, baseline + 19, size, Color.WHITE, selected);
            text(c, fit(parts[0], maxWidth, 11), matchX, baseline + 35, 11, Color.LTGRAY, false);
        } else {
            text(c, fit(parts[1], maxWidth, compact ? 18 : 18), matchX, baseline, compact ? 18 : 18, Color.WHITE, selected);
            text(c, fit(parts[0], maxWidth, 11), matchX, baseline + 22, 11, Color.LTGRAY, false);
        }
        text(c, sources, width - sourceWidth - 16, baseline - 5, compact ? 13 : 16, Color.LTGRAY, false);
    }
}
