package com.futbol.tv.ui.layout;

public final class TvTelevisionLayout implements TvLayoutProfile {
    @Override public boolean compact() { return false; }
    @Override public float eventRow(float widthDp, float heightDp) { return TvLayoutMetrics.TV_EVENT_ROW_DP; }
    @Override public float eventListTop(float widthDp, float heightDp) { return 135; }
    @Override public int visibleRows(float widthDp, float heightDp) { return TvLayoutMetrics.visibleRows(false, widthDp, heightDp); }
    @Override public float horizontalInset() { return 55; }
    @Override public float headerY() { return 62; }
    @Override public float headerSubtitleY() { return 96; }
    @Override public float headerTitleSize() { return 30; }
    @Override public float headerSubtitleSize() { return 16; }
    @Override public float eventTimeX() { return 70; }
    @Override public float eventTitleX() { return 170; }
    @Override public float eventTitleSize() { return 18; }
    @Override public float eventSourcesSize() { return 16; }
    @Override public float sourceTop() { return 170; }
    @Override public float footerY(float heightDp) { return heightDp - 24; }
    @Override public float footerX() { return 70; }
    @Override public float footerSize() { return 16; }
    @Override public float sourceTextX() { return 85; }
    @Override public float sourceTextSize() { return 20; }
    @Override public float sourceCountWidth() { return 155; }
    @Override public float sourceCountY() { return 135; }
    @Override public float sourceRightInset() { return 55; }
}
