package com.futbol.tv;

import com.futbol.tv.state.ScreenStates;
import com.futbol.tv.state.TvNavigationController;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class TvNavigationControllerTest {
    @Test public void backReturnsToPreviousScreen() {
        TvNavigationController navigation = new TvNavigationController();
        navigation.goTo(ScreenStates.SOURCES_STATE);
        assertEquals(ScreenStates.SOURCES_STATE, navigation.current());
        assertEquals(ScreenStates.EVENTS_STATE, navigation.backTarget());
        navigation.goTo(ScreenStates.PREVIEW_STATE);
        assertEquals(ScreenStates.SOURCES_STATE, navigation.backTarget());
        navigation.goTo(ScreenStates.DUAL_STATE);
        assertEquals(ScreenStates.PLAYER_STATE, navigation.backTarget());
        assertTrue(navigation.current().isPlayback());
    }

    @Test public void eventsAndErrorsExitOnBack() {
        TvNavigationController navigation = new TvNavigationController();
        navigation.goTo(ScreenStates.EVENTS_STATE);
        assertTrue(navigation.exitsOnBack());
        navigation.goTo(ScreenStates.ERROR_STATE);
        assertTrue(navigation.exitsOnBack());
    }

    @Test public void updateBackContinuesToEvents() {
        TvNavigationController navigation = new TvNavigationController();
        navigation.goTo(ScreenStates.UPDATE_STATE);
        assertEquals(ScreenStates.EVENTS_STATE, navigation.backTarget());
    }

    @Test public void searchingBackDoesNotInventAState() {
        TvNavigationController navigation = new TvNavigationController();
        assertEquals(ScreenStates.SEARCHING_STATE, navigation.backTarget());
    }

    @Test public void statesExposeListBehaviorWithoutConsumerComparisons() {
        assertTrue(ScreenStates.EVENTS_STATE.eventListVisible());
        assertTrue(!ScreenStates.EVENTS_STATE.sourceListVisible());
        assertTrue(ScreenStates.PIP_EVENTS_STATE.eventListVisible());
        assertTrue(ScreenStates.PIP_EVENTS_STATE.isPipList());
        assertTrue(ScreenStates.SOURCES_STATE.sourceListVisible());
        assertTrue(!ScreenStates.SOURCES_STATE.isPipList());
        assertTrue(ScreenStates.PIP_SOURCES_STATE.sourceListVisible());
    }
}
