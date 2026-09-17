package com.futbol.tv;

import com.futbol.tv.ui.layout.TvLayoutMetrics;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class TvLayoutMetricsTest {
    @Test public void previewUsesTheSameControlsForPortraitHitTesting() {
        TvLayoutMetrics.PreviewLayout layout = TvLayoutMetrics.preview(360f, 640f, 24f, true, true);
        assertEquals(2, layout.controlAt(layout.fullscreen.left + 4f, layout.fullscreen.top + 4f));
        assertEquals(4, layout.controlAt(layout.pip.left + 4f, layout.pip.top + 4f));
        assertEquals(3, layout.controlAt(layout.vpn.left + 4f, layout.vpn.top + 4f));
    }

    @Test public void compactControlsKeepA48DpInteractionHeight() {
        TvLayoutMetrics.PreviewLayout layout = TvLayoutMetrics.preview(360f, 640f, 24f, true, false);
        assertTrue(layout.fullscreen.contains(layout.fullscreen.left + 4f, layout.fullscreen.top - 6f));
        assertEquals(-1, layout.controlAt(0f, 0f));
    }

    @Test public void tvPreviewKeepsThreeActionsAligned() {
        TvLayoutMetrics.PreviewLayout layout = TvLayoutMetrics.preview(1920f, 1080f, 0f, false, true);
        assertEquals(2, layout.controlAt(layout.fullscreen.left + 10f, layout.fullscreen.top + 10f));
        assertEquals(4, layout.controlAt(layout.pip.left + 10f, layout.pip.top + 10f));
        assertEquals(3, layout.controlAt(layout.vpn.left + 10f, layout.vpn.top + 10f));
    }

    @Test public void listHitTestingUsesTheSameRowCentersAsDrawing() {
        assertEquals(0, TvLayoutMetrics.eventIndexAt(125f, 0, 0f, true, 360f, 640f));
        assertEquals(1, TvLayoutMetrics.eventIndexAt(213f, 0, 0f, true, 360f, 640f));
        assertEquals(0, TvLayoutMetrics.sourceIndexAt(160f, 0, 0f, true));
        assertEquals(1, TvLayoutMetrics.sourceIndexAt(208f, 0, 0f, true));
    }
}
