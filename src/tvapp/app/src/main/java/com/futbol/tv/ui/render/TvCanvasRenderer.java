package com.futbol.tv.ui.render;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;

import com.futbol.tv.TvScreenView;
import com.futbol.tv.model.Event;
import com.futbol.tv.state.ScreenState;
import com.futbol.tv.ui.layout.TvLayoutMetrics;
import com.futbol.tv.ui.layout.TvLayoutProfile;
import com.futbol.tv.ui.layout.TvVisualTokens;
import com.futbol.tv.ui.list.TvListBinder;

import java.util.List;

/** Owns Canvas drawing. TvScreenView only hosts this renderer and forwards lifecycle/input. */
public final class TvCanvasRenderer {
    private final TvScreenView view;
    private final TvScreenView.Host host;
    private final TvLayoutProfile layout;
    private final TvListBinder lists;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;
    private float dragOffset;
    private float loadingRotation;

    public TvCanvasRenderer(TvScreenView view, TvScreenView.Host host,
                            TvLayoutProfile layout, TvListBinder lists) {
        this.view = view;
        this.host = host;
        this.layout = layout;
        this.lists = lists;
        density = view.getResources().getDisplayMetrics().density;
    }

    public void setDragOffset(float value) { dragOffset = value; }
    public void setLoadingRotation(float value) { loadingRotation = value; }

    public void renderBackground(Canvas canvas, CanvasRenderAction action) {
        canvas.drawColor(TvVisualTokens.BACKGROUND);
        action.draw(canvas);
    }

    public void renderError(Canvas canvas) {
        renderBackground(canvas, c -> {
            text(c, "No se encontró el servidor", 80, 90, 28, Color.WHITE, true);
            text(c, "Back para salir · OK para reintentar", 80, 135, 18, Color.LTGRAY, false);
        });
    }

    public void drawEvents(Canvas canvas, boolean pip) {
        List<Event> events = host.events();
        header(canvas, pip ? "Elegí el segundo evento para PiP" : "Eventos");
        if (events.isEmpty()) {
            text(canvas, "No hay eventos disponibles", layout.compact() ? 24 : 80,
                    layout.compact() ? 130 : 170, 22, Color.LTGRAY, false);
            return;
        }
        if (lists.eventsVisible()) {
            text(canvas, pip ? "El principal sigue reproduciendo"
                            : (layout.compact() ? "Tocá un evento · Deslizá para desplazarte"
                            : "OK para seleccionar · Flechas para desplazarte"),
                    layout.footerX(), layout.footerY(heightDp()), layout.footerSize(), Color.LTGRAY, false);
            return;
        }
        if (layout.compact()) {
            drawCompactEvents(canvas, events, pip);
            return;
        }
        int offset = pip ? host.pipEventOffset() : host.eventOffset();
        int selected = pip ? host.pipEvent() : host.selectedEvent();
        float left = layout.horizontalInset();
        float right = widthDp() - layout.horizontalInset();
        for (int i = offset; i < Math.min(events.size(), offset + visibleRows()); i++) {
            Event event = events.get(i);
            float y = layout.eventListTop(widthDp(), heightDp()) + (i - offset) * layout.eventRow(widthDp(), heightDp());
            if (i == selected) roundRect(canvas, left, y - 34, right, y + 38, 8, Color.rgb(25, 57, 77));
            text(canvas, event.startsAt.length() >= 16 ? event.startsAt.substring(11, 16) : "--:--",
                    layout.eventTimeX(), y, 19, Color.rgb(94, 234, 212), true);
            String sources = event.sources.size() + " fuente" + (event.sources.size() == 1 ? "" : "s");
            paint.setTextSize(d(layout.eventSourcesSize()));
            float sourceWidth = paint.measureText(sources) / density;
            drawMatch(canvas, event, layout.eventTitleX(), y, right - layout.eventTitleX() - sourceWidth - 12,
                    layout.eventTitleSize(), i == selected);
            text(canvas, sources, right - sourceWidth, y - 5, layout.eventSourcesSize(), Color.LTGRAY, false);
        }
        text(canvas, pip ? "El principal sigue reproduciendo · OK para ver sus fuentes"
                        : "OK para seleccionar · Flechas para desplazarte",
                layout.footerX(), layout.footerY(heightDp()), layout.footerSize(), Color.LTGRAY, false);
    }

    public void drawLoading(Canvas canvas) {
        float cx = view.getWidth() / 2f;
        float cy = view.getHeight() / 2f;
        paint.setTextSize(d(52));
        canvas.save();
        canvas.rotate(loadingRotation, cx, cy);
        canvas.drawText("⚽", cx - paint.measureText("⚽") / 2f,
                cy - (paint.ascent() + paint.descent()) / 2f, paint);
        canvas.restore();
    }

    public void drawUpdate(Canvas canvas) {
        renderBackground(canvas, c -> {
            header(c, "Actualización disponible");
            if (layout.compact()) {
                float max = widthDp() - 48;
                text(c, fit("Nueva versión " + host.updateVersion(), max, 20), 24, 112, 20, Color.WHITE, true);
                wrapped(c, host.updateStatus(), 24, 150, 16, Color.LTGRAY, max, 5);
                text(c, fit("Tap instalar · Back para continuar", max, 14), 24, heightDp() - 56,
                        14, TvVisualTokens.ACCENT, true);
            } else {
                text(c, "Nueva versión " + host.updateVersion(), 80, 180, 25, Color.WHITE, true);
                text(c, host.updateStatus(), 80, 225, 18, Color.LTGRAY, false);
                text(c, "OK instalar · Back para continuar", 80, 285, 18, TvVisualTokens.ACCENT, true);
            }
        });
    }

    public void drawSources(Canvas canvas) {
        if (host.events().isEmpty()) return;
        Event event = host.events().get(host.selectedEvent());
        header(canvas, event.title);
        if (lists.sourcesVisible()) {
            text(canvas, layout.compact() ? "Elegí una fuente · Tocá para reproducir"
                            : "Elegí una fuente · Flechas para desplazarte",
                    layout.footerX(), layout.compact() ? 100 : 135,
                    layout.compact() ? 14 : 18, Color.LTGRAY, false);
            return;
        }
        if (layout.compact()) {
            drawCompactSources(canvas, event);
            return;
        }
        text(canvas, "Elegí una fuente · Flechas para desplazarte", layout.footerX(), 135, 18, Color.LTGRAY, false);
        if (event.sources.isEmpty()) {
            text(canvas, "No hay fuentes disponibles", 85, 205, 22, Color.LTGRAY, false);
            return;
        }
        int end = Math.min(event.sources.size(), host.sourceOffset() + visibleRows());
        float right = widthDp() - layout.sourceRightInset();
        for (int i = host.sourceOffset(); i < end; i++) {
            float y = layout.sourceTop() + (i - host.sourceOffset()) * 48;
            if (i == host.selectedSource()) roundRect(canvas, layout.horizontalInset(), y - 27, right, y + 13, 8, Color.rgb(25, 57, 77));
            text(canvas, fit(event.sources.get(i).name, right - layout.sourceTextX(), layout.sourceTextSize()),
                    layout.sourceTextX(), y, layout.sourceTextSize(), Color.WHITE, i == host.selectedSource());
        }
    }

    public void drawPipSources(Canvas canvas) {
        if (host.events().isEmpty()) return;
        Event event = host.events().get(host.pipEvent());
        canvas.drawColor(TvVisualTokens.BACKGROUND);
        header(canvas, event.title);
        text(canvas, "Elegí la fuente para PiP · OK para reproducir muteado",
                layout.footerX(), layout.compact() ? 100 : 135, layout.compact() ? 14 : 18, Color.LTGRAY, false);
        if (lists.sourcesVisible()) return;
        float right = widthDp() - layout.sourceRightInset();
        for (int i = host.pipSourceOffset(); i < Math.min(event.sources.size(), host.pipSourceOffset() + visibleRows()); i++) {
            float y = layout.sourceTop() + (i - host.pipSourceOffset()) * 48;
            if (i == host.pipSource()) roundRect(canvas, layout.horizontalInset(), y - 27, right, y + 13, 8, Color.rgb(25, 57, 77));
            text(canvas, fit(event.sources.get(i).name, right - layout.sourceTextX(), layout.sourceTextSize()),
                    layout.sourceTextX(), y, layout.sourceTextSize(), Color.WHITE, i == host.pipSource());
        }
    }

    public void drawPreview(Canvas canvas) {
        TvLayoutMetrics.PreviewLayout preview = TvLayoutMetrics.preview(widthDp(), heightDp(), safeBottomDp(), layout.compact(), host.vpnAvailable());
        paint.setColor(TvVisualTokens.withAlpha(220, TvVisualTokens.BACKGROUND));
        canvas.drawRect(0, d(preview.panelTop), view.getWidth(), d(preview.panelBottom), paint);
        String position = host.events().isEmpty() ? "" : host.events().get(host.selectedEvent()).title;
        text(canvas, fit(position, widthDp() - 48, 15), layout.compact() ? 24 : 60,
                preview.panelTop + 26, 15, TvVisualTokens.ACCENT, true);
        text(canvas, host.playerMessage(), layout.compact() ? 16 : 60,
                preview.panelTop + 62, 18, Color.WHITE, true);
        button(canvas, preview.fullscreen, "Pantalla completa", host.previewAction() == 0);
        button(canvas, preview.pip, "Agregar segundo evento", host.previewAction() == 1);
        if (preview.vpn != null) vpnButton(canvas, preview.vpn, host.vpnActive(), host.previewAction() == 2);
    }

    private void drawCompactEvents(Canvas c, List<Event> events, boolean pip) {
        int offset = pip ? host.pipEventOffset() : host.eventOffset();
        int selected = pip ? host.pipEvent() : host.selectedEvent();
        float right = widthDp() - 16;
        c.save();
        c.clipRect(0, d(layout.eventListTop(widthDp(), heightDp()) - 45), view.getWidth(), d(heightDp() - 38));
        c.translate(0, d(dragOffset));
        for (int i = offset; i < Math.min(events.size(), offset + visibleRows()); i++) {
            Event event = events.get(i);
            float y = layout.eventListTop(widthDp(), heightDp()) + (i - offset) * layout.eventRow(widthDp(), heightDp());
            if (i == selected) roundRect(c, 16, y - 39, right, y + 39, 8, Color.rgb(25, 57, 77));
            text(c, event.startsAt.length() >= 16 ? event.startsAt.substring(11, 16) : "--:--", 24, y, 20, TvVisualTokens.ACCENT, true);
            drawMatch(c, event, 92, y, right - 92 - 60, 18, i == selected);
        }
        c.restore();
        text(c, pip ? "Tocá un evento para elegir su fuente" : "Tocá un evento · Deslizá para desplazarte", 24, heightDp() - 24, 13, Color.LTGRAY, false);
    }

    private void drawCompactSources(Canvas c, Event event) {
        text(c, "Elegí una fuente · Tocá para reproducir", 24, 100, 14, Color.LTGRAY, false);
        int end = Math.min(event.sources.size(), host.sourceOffset() + visibleRows());
        float right = widthDp() - 16;
        c.save();
        c.clipRect(0, d(112), view.getWidth(), d(heightDp() - 38));
        c.translate(0, d(dragOffset));
        for (int i = host.sourceOffset(); i < end; i++) {
            float y = 160 + (i - host.sourceOffset()) * 48;
            if (i == host.selectedSource()) roundRect(c, 16, y - 27, right, y + 13, 8, Color.rgb(25, 57, 77));
            text(c, fit(event.sources.get(i).name, right - 32, 17), 32, y, 17, Color.WHITE, i == host.selectedSource());
        }
        c.restore();
        text(c, "Deslizá para desplazarte", 24, heightDp() - 24, 13, Color.LTGRAY, false);
    }

    private void drawMatch(Canvas c, Event event, float x, float y, float max, float size, boolean bold) {
        String[] parts = titleParts(event.title);
        if (parts[1].matches("(?s).*\\s+(?i:vs\\.?)\\s+.*")) {
            String[] teams = parts[1].split("\\s+(?i:vs\\.?)\\s+", 2);
            float teamSize = Math.max(13f, size - 2f);
            text(c, fit(teams[0], max, teamSize), x, y - 13, teamSize, Color.WHITE, bold);
            text(c, "VS", x, y + 3, Math.max(11f, teamSize - 2), TvVisualTokens.ACCENT, true);
            text(c, fit(teams.length > 1 ? teams[1] : "", max, teamSize), x, y + 19, teamSize, Color.WHITE, bold);
            text(c, fit(parts[0], max, 11), x, y + 35, 11, Color.LTGRAY, false);
        } else {
            text(c, fit(parts[1], max, size), x, y, size, Color.WHITE, bold);
            text(c, fit(parts[0], max, 11), x, y + 22, 11, Color.LTGRAY, false);
        }
    }

    private String[] titleParts(String title) {
        int separator = title == null ? -1 : title.indexOf(':');
        return separator > 0 && separator < title.length() - 1
                ? new String[] { title.substring(0, separator).trim(), title.substring(separator + 1).trim() }
                : new String[] { "", title == null ? "Evento" : title.trim() };
    }

    private void header(Canvas c, String title) {
        float x = layout.compact() ? 24 : 70;
        text(c, fit(title, widthDp() - x * 2, layout.headerTitleSize()), x, layout.headerY(), layout.headerTitleSize(), Color.WHITE, true);
        text(c, "Fútbol TV", x, layout.headerSubtitleY(), layout.headerSubtitleSize(), TvVisualTokens.ACCENT, true);
    }

    private void button(Canvas c, TvLayoutMetrics.Bounds bounds, String label, boolean selected) {
        if (bounds == null) return;
        paint.setColor(selected ? TvVisualTokens.SURFACE_SELECTED : TvVisualTokens.SURFACE);
        c.drawRoundRect(d(bounds.left), d(bounds.top), d(bounds.right), d(bounds.bottom), d(10), d(10), paint);
        text(c, fit(label, bounds.right - bounds.left - 24, 15), bounds.left + 12, bounds.top + 30, 15, Color.WHITE, selected);
    }

    private void vpnButton(Canvas c, TvLayoutMetrics.Bounds bounds, boolean active, boolean focused) {
        if (bounds == null) return;
        button(c, bounds, "VPN", active || focused);
    }

    private void wrapped(Canvas c, String value, float x, float y, float size, int color, float maxWidth, int maxLines) {
        if (value == null || value.trim().isEmpty()) return;
        paint.setTextSize(d(size));
        StringBuilder line = new StringBuilder();
        int row = 0;
        for (String word : value.trim().split("\\s+")) {
            String candidate = line.length() == 0 ? word : line + " " + word;
            if (paint.measureText(candidate) <= d(maxWidth)) line = new StringBuilder(candidate);
            else {
                text(c, fit(line.toString(), maxWidth, size), x, y + row++ * 22, size, color, false);
                line = new StringBuilder(word);
                if (row == maxLines - 1) { text(c, fit(line + "…", maxWidth, size), x, y + row * 22, size, color, false); return; }
            }
        }
        if (line.length() > 0 && row < maxLines) text(c, fit(line.toString(), maxWidth, size), x, y + row * 22, size, color, false);
    }

    private int visibleRows() { return layout.visibleRows(widthDp(), heightDp()); }
    private float widthDp() { return view.getWidth() / density; }
    private float heightDp() { return view.getHeight() / density; }
    private float d(float value) { return value * density; }
    private float safeBottomDp() {
        android.view.WindowInsets insets = view.getRootWindowInsets();
        if (insets != null) return Math.max(24f, insets.getSystemWindowInsetBottom() / density);
        return 56f;
    }
    private void roundRect(Canvas c, float left, float top, float right, float bottom, float radius, int color) {
        paint.setColor(color);
        c.drawRoundRect(d(left), d(top), d(right), d(bottom), d(radius), d(radius), paint);
    }
    private void text(Canvas c, String value, float x, float y, float size, int color, boolean bold) {
        paint.setColor(color); paint.setTextSize(d(size)); paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        c.drawText(value == null ? "" : value, d(x), d(y), paint);
    }
    private String fit(String value, float maxWidthDp, float sizeDp) {
        if (value == null) return "";
        paint.setTextSize(d(sizeDp));
        if (paint.measureText(value) <= d(maxWidthDp)) return value;
        String suffix = "…"; String result = value;
        while (result.length() > 1 && paint.measureText(result + suffix) > d(maxWidthDp)) result = result.substring(0, result.length() - 1);
        return result + suffix;
    }

    public interface CanvasRenderAction { void draw(Canvas canvas); }
}
