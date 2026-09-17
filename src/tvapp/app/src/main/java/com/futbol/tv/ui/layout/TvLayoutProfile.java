package com.futbol.tv.ui.layout;

/** Layout strategy selected once for the lifetime of the screen. */
public interface TvLayoutProfile {
    boolean compact();
    float eventRow(float widthDp, float heightDp);
    float eventListTop(float widthDp, float heightDp);
    int visibleRows(float widthDp, float heightDp);
    float horizontalInset();
    float headerY();
    float headerSubtitleY();
    float headerTitleSize();
    float headerSubtitleSize();
    float eventTimeX();
    float eventTitleX();
    float eventTitleSize();
    float eventSourcesSize();
    float sourceTop();
    float footerY(float heightDp);
    float footerX();
    float footerSize();
    float sourceTextX();
    float sourceTextSize();
    float sourceCountWidth();
    float sourceCountY();
    float sourceRightInset();
}
