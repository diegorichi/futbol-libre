package com.futbol.tv.input;

import android.view.KeyEvent;
import android.view.MotionEvent;

import com.futbol.tv.TvScreenView;
import com.futbol.tv.state.ScreenState;
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
        boolean portrait = heightDp() >= widthDp();
        float bottom = heightDp() - safeBottomDp();
        float top = Math.max(0, bottom - (portrait ? 232f : 156f));
        float rowY = top + (portrait ? 62 : 48);
        float margin = 16, gap = 8;
        if (x >= margin && x < margin + 42 && y >= rowY - 25 && y <= rowY + 9) return 0;
        if (x >= margin && x < margin + 42 && y >= rowY + 25 && y <= rowY + 59) return 1;
        if (portrait) {
            int count = host.vpnAvailable() ? 3 : 2;
            float width = (widthDp() - 2 * margin - gap * (count - 1)) / count;
            float buttonY = top + 108;
            if (x >= margin && x < margin + width && y >= buttonY && y <= buttonY + 34) return 2;
            if (x >= margin + width + gap && x < margin + 2 * width + gap && y >= buttonY && y <= buttonY + 34) return 4;
            if (host.vpnAvailable() && x >= margin + 2 * (width + gap) && y >= buttonY && y <= buttonY + 34) return 3;
            return -1;
        }
        float right = widthDp() - margin;
        float vpnWidth = host.vpnAvailable() ? 58 : 0;
        float pipWidth = 54, fullscreenWidth = 50;
        float vpnX = right - vpnWidth;
        float pipX = host.vpnAvailable() ? vpnX - gap - pipWidth : right - pipWidth;
        float fullscreenX = pipX - gap - fullscreenWidth;
        if (x >= fullscreenX && x < fullscreenX + fullscreenWidth && y >= rowY - 17 && y <= rowY + 17) return 2;
        if (x >= pipX && x < pipX + pipWidth && y >= rowY - 17 && y <= rowY + 17) return 4;
        if (host.vpnAvailable() && x >= vpnX && x < vpnX + vpnWidth && y >= rowY - 17 && y <= rowY + 17) return 3;
        return -1;
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
