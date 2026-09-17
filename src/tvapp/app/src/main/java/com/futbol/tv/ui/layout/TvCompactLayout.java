package com.futbol.tv.ui.layout;

public final class TvCompactLayout implements TvLayoutProfile {
    @Override public boolean compact() { return true; }
    @Override public float eventRow(float widthDp, float heightDp) { return TvLayoutMetrics.compactEventRow(widthDp, heightDp); }
    @Override public float eventListTop(float widthDp, float heightDp) { return TvLayoutMetrics.compactEventListTop(widthDp, heightDp); }
    @Override public int visibleRows(float widthDp, float heightDp) { return TvLayoutMetrics.visibleRows(true, widthDp, heightDp); }
    @Override public float horizontalInset() { return 16; }
    @Override public float headerY() { return 42; }
    @Override public float headerSubtitleY() { return 68; }
    @Override public float headerTitleSize() { return 24; }
    @Override public float headerSubtitleSize() { return 14; }
    @Override public float eventTimeX() { return 24; }
    @Override public float eventTitleX() { return 92; }
    @Override public float eventTitleSize() { return 16; }
    @Override public float eventSourcesSize() { return 13; }
    @Override public float sourceTop() { return 135; }
    @Override public float footerY(float heightDp) { return heightDp - 24; }
    @Override public float footerX() { return 24; }
    @Override public float footerSize() { return 13; }
    @Override public float sourceTextX() { return 32; }
    @Override public float sourceTextSize() { return 17; }
    @Override public float sourceCountWidth() { return 95; }
    @Override public float sourceCountY() { return 124; }
    @Override public float sourceRightInset() { return 16; }
}
