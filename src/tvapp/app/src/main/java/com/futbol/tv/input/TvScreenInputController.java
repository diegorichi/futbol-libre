package com.futbol.tv.input;

import android.view.KeyEvent;
import android.view.MotionEvent;

import com.futbol.tv.TvScreenView;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.ui.layout.TvLayoutMetrics;
import com.futbol.tv.ui.layout.TvLayoutProfile;
import com.futbol.tv.ui.render.TvCanvasRenderer;

/** Translates Android view events into semantic host actions and scrolling. */
public final class TvScreenInputController {
    private final TvScreenView view;
    private final TvScreenView.Host host;
    private final TvLayoutProfile layout;
    private final TvCanvasRenderer canvas;
    private final float density;
    private float downX;
    private float downY;
    private float dragY;
    private float startDragY;
    private boolean dragging;

    public TvScreenInputController(TvScreenView view, TvScreenView.Host host,
                                   TvLayoutProfile layout, TvCanvasRenderer canvas) {
        this.view = view;
        this.host = host;
        this.layout = layout;
        this.canvas = canvas;
        density = view.getResources().getDisplayMetrics().density;
    }

    public float dragOffsetDp() { return dragY; }

    public boolean onKeyDown(int keyCode) {
        if (keyCode == KeyEvent.KEYCODE_BACK) host.onBack();
        else if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER || keyCode == KeyEvent.KEYCODE_ENTER) host.onConfirm();
        else host.onDpad(keyCode);
        return true;
    }

    public boolean onTouchEvent(MotionEvent event) {
        ScreenState state = host.state();
        if (state.isPlayback()) return false;
        if (state.isPreview() && layout.compact()) {
            int control = previewControlAt(event.getX() / density, event.getY() / density);
            if (control >= 0) {
                if (event.getAction() == MotionEvent.ACTION_UP) host.onPlaybackControl(control);
                return true;
            }
        }
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            downX = event.getX(); downY = event.getY(); startDragY = dragY; dragging = false;
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_MOVE && layout.compact() && state.isScrollable()) {
            float dy = (event.getY() - downY) / density;
            if (Math.abs(dy) > 8) dragging = true;
            if (dragging) {
                dragY = clampDrag(startDragY + dy, state);
                syncCanvas();
                view.invalidate();
            }
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_UP) {
            float dx = (event.getX() - downX) / density;
            float dy = (event.getY() - downY) / density;
            if (dragging) {
                int movedRows = host.onScroll(dragY - startDragY);
                dragY = clampDrag(dragY + movedRows * rowDp(state), state);
                dragging = false;
                syncCanvas();
                view.invalidate();
            } else if (Math.abs(dy) > 32 && Math.abs(dy) > Math.abs(dx)) {
                host.onSwipe(dy < 0);
            } else {
                dragY = 0;
                syncCanvas();
                host.onTouch(event.getX() / density, event.getY() / density);
            }
        }
        if (event.getAction() == MotionEvent.ACTION_CANCEL) {
            dragY = 0;
            dragging = false;
            syncCanvas();
            view.invalidate();
        }
        return true;
    }

    private void syncCanvas() { canvas.setDragOffset(dragY); }
    private float widthDp() { return view.getWidth() / density; }
    private float heightDp() { return view.getHeight() / density; }
    private float rowDp(ScreenState state) { return state.eventListVisible() ? layout.eventRow(widthDp(), heightDp()) : 48f; }
    private int visibleRows() { return layout.visibleRows(widthDp(), heightDp()); }

    private int previewControlAt(float x, float y) {
        return TvLayoutMetrics.preview(widthDp(), heightDp(), safeBottomDp(), layout.compact(), host.vpnAvailable())
                .controlAt(x, y);
    }

    private int offsetRows(ScreenState state) {
        if (state.eventListVisible()) return state.isPipList() ? host.pipEventOffset() : host.eventOffset();
        if (state.sourceListVisible()) return state.isPipList() ? host.pipSourceOffset() : host.sourceOffset();
        return 0;
    }

    private int maxOffsetRows(ScreenState state) {
        if (state.eventListVisible()) return Math.max(0, host.events().size() - visibleRows());
        if (!state.sourceListVisible() || host.events().isEmpty()) return 0;
        int event = state.isPipList() ? host.pipEvent() : host.selectedEvent();
        if (event >= host.events().size()) return 0;
        return Math.max(0, host.events().get(event).sources.size() - visibleRows());
    }

    private float clampDrag(float value, ScreenState state) {
        float row = rowDp(state);
        float current = offsetRows(state) * row;
        float min = current - maxOffsetRows(state) * row;
        return Math.max(min, Math.min(current, value));
    }

    private float safeBottomDp() {
        android.view.WindowInsets insets = view.getRootWindowInsets();
        if (insets != null) return Math.max(24f, insets.getSystemWindowInsetBottom() / density);
        return 56f;
    }
}
