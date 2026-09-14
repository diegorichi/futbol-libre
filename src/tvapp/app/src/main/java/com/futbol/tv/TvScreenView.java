package com.futbol.tv;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Handler;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.Gravity;
import android.widget.FrameLayout;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.futbol.tv.model.Event;

import java.util.List;

/** Dumb TV canvas: drawing and input forwarding only. */
public final class TvScreenView extends FrameLayout {
    public static final int SEARCHING = 0, EVENTS = 1, SOURCES = 2, PREVIEW = 3,
            PLAYER = 4, ERROR = 5, PIP_EVENTS = 6, PIP_SOURCES = 7, DUAL = 8, UPDATE = 9;

    public interface Host {
        int state();
        List<Event> events();
        int selectedEvent(); int eventOffset(); int selectedSource(); int sourceOffset();
        int pipEvent(); int pipEventOffset(); int pipSource(); int pipSourceOffset();
        int previewAction(); String playerMessage(); Bitmap logo(String url); String playbackLabel();
        String updateVersion(); String updateStatus();
        void onBack(); void onDpad(int keyCode); void onConfirm(); void onTouch(float x, float y); void onSwipe(boolean down); int onScroll(float deltaY);
        void onEventTap(int index, boolean forPip); void onSourceTap(int index, boolean forPip);
    }

    private final Host host;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;
    private final Handler overlayHandler = new Handler();
    private final RecyclerView eventList;
    private final RecyclerView sourceList;
    private final EventListAdapter eventAdapter;
    private SourceListAdapter sourceAdapter;
    private String listKey = "";
    private boolean listForPip;
    private boolean playbackOverlayVisible;
    private float downX;
    private float downY;
    private float dragY;
    private float startDragY;
    private boolean dragging;
    private int lastState = -1;
    private float ballRotation;
    private final Runnable ballAnimation = new Runnable() {
        @Override public void run() {
            ballRotation = (ballRotation + 8f) % 360f;
            invalidate();
            postDelayed(this, 45);
        }
    };

    public TvScreenView(Context context, Host host) {
        super(context);
        this.host = host;
        density = getResources().getDisplayMetrics().density;
        setWillNotDraw(false);
        setFocusable(true);
        requestFocus();
        eventList = new RecyclerView(context);
        eventList.setLayoutManager(new LinearLayoutManager(context));
        eventList.setOverScrollMode(OVER_SCROLL_IF_CONTENT_SCROLLS);
        eventList.setFocusable(false);
        eventList.setDescendantFocusability(FOCUS_BLOCK_DESCENDANTS);
        eventAdapter = new EventListAdapter(host.events(), index -> host.onEventTap(index, listForPip));
        eventList.setAdapter(eventAdapter);
        sourceList = new RecyclerView(context);
        sourceList.setLayoutManager(new LinearLayoutManager(context));
        sourceList.setOverScrollMode(OVER_SCROLL_IF_CONTENT_SCROLLS);
        sourceList.setFocusable(false);
        sourceList.setDescendantFocusability(FOCUS_BLOCK_DESCENDANTS);
        eventList.setVisibility(GONE);
        sourceList.setVisibility(GONE);
        addView(eventList);
        addView(sourceList);
    }

    private float d(float value) { return value * density; }
    private float widthDp() { return getWidth() / density; }
    private float heightDp() { return getHeight() / density; }
    private boolean compactLayout() {
        return getResources().getConfiguration().smallestScreenWidthDp < 600;
    }
    public boolean isCompactLayout() { return compactLayout(); }
    private float compactEventRow() {
        if (heightDp() >= widthDp()) return 88f;
        return Math.max(56f, Math.min(76f, (heightDp() - 130f) / 3f));
    }
    private float compactEventListTop() { return heightDp() >= widthDp() ? 125f : 96f; }
    private static final float TV_EVENT_ROW = 72f;
    private float eventRow() { return compactLayout() ? compactEventRow() : TV_EVENT_ROW; }
    private float eventListTop() { return compactLayout() ? compactEventListTop() : 135f; }
    public float compactEventRowDp() { return compactEventRow(); }
    public float compactEventListTopDp() { return compactEventListTop(); }
    public float dragOffsetDp() { return dragY; }
    public int visibleRows() {
        if (!compactLayout()) return 8;
        return Math.max(1, Math.min(8, (int) ((heightDp() - compactEventListTop() - 35f) / compactEventRow())));
    }
    private String fit(String value, float maxWidthDp, float sizeDp) {
        if (value == null) return "";
        paint.setTextSize(d(sizeDp));
        if (paint.measureText(value) <= d(maxWidthDp)) return value;
        String suffix = "…";
        while (value.length() > 1 && paint.measureText(value + suffix) > d(maxWidthDp)) {
            value = value.substring(0, value.length() - 1);
        }
        return value + suffix;
    }
    private void text(Canvas c, String value, float x, float y, float size, int color, boolean bold) {
        paint.setColor(color); paint.setTextSize(d(size));
        paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        c.drawText(value, d(x), d(y), paint);
    }

    private int dp(float value) { return (int) (value * density + 0.5f); }

    private void syncLists() {
        int state = host.state();
        boolean eventsState = state == EVENTS || state == PIP_EVENTS;
        boolean sourcesState = state == SOURCES || state == PIP_SOURCES;
        eventList.setVisibility(eventsState ? VISIBLE : GONE);
        sourceList.setVisibility(sourcesState ? VISIBLE : GONE);
        if (eventsState) {
            listForPip = state == PIP_EVENTS;
            String key = state + ":" + host.events().size() + ":" + host.selectedEvent() + ":" + host.pipEvent();
            if (!key.equals(listKey)) {
                listKey = key;
                eventAdapter.setSelected(listForPip ? host.pipEvent() : host.selectedEvent());
                eventList.scrollToPosition(listForPip ? host.pipEvent() : host.selectedEvent());
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1, Math.max(0, getHeight() - dp(compactLayout() ? 82 : 98) - dp(46)));
            params.topMargin = dp(compactLayout() ? 82 : 98);
            eventList.setLayoutParams(params);
        } else if (sourcesState && !host.events().isEmpty()) {
            listForPip = state == PIP_SOURCES;
            int eventIndex = listForPip ? host.pipEvent() : host.selectedEvent();
            if (eventIndex < host.events().size()) {
                String key = state + ":" + eventIndex + ":" + host.events().get(eventIndex).sources.size() + ":" + host.selectedSource() + ":" + host.pipSource();
                if (!key.equals(listKey)) {
                    listKey = key;
                    sourceAdapter = new SourceListAdapter(host.events().get(eventIndex).sources, index -> host.onSourceTap(index, listForPip));
                    sourceAdapter.setSelected(listForPip ? host.pipSource() : host.selectedSource());
                    sourceList.setAdapter(sourceAdapter);
                    sourceList.scrollToPosition(listForPip ? host.pipSource() : host.selectedSource());
                }
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1, Math.max(0, getHeight() - dp(compactLayout() ? 108 : 122) - dp(46)));
            params.topMargin = dp(compactLayout() ? 108 : 122);
            sourceList.setLayoutParams(params);
        }
    }

    @Override protected void onDraw(Canvas c) {
        int state = host.state();
        syncLists();
        if (state != lastState) {
            dragY = 0;
            lastState = state;
        }
        if (state == PREVIEW || state == PLAYER || state == DUAL) {
            if (state == PREVIEW) drawPreview(c);
            if (state == PLAYER || state == DUAL) drawPlaybackOverlay(c);
            return;
        }
        c.drawColor(Color.rgb(7, 17, 31));
        if (state == SEARCHING) { drawLoading(c); return; }
        if (state == ERROR) { text(c, "No se encontró el servidor", 80, 90, 28, Color.WHITE, true); text(c, "Back para salir · OK para reintentar", 80, 135, 18, Color.LTGRAY, false); return; }
        if (state == UPDATE) { drawUpdate(c); return; }
        if (state == EVENTS) drawEvents(c, false);
        if (state == SOURCES) drawSources(c);
        if (state == PIP_EVENTS) drawEvents(c, true);
        if (state == PIP_SOURCES) drawPipSources(c);
    }

    private void header(Canvas c, String title) {
        float x = compactLayout() ? 24 : 70;
        text(c, fit(title, widthDp() - x * 2, compactLayout() ? 24 : 30), x, compactLayout() ? 42 : 62, compactLayout() ? 24 : 30, Color.WHITE, true);
        text(c, "Fútbol TV", x, compactLayout() ? 68 : 96, compactLayout() ? 14 : 16, Color.rgb(94,234,212), true);
    }

    private void drawEvents(Canvas c, boolean forPip) {
        List<Event> events = host.events();
        header(c, forPip ? "Elegí el segundo evento para PiP" : "Eventos");
        if (events.isEmpty()) { text(c, "No hay eventos disponibles", compactLayout() ? 24 : 80, compactLayout() ? 130 : 170, 22, Color.LTGRAY, false); return; }
        if (eventList.getVisibility() == VISIBLE) {
            text(c, forPip ? "El principal sigue reproduciendo" : (compactLayout() ? "Tocá un evento · Deslizá para desplazarte" : "OK para seleccionar · Flechas para desplazarte"), compactLayout() ? 24 : 70, heightDp() - 24, compactLayout() ? 13 : 16, Color.LTGRAY, false);
            return;
        }
        if (compactLayout()) { drawCompactEvents(c, events, forPip); return; }
        int offset = forPip ? host.pipEventOffset() : host.eventOffset();
        int selected = forPip ? host.pipEvent() : host.selectedEvent();
        int rows = visibleRows();
        float left = compactLayout() ? 16 : 55;
        float right = compactLayout() ? widthDp() - 16 : widthDp() - 55;
        for (int i = offset; i < Math.min(events.size(), offset + rows); i++) {
            Event event = events.get(i); float y = eventListTop() + (i - offset) * eventRow();
            if (i == selected) { paint.setColor(Color.rgb(25, 57, 77)); c.drawRoundRect(d(left), d(y - 34), d(right), d(y + 38), d(8), d(8), paint); }
            float timeX = compactLayout() ? 24 : 70;
            text(c, event.startsAt.length() >= 16 ? event.startsAt.substring(11, 16) : "--:--", timeX, y, compactLayout() ? 17 : 19, Color.rgb(94,234,212), true);
            float titleX = compactLayout() ? 92 : 170;
            String sources = event.sources.size() + " fuente" + (event.sources.size() == 1 ? "" : "s");
            paint.setTextSize(d(compactLayout() ? 13 : 16));
            float sourceWidth = paint.measureText(sources) / density;
            drawMatch(c, event, titleX, y, right - titleX - sourceWidth - 12, compactLayout() ? 16 : 18, i == selected);
            text(c, sources, right - sourceWidth, y - 5, compactLayout() ? 13 : 16, Color.LTGRAY, false);
        }
        text(c, forPip ? (compactLayout() ? "Tocá un evento para elegir su fuente" : "El principal sigue reproduciendo · OK para ver sus fuentes") : (compactLayout() ? "Tocá un evento · Deslizá para desplazarte" : "OK para seleccionar · Flechas para desplazarte"), compactLayout() ? 24 : 70, heightDp() - 24, compactLayout() ? 13 : 16, Color.LTGRAY, false);
    }

    private void drawCompactEvents(Canvas c, List<Event> events, boolean forPip) {
        int offset = forPip ? host.pipEventOffset() : host.eventOffset();
        int selected = forPip ? host.pipEvent() : host.selectedEvent();
        float left = 16, right = widthDp() - 16, titleX = 24, matchX = 92;
        int rows = visibleRows();
        c.save();
        c.clipRect(0, d(compactEventListTop() - 45), getWidth(), d(heightDp() - 38));
        c.translate(0, d(dragY));
        for (int i = offset; i < Math.min(events.size(), offset + rows); i++) {
            Event event = events.get(i);
            float y = compactEventListTop() + (i - offset) * compactEventRow();
            if (i == selected) {
                paint.setColor(Color.rgb(25, 57, 77));
                c.drawRoundRect(d(left), d(y - 39), d(right), d(y + 39), d(8), d(8), paint);
            }
            String time = event.startsAt.length() >= 16 ? event.startsAt.substring(11, 16) : "--:--";
            text(c, time, titleX, y, 20, Color.rgb(94, 234, 212), true);
            String sources = event.sources.size() + " fuente" + (event.sources.size() == 1 ? "" : "s");
            paint.setTextSize(d(13));
            float sourceWidth = paint.measureText(sources) / density;
            float maxMatch = right - matchX - sourceWidth - 10;
            drawMatch(c, event, matchX, y, maxMatch, 18, i == selected);
            text(c, sources, right - sourceWidth, y, 13, Color.LTGRAY, false);
        }
        c.restore();
        text(c, forPip ? "Tocá un evento para elegir su fuente" : "Tocá un evento · Deslizá para desplazarte", 24, heightDp() - 24, 13, Color.LTGRAY, false);
    }

    private String[] titleParts(String title) {
        int separator = title == null ? -1 : title.indexOf(':');
        if (separator > 0 && separator < title.length() - 1) {
            return new String[] { title.substring(0, separator).trim(), title.substring(separator + 1).trim() };
        }
        return new String[] { "", title == null ? "Evento" : title.trim() };
    }

    private void drawMatch(Canvas c, Event event, float x, float y, float maxWidth, float size, boolean bold) {
        String[] parts = titleParts(event.title);
        if (parts[1].matches("(?s).*\\s+(?i:vs\\.?)\\s+.*")) {
            String[] teams = parts[1].split("\\s+(?i:vs\\.?)\\s+", 2);
            float teamSize = Math.max(13f, size - 2f);
            text(c, fit(teams[0], maxWidth, teamSize), x, y - 13, teamSize, Color.WHITE, bold);
            text(c, "VS", x, y + 3, Math.max(11f, teamSize - 2), Color.rgb(94, 234, 212), true);
            text(c, fit(teams.length > 1 ? teams[1] : "", maxWidth, teamSize), x, y + 19, teamSize, Color.WHITE, bold);
            text(c, fit(parts[0], maxWidth, 11), x, y + 35, 11, Color.LTGRAY, false);
        } else {
            text(c, fit(parts[1], maxWidth, size), x, y, size, Color.WHITE, bold);
            text(c, fit(parts[0], maxWidth, 11), x, y + 22, 11, Color.LTGRAY, false);
        }
    }

    private void drawLoading(Canvas c) {
        float cx = getWidth() / 2f;
        float cy = getHeight() / 2f;
        paint.setTextSize(d(52));
        paint.setTypeface(Typeface.DEFAULT);
        c.save();
        c.rotate(ballRotation, cx, cy);
        c.drawText("⚽", cx - paint.measureText("⚽") / 2f, cy - (paint.ascent() + paint.descent()) / 2f, paint);
        c.restore();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        removeCallbacks(ballAnimation);
        post(ballAnimation);
    }

    @Override protected void onDetachedFromWindow() {
        removeCallbacks(ballAnimation);
        super.onDetachedFromWindow();
    }

    private void drawUpdate(Canvas c) {
        if (compactLayout()) {
            drawCompactUpdate(c);
            return;
        }
        header(c, "Actualización disponible");
        text(c, "Nueva versión " + host.updateVersion(), 80, 180, 25, Color.WHITE, true);
        text(c, host.updateStatus(), 80, 225, 18, Color.LTGRAY, false);
        text(c, "OK para descargar e instalar · Back para continuar", 80, 285, 18, Color.rgb(94,234,212), true);
    }

    private void drawCompactUpdate(Canvas c) {
        header(c, "Actualización disponible");
        float maxWidth = widthDp() - 48;
        text(c, fit("Nueva versión " + host.updateVersion(), maxWidth, 20), 24, 112, 20, Color.WHITE, true);
        drawWrappedText(c, host.updateStatus(), 24, 150, 16, Color.LTGRAY, false, maxWidth, 5);
        float bottom = heightDp() - 56;
        text(c, fit("Tap para descargar e instalar · Back para continuar", maxWidth, 14), 24, bottom, 14, Color.rgb(94, 234, 212), true);
    }

    private void drawWrappedText(Canvas c, String value, float x, float y, float size, int color,
                                 boolean bold, float maxWidth, int maxLines) {
        if (value == null || value.trim().isEmpty()) return;
        paint.setTextSize(d(size));
        paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        StringBuilder line = new StringBuilder();
        int lineNumber = 0;
        for (String word : value.trim().split("\\s+")) {
            String candidate = line.length() == 0 ? word : line + " " + word;
            if (paint.measureText(candidate) <= d(maxWidth)) {
                line = new StringBuilder(candidate);
            } else {
                if (line.length() > 0) {
                    text(c, fit(line.toString(), maxWidth, size), x, y + lineNumber * 22, size, color, bold);
                    lineNumber++;
                }
                line = new StringBuilder(word);
                if (lineNumber == maxLines - 1) {
                    text(c, fit(line + "…", maxWidth, size), x, y + lineNumber * 22, size, color, bold);
                    return;
                }
            }
        }
        if (line.length() > 0 && lineNumber < maxLines) {
            text(c, fit(line.toString(), maxWidth, size), x, y + lineNumber * 22, size, color, bold);
        }
    }

    private void drawSources(Canvas c) {
        Event event = host.events().get(host.selectedEvent());
        if (sourceList.getVisibility() == VISIBLE) {
            header(c, event.title);
            text(c, compactLayout() ? "Elegí una fuente · Tocá para reproducir" : "Elegí una fuente · Flechas para desplazarte", compactLayout() ? 24 : 70, compactLayout() ? 100 : 135, compactLayout() ? 14 : 18, Color.LTGRAY, false);
            return;
        }
        if (compactLayout()) { drawCompactSources(c, event); return; }
        header(c, event.title); text(c, compactLayout() ? "Elegí una fuente · Deslizá para desplazarte" : "Elegí una fuente · Flechas para desplazarte", compactLayout() ? 24 : 70, compactLayout() ? 100 : 135, compactLayout() ? 14 : 18, Color.LTGRAY, false);
        if (event.sources.isEmpty()) { text(c, "No hay fuentes disponibles", 85, 205, 22, Color.LTGRAY, false); return; }
        int visibleEnd = Math.min(event.sources.size(), host.sourceOffset() + visibleRows());
        float right = widthDp() - (compactLayout() ? 16 : 55);
        text(c, (host.sourceOffset() + 1) + "–" + visibleEnd + " de " + event.sources.size(), right - (compactLayout() ? 95 : 155), compactLayout() ? 100 : 135, compactLayout() ? 13 : 16, Color.LTGRAY, false);
        for (int i = host.sourceOffset(); i < visibleEnd; i++) { float y = (compactLayout() ? 135 : 170) + (i - host.sourceOffset()) * 48; if (i == host.selectedSource()) { paint.setColor(Color.rgb(25,57,77)); c.drawRoundRect(d(compactLayout() ? 16 : 55),d(y-27),d(right),d(y+13),d(8),d(8),paint); } text(c, fit(event.sources.get(i).name, right - (compactLayout() ? 32 : 85), compactLayout() ? 17 : 20), compactLayout() ? 32 : 85, y, compactLayout() ? 17 : 20, Color.WHITE, i == host.selectedSource()); }
    }

    private void drawCompactSources(Canvas c, Event event) {
        header(c, event.title);
        text(c, "Elegí una fuente · Tocá para reproducir", 24, 100, 14, Color.LTGRAY, false);
        int visibleEnd = Math.min(event.sources.size(), host.sourceOffset() + visibleRows());
        float right = widthDp() - 16;
        text(c, (host.sourceOffset() + 1) + "–" + visibleEnd + " de " + event.sources.size(), right - 95, 124, 13, Color.LTGRAY, false);
        c.save();
        c.clipRect(0, d(112), getWidth(), d(heightDp() - 38));
        c.translate(0, d(dragY));
        for (int i = host.sourceOffset(); i < visibleEnd; i++) {
            float y = 160 + (i - host.sourceOffset()) * 48;
            if (i == host.selectedSource()) {
                paint.setColor(Color.rgb(25, 57, 77));
                c.drawRoundRect(d(16), d(y - 27), d(right), d(y + 13), d(8), d(8), paint);
            }
            text(c, fit(event.sources.get(i).name, right - 32, 17), 32, y, 17, Color.WHITE, i == host.selectedSource());
        }
        c.restore();
        text(c, "Deslizá para desplazarte", 24, heightDp() - 24, 13, Color.LTGRAY, false);
    }

    private void drawPreview(Canvas c) {
        if (compactLayout()) {
            drawCompactPreview(c);
            return;
        }
        paint.setColor(Color.argb(220, 7, 17, 31)); c.drawRect(0, getHeight() - d(125), getWidth(), getHeight(), paint);
        String position = ""; List<Event> events = host.events();
        if (!events.isEmpty() && host.selectedEvent() < events.size()) {
            Event event = events.get(host.selectedEvent());
            if (host.selectedSource() < event.sources.size()) position = event.title + " · " + (host.selectedSource() + 1) + "/" + event.sources.size() + " · " + event.sources.get(host.selectedSource()).name;
        }
        text(c, position, 60, getHeight() / density - 112, 15, Color.rgb(94,234,212), true);
        text(c, host.playerMessage(), 60, getHeight() / density - 88, 18, Color.WHITE, true);
        text(c, host.previewAction() == 0 ? "[Ver en pantalla completa]" : "[Agregar segundo evento en PiP]", 60, getHeight() / density - 53, 18, Color.rgb(94,234,212), true);
        text(c, "◀ ▶ elegir acción · ▲ ▼ cambiar fuente · OK confirmar · Back: fuentes", 60, getHeight() / density - 18, 14, Color.LTGRAY, false);
    }

    private void drawCompactPreview(Canvas c) {
        String position = "";
        List<Event> events = host.events();
        if (!events.isEmpty() && host.selectedEvent() < events.size()) {
            Event event = events.get(host.selectedEvent());
            if (host.selectedSource() < event.sources.size()) {
                position = event.title + " · " + (host.selectedSource() + 1) + "/" + event.sources.size()
                        + " · " + event.sources.get(host.selectedSource()).name;
            }
        }

        // Dejamos una zona inferior libre para la barra de navegación del
        // teléfono, que puede ocupar espacio distinto según el fabricante.
        float safeBottom = 56f;
        float bottom = heightDp() - safeBottom;
        float top = Math.max(0, bottom - 178f);
        paint.setColor(Color.argb(235, 7, 17, 31));
        c.drawRect(0, d(top), getWidth(), d(bottom), paint);
        text(c, fit(position, widthDp() - 48, 13), 24, top + 26, 13, Color.rgb(94, 234, 212), true);
        text(c, fit(host.playerMessage(), widthDp() - 48, 16), 24, top + 58, 16, Color.WHITE, true);
        text(c, fit(host.previewAction() == 0 ? "[Ver en pantalla completa]" : "[Agregar segundo evento en PiP]", widthDp() - 48, 17), 24, top + 98, 17, Color.rgb(94, 234, 212), true);
        text(c, fit("Tap para elegir · Deslizá para cambiar fuente · Back: fuentes", widthDp() - 48, 13), 24, bottom - 14, 13, Color.LTGRAY, false);
    }

    public void showPlaybackOverlay() {
        playbackOverlayVisible = true;
        overlayHandler.removeCallbacksAndMessages(null);
        overlayHandler.postDelayed(() -> { playbackOverlayVisible = false; invalidate(); }, 4000);
        invalidate();
    }

    private void drawPlaybackOverlay(Canvas c) {
        if (!playbackOverlayVisible) return;
        float bottom = getHeight() / density - 22;
        String help = host.state() == DUAL
                ? "▲ ▼ cambiar fuente principal · ◀ ▶ intercambiar · Back: cerrar PiP"
                : "▲ ▼ cambiar fuente · Back: volver";
        paint.setColor(Color.argb(205, 7, 17, 31));
        c.drawRect(0, getHeight() - d(58), getWidth(), getHeight(), paint);
        text(c, help, 35, bottom, 14, Color.LTGRAY, false);
        String label = host.playbackLabel();
        paint.setTextSize(d(15)); paint.setTypeface(Typeface.DEFAULT_BOLD);
        float labelWidth = paint.measureText(label);
        text(c, label, getWidth() / density - labelWidth / density - 35, bottom, 15, Color.rgb(94,234,212), true);
    }

    private void drawPipSources(Canvas c) {
        c.drawColor(Color.rgb(7,17,31)); Event event = host.events().get(host.pipEvent()); header(c,event.title); text(c,compactLayout() ? "Elegí la fuente para PiP · Tocá para reproducir" : "Elegí la fuente para PiP · OK para reproducir muteado",compactLayout() ? 24 : 70,compactLayout() ? 100 : 135,compactLayout() ? 14 : 18,Color.LTGRAY,false);
        if (sourceList.getVisibility() == VISIBLE) return;
        float right = widthDp() - (compactLayout() ? 16 : 55);
        for(int i=host.pipSourceOffset();i<Math.min(event.sources.size(),host.pipSourceOffset()+visibleRows());i++){float y=(compactLayout() ? 135 : 170)+(i-host.pipSourceOffset())*48;if(i==host.pipSource()){paint.setColor(Color.rgb(25,57,77));c.drawRoundRect(d(compactLayout() ? 16 : 55),d(y-27),d(right),d(y+13),d(8),d(8),paint);}text(c,fit(event.sources.get(i).name,right-(compactLayout() ? 32 : 85),compactLayout() ? 17 : 20),compactLayout() ? 32 : 85,y,compactLayout() ? 17 : 20,Color.WHITE,i==host.pipSource());}
    }

    private void drawLogo(Canvas c, Event event, float x, float y, float size) {
        Bitmap bitmap = host.logo(event.logo);
        if (bitmap != null) c.drawBitmap(bitmap, null, new android.graphics.RectF(d(x),d(y),d(x+size),d(y+size)), paint);
        else { paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(d(2)); paint.setColor(Color.rgb(94,234,212)); c.drawCircle(d(x+size/2),d(y+size/2),d(size/2-2),paint); paint.setStyle(Paint.Style.FILL); }
    }

    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) host.onBack();
        else if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER || keyCode == KeyEvent.KEYCODE_ENTER) host.onConfirm();
        else host.onDpad(keyCode);
        return true;
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        // Durante reproducción esta vista es transparente y no debe tapar los
        // gestos/controles táctiles del PlayerView que está debajo.
        int state = host.state();
        if (state == PLAYER || state == DUAL) return false;
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            downX = event.getX(); downY = event.getY();
            startDragY = dragY;
            dragging = false;
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_MOVE && compactLayout() && isScrollableState(state)) {
            float dy = (event.getY() - downY) / density;
            if (Math.abs(dy) > 8) dragging = true;
            if (dragging) {
                dragY = clampDrag(startDragY + dy, state);
                invalidate();
            }
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_UP) {
            float dx = (event.getX() - downX) / density;
            float dy = (event.getY() - downY) / density;
            if (dragging) {
                float gestureDelta = dragY - startDragY;
                int movedRows = host.onScroll(gestureDelta);
                // Conserva la fracción que no llegó a completar otra fila;
                // así el contenido no salta al soltar.
                dragY = clampDrag(dragY + movedRows * scrollRowDp(state), state);
                dragging = false;
                invalidate();
            } else if (Math.abs(dy) > 32 && Math.abs(dy) > Math.abs(dx)) {
                // Deslizar hacia arriba muestra los elementos siguientes.
                host.onSwipe(dy < 0);
            } else {
                dragY = 0;
                host.onTouch(event.getX() / density, event.getY() / density);
            }
        }
        if (event.getAction() == MotionEvent.ACTION_CANCEL) {
            dragY = 0;
            dragging = false;
            invalidate();
        }
        return true;
    }

    private boolean isScrollableState(int state) {
        return state == EVENTS || state == SOURCES || state == PIP_EVENTS || state == PIP_SOURCES;
    }

    private float scrollRowDp(int state) {
        return state == EVENTS || state == PIP_EVENTS ? compactEventRow() : 48f;
    }

    private int offsetRows(int state) {
        if (state == EVENTS) return host.eventOffset();
        if (state == SOURCES) return host.sourceOffset();
        if (state == PIP_EVENTS) return host.pipEventOffset();
        return host.pipSourceOffset();
    }

    private int maxOffsetRows(int state) {
        int size;
        if (state == EVENTS || state == PIP_EVENTS) size = host.events().size();
        else if (state == SOURCES && !host.events().isEmpty()) size = host.events().get(host.selectedEvent()).sources.size();
        else if (state == PIP_SOURCES && !host.events().isEmpty()) size = host.events().get(host.pipEvent()).sources.size();
        else return 0;
        return Math.max(0, size - visibleRows());
    }

    private float clampDrag(float value, int state) {
        float row = scrollRowDp(state);
        float current = offsetRows(state) * row;
        float min = current - maxOffsetRows(state) * row;
        return Math.max(min, Math.min(current, value));
    }
}
