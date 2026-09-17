package com.futbol.tv.ui.layout;

import android.graphics.Color;

/** Shared visual tokens for the dark TV/mobile surface. */
public final class TvVisualTokens {
    private TvVisualTokens() { }

    public static final int BACKGROUND = Color.rgb(7, 17, 31);
    public static final int SURFACE = Color.rgb(25, 57, 77);
    public static final int SURFACE_SELECTED = Color.rgb(25, 122, 113);
    public static final int BORDER = Color.rgb(71, 96, 120);
    public static final int ACCENT = Color.rgb(94, 234, 212);
    public static final int DANGER = Color.rgb(127, 29, 29);
    public static final int DANGER_TEXT = Color.rgb(254, 202, 202);

    public static int withAlpha(int alpha, int color) {
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color));
    }
}
