package com.futbol.tv;

import com.futbol.tv.ui.layout.TvCompactLayout;
import com.futbol.tv.ui.layout.TvLayoutMetrics;
import com.futbol.tv.ui.layout.TvLayoutProfile;
import com.futbol.tv.ui.layout.TvTelevisionLayout;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class TvLayoutProfileTest {
    @Test public void profilesHaveStableIdentity() {
        TvLayoutProfile compact = new TvCompactLayout();
        TvLayoutProfile television = new TvTelevisionLayout();

        assertTrue(compact.compact());
        assertFalse(television.compact());
        assertTrue(compact.eventRow(390, 844) > 0);
        assertTrue(compact.eventRow(390, 844) == 88f);
        assertTrue(television.eventRow(1920, 1080) == TvLayoutMetrics.TV_EVENT_ROW_DP);
    }
}
