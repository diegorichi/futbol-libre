package com.futbol.tv.ui.layout;

/** Pure layout calculations shared by drawing and hit-testing. Values are dp. */
public final class TvLayoutMetrics {
    public static final float TV_EVENT_ROW_DP = 72f;
    public static final float SOURCE_ROW_DP = 48f;
    public static final float LIST_BOTTOM_INSET_DP = 46f;
    public static final float COMPACT_MARGIN_DP = 16f;
    public static final float CONTROL_GAP_DP = 8f;

    private TvLayoutMetrics() { }

    public static float compactEventRow(float widthDp, float heightDp) {
        if (heightDp >= widthDp) return 88f;
        return Math.max(56f, Math.min(76f, (heightDp - 130f) / 3f));
    }

    public static float compactEventListTop(float widthDp, float heightDp) {
        return heightDp >= widthDp ? 125f : 96f;
    }

    public static int visibleRows(boolean compact, float widthDp, float heightDp) {
        if (!compact) return 8;
        float row = compactEventRow(widthDp, heightDp);
        return Math.max(1, Math.min(8,
                (int) ((heightDp - compactEventListTop(widthDp, heightDp) - 35f) / row)));
    }

    public static PreviewLayout preview(float widthDp, float heightDp, float safeBottomDp,
                                        boolean compact, boolean vpnAvailable) {
        return new PreviewLayout(widthDp, heightDp, safeBottomDp, compact, vpnAvailable);
    }

    public static int eventIndexAt(float y, int offset, float dragOffsetDp,
                                   boolean compact, float widthDp, float heightDp) {
        float row = compact ? compactEventRow(widthDp, heightDp) : TV_EVENT_ROW_DP;
        float firstCenter = compact ? compactEventListTop(widthDp, heightDp) : 135f;
        return offset + (int) ((y - dragOffsetDp - (firstCenter - row / 2f)) / row);
    }

    public static int sourceIndexAt(float y, int offset, float dragOffsetDp, boolean compact) {
        float firstCenter = compact ? 160f : 170f;
        return offset + (int) ((y - dragOffsetDp - (firstCenter - SOURCE_ROW_DP / 2f)) / SOURCE_ROW_DP);
    }

    public static final class Bounds {
        public final float left;
        public final float top;
        public final float right;
        public final float bottom;

        private Bounds(float left, float top, float right, float bottom) {
            this.left = left;
            this.top = top;
            this.right = right;
            this.bottom = bottom;
        }

        public static Bounds of(float left, float top, float width, float height) {
            return new Bounds(left, top, left + width, top + height);
        }

        public boolean contains(float x, float y) {
            // The visual control may be 34dp high on compact playback, but
            // its interaction target remains at least 48dp high.
            float hitLeft = left - Math.max(0f, (48f - (right - left)) / 2f);
            float hitRight = right + Math.max(0f, (48f - (right - left)) / 2f);
            float hitTop = top - Math.max(0f, (48f - (bottom - top)) / 2f);
            float hitBottom = bottom + Math.max(0f, (48f - (bottom - top)) / 2f);
            return x >= hitLeft && x <= hitRight && y >= hitTop && y <= hitBottom;
        }
    }

    public static final class PreviewLayout {
        public final float panelTop;
        public final float panelBottom;
        public final float rowY;
        public final Bounds up;
        public final Bounds down;
        public final Bounds fullscreen;
        public final Bounds pip;
        public final Bounds vpn;

        private PreviewLayout(float widthDp, float heightDp, float safeBottomDp,
                              boolean compact, boolean vpnAvailable) {
            if (!compact) {
                panelBottom = heightDp;
                panelTop = Math.max(0f, heightDp - 125f);
                rowY = heightDp - 94f;
                float buttonWidth = vpnAvailable ? 210f : 260f;
                fullscreen = Bounds.of(60f, rowY, buttonWidth, 48f);
                pip = Bounds.of(68f + buttonWidth, rowY, buttonWidth, 48f);
                vpn = vpnAvailable ? Bounds.of(76f + buttonWidth * 2f, rowY, buttonWidth, 48f) : null;
                up = down = null;
                return;
            }

            panelBottom = Math.max(0f, heightDp - safeBottomDp);
            boolean portrait = heightDp >= widthDp;
            float panelHeight = portrait ? 232f : 156f;
            panelTop = Math.max(0f, panelBottom - panelHeight);
            rowY = panelTop + (portrait ? 62f : 48f);
            up = Bounds.of(COMPACT_MARGIN_DP, rowY - 25f, 42f, 34f);
            down = Bounds.of(COMPACT_MARGIN_DP, rowY + 25f, 42f, 34f);
            if (portrait) {
                int buttonCount = vpnAvailable ? 3 : 2;
                float buttonWidth = (widthDp - 2f * COMPACT_MARGIN_DP
                        - CONTROL_GAP_DP * (buttonCount - 1)) / buttonCount;
                // Keep the action row below the up/down controls. The old
                // independent hit-test placed these rows on top of each other.
                float buttonY = panelTop + 132f;
                fullscreen = Bounds.of(COMPACT_MARGIN_DP, buttonY, buttonWidth, 34f);
                pip = Bounds.of(COMPACT_MARGIN_DP + buttonWidth + CONTROL_GAP_DP,
                        buttonY, buttonWidth, 34f);
                vpn = vpnAvailable ? Bounds.of(COMPACT_MARGIN_DP + 2f * (buttonWidth + CONTROL_GAP_DP),
                        buttonY, buttonWidth, 34f) : null;
            } else {
                float right = widthDp - COMPACT_MARGIN_DP;
                float vpnWidth = vpnAvailable ? 58f : 0f;
                float pipWidth = 54f;
                float fullscreenWidth = 50f;
                float vpnX = right - vpnWidth;
                float pipX = vpnAvailable ? vpnX - CONTROL_GAP_DP - pipWidth : right - pipWidth;
                float fullscreenX = pipX - CONTROL_GAP_DP - fullscreenWidth;
                fullscreen = Bounds.of(fullscreenX, rowY - 17f, fullscreenWidth, 34f);
                pip = Bounds.of(pipX, rowY - 17f, pipWidth, 34f);
                vpn = vpnAvailable ? Bounds.of(vpnX, rowY - 17f, vpnWidth, 34f) : null;
            }
        }

        public int controlAt(float x, float y) {
            if (up != null && up.contains(x, y)) return 0;
            if (down != null && down.contains(x, y)) return 1;
            if (fullscreen != null && fullscreen.contains(x, y)) return 2;
            if (pip != null && pip.contains(x, y)) return 4;
            if (vpn != null && vpn.contains(x, y)) return 3;
            return -1;
        }
    }
}
