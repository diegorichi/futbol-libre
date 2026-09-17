package com.futbol.tv.state;

/** Pure navigation state holder. Side effects stay in MainActivity. */
public final class TvNavigationController {
    private ScreenState state = ScreenStates.SEARCHING_STATE;

    public ScreenState current() {
        return state;
    }

    public void goTo(ScreenState nextState) {
        state = nextState;
    }

    public void back(ScreenState.BackHandler handler) {
        state.onBack(handler);
    }

    public ScreenState backTarget() {
        return state.backTarget();
    }

    public boolean exitsOnBack() {
        return state.exitsOnBack();
    }
}
