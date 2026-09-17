package com.futbol.tv.playback;

import android.content.Context;
import android.os.Handler;

import androidx.media3.ui.PlayerView;

import com.futbol.tv.model.Event;
import com.futbol.tv.model.Source;
import com.futbol.tv.PlaybackController;
import com.futbol.tv.ServerClient;
import com.futbol.tv.catalog.TvCatalogController;

/** Owns Media3 playback, VPN switching and the internal dual-player mode. */
@androidx.media3.common.util.UnstableApi
public final class TvPlaybackCoordinator {
    public interface Listener { void onChanged(); }

    private final Handler main;
    private final TvCatalogController catalog;
    private final Listener listener;
    private final PlaybackController playback;
    private boolean vpnPlayback;
    private boolean vpnConnecting;
    private boolean previewLoading;
    private String vpnProxyUrl;
    private String playerMessage = "";

    public TvPlaybackCoordinator(Context context, PlayerView primary, PlayerView pip,
                                 TvCatalogController catalog, Handler main, Listener listener) {
        this.main = main;
        this.catalog = catalog;
        this.listener = listener;
        this.playback = new PlaybackController(context, primary, pip, message -> {
            if (message == null || message.isEmpty()) previewLoading = false;
            playerMessage = message;
            main.post(listener::onChanged);
        });
    }

    public void preview(Source source) {
        resetRoute();
        previewLoading = true;
        playerMessage = "Cargando preview...";
        playback.preview(source);
    }

    public void toggleVpnPreview(String baseUrl, Event event, Source source) {
        if (vpnPlayback || vpnConnecting) {
            resetRoute();
            previewLoading = true;
            playerMessage = "Cargando preview...";
            playback.preview(source);
            notifyChanged();
            return;
        }
        previewLoading = true;
        playerMessage = "Obteniendo URL por VPN...";
        vpnConnecting = true;
        playback.releaseAll();
        notifyChanged();
        requestVpn(baseUrl, event, source, true);
    }

    public void toggleVpnPlayback(String baseUrl, Event event, Source source) {
        if (vpnPlayback || vpnConnecting) {
            resetRoute();
            playback.switchPrimary(source);
            notifyChanged();
            return;
        }
        vpnConnecting = true;
        notifyChanged();
        requestVpn(baseUrl, event, source, false);
    }

    private void requestVpn(String baseUrl, Event event, Source source, boolean preview) {
        catalog.requestVpnStreamUrl(baseUrl, event.id, source.id, new ServerClient.StreamUrlCallback() {
            @Override public void onSuccess(String url, String proxyUrl) {
                main.post(() -> {
                    Source vpnSource = new Source(source.id, source.name, url, source.userAgent, source.pageUrl);
                    vpnPlayback = true;
                    vpnConnecting = false;
                    previewLoading = true;
                    vpnProxyUrl = proxyUrl;
                    playerMessage = preview ? "Cargando por VPN..." : playerMessage;
                    if (preview) playback.preview(vpnSource, true, proxyUrl);
                    else playback.switchPrimary(vpnSource, true, proxyUrl);
                    listener.onChanged();
                });
            }

            @Override public void onError(Exception error) {
                main.post(() -> {
                    resetRoute();
                    playerMessage = "Error al cargar por VPN";
                    listener.onChanged();
                });
            }
        });
    }

    public void startPip(Source source) { playback.startPip(source); }
    public void closePip() { playback.closePip(); }
    public boolean swap() { return playback.swap(); }
    public void enterFullscreen() { playback.enterFullscreen(); }
    public void showPreview() { playback.showPreview(); }
    public void stopPrimary() { playback.stopPrimary(); }
    public void releaseAll() { previewLoading = false; playback.releaseAll(); }
    public void switchPrimary(Source source) { resetRoute(); previewLoading = false; playback.switchPrimary(source); }
    public void pauseAll() { playback.pauseAll(); }
    public void resumeAll() { playback.resumeAll(); }
    public void onConfigurationChanged() { playback.onConfigurationChanged(); }

    public boolean vpnActive() { return vpnPlayback; }
    public boolean vpnConnecting() { return vpnConnecting; }
    public boolean previewLoading() { return previewLoading; }
    public String playerMessage() { return playerMessage; }

    private void resetRoute() {
        vpnPlayback = false;
        vpnConnecting = false;
        vpnProxyUrl = null;
    }

    private void notifyChanged() { main.post(listener::onChanged); }

    public void release() { playback.release(); }
}
