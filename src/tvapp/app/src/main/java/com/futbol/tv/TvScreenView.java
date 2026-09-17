package com.futbol.tv;

import android.content.Context;
import android.graphics.Canvas;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.widget.FrameLayout;

import com.futbol.tv.input.TvScreenInputController;
import com.futbol.tv.model.Event;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.ui.layout.TvCompactLayout;
import com.futbol.tv.ui.layout.TvLayoutProfile;
import com.futbol.tv.ui.layout.TvTelevisionLayout;
import com.futbol.tv.ui.list.TvListBinder;
import com.futbol.tv.ui.render.TvCanvasRenderer;
import com.futbol.tv.ui.render.TvCanvasStateRenderer;

import java.util.List;

/** Android view adapter: composition, lifecycle and delegation only. */
public final class TvScreenView extends FrameLayout {
    public interface Host {
        ScreenState state();
        List<Event> events();
        int selectedEvent(); int eventOffset(); int selectedSource(); int sourceOffset();
        int pipEvent(); int pipEventOffset(); int pipSource(); int pipSourceOffset();
        int previewAction(); boolean vpnAvailable(); boolean vpnActive(); boolean previewLoading(); String playerMessage();
        String updateVersion(); String updateStatus();
        void onBack(); void onDpad(int keyCode); void onConfirm(); void onTouch(float x, float y); void onSwipe(boolean down); int onScroll(float deltaY);
        void onEventTap(int index, boolean forPip); void onSourceTap(int index, boolean forPip); void onPlaybackControl(int control);
    }

    private final Host host;
    private final TvLayoutProfile layout;
    private final TvListBinder lists;
    private final TvCanvasRenderer canvas;
    private final TvCanvasStateRenderer stateRenderer;
    private final TvScreenInputController input;
    private ScreenState lastState;
    private boolean lastPreviewLoading;
    private float ballRotation;
    private final Runnable ballAnimation = new Runnable() {
        @Override public void run() {
            if (!host.state().isSearching() && !host.previewLoading()) return;
            ballRotation = (ballRotation + 8f) % 360f;
            invalidate();
            postDelayed(this, 45);
        }
    };

    public TvScreenView(Context context, Host host) {
        super(context);
        this.host = host;
        layout = getResources().getConfiguration().smallestScreenWidthDp < 600
                ? new TvCompactLayout() : new TvTelevisionLayout();
        setWillNotDraw(false);
        setFocusable(true);
        requestFocus();
        lists = new TvListBinder(context, host);
        addView(lists.eventList());
        addView(lists.sourceList());
        canvas = new TvCanvasRenderer(this, host, layout, lists);
        stateRenderer = new TvCanvasStateRenderer(canvas);
        input = new TvScreenInputController(this, host, layout, canvas);
    }

    public boolean isCompactLayout() { return layout.compact(); }
    public TvLayoutProfile layoutProfile() { return layout; }
    public float dragOffsetDp() { return input.dragOffsetDp(); }
    public int visibleRows() { return layout.visibleRows(widthDp(), heightDp()); }

    private float widthDp() { return getWidth() / getResources().getDisplayMetrics().density; }
    private float heightDp() { return getHeight() / getResources().getDisplayMetrics().density; }

    @Override protected void onDraw(Canvas canvas) {
        ScreenState state = host.state();
        lists.sync(state, getHeight(), getResources().getDisplayMetrics().density, layout.compact(), host);
        boolean previewLoading = host.previewLoading();
        if (state != lastState || previewLoading != lastPreviewLoading) {
            lastState = state;
            removeCallbacks(ballAnimation);
            if (state.isSearching() || previewLoading) post(ballAnimation);
        }
        lastPreviewLoading = previewLoading;
        this.canvas.setLoadingRotation(ballRotation);
        stateRenderer.render(canvas, state);
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        removeCallbacks(ballAnimation);
        if (host.state().isSearching() || host.previewLoading()) post(ballAnimation);
    }

    @Override protected void onDetachedFromWindow() {
        removeCallbacks(ballAnimation);
        super.onDetachedFromWindow();
    }

    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        return input.onKeyDown(keyCode);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        return input.onTouchEvent(event);
    }
}
