package com.futbol.tv.discovery;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.os.Handler;

import org.json.JSONObject;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Owns mDNS and UDP discovery without deciding what the Activity does next. */
public final class ServerDiscoveryController {
    public interface Listener {
        void onServerFound(String baseUrl);
        void onDiscoveryError(Exception error);
    }

    private static final String SERVICE_TYPE = "_futbol._tcp.";
    private static final int UDP_DISCOVERY_PORT = 45678;
    private static final long FALLBACK_DELAY_MS = 6000L;

    private final NsdManager nsd;
    private final Handler main;
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private final Listener listener;
    private NsdManager.DiscoveryListener discovery;
    private Runnable fallback;
    private boolean active;
    private boolean announced;

    public ServerDiscoveryController(Context context, Handler main, Listener listener) {
        this.nsd = (NsdManager) context.getSystemService(Context.NSD_SERVICE);
        this.main = main;
        this.listener = listener;
    }

    public void start(boolean emulator) {
        stop();
        active = true;
        announced = false;
        fallback = () -> {
            if (!active) return;
            if (emulator) listener.onServerFound("http://10.0.2.2:8080");
            else discoverByBroadcast();
        };
        main.postDelayed(fallback, FALLBACK_DELAY_MS);
        discovery = new NsdManager.DiscoveryListener() {
            @Override public void onDiscoveryStarted(String serviceType) { }

            @Override public void onServiceFound(NsdServiceInfo info) {
                if (!SERVICE_TYPE.equals(info.getServiceType()) || !active) return;
                nsd.resolveService(info, new NsdManager.ResolveListener() {
                    @Override public void onResolveFailed(NsdServiceInfo serviceInfo, int errorCode) { }

                    @Override public void onServiceResolved(NsdServiceInfo serviceInfo) {
                        if (active && serviceInfo.getHost() != null) {
                            publish("http://" + serviceInfo.getHost().getHostAddress()
                                    + ":" + serviceInfo.getPort());
                        }
                    }
                });
            }

            @Override public void onServiceLost(NsdServiceInfo serviceInfo) { }
            @Override public void onDiscoveryStopped(String serviceType) { }
            @Override public void onStartDiscoveryFailed(String serviceType, int errorCode) {
                stopDiscoveryOnly();
            }
            @Override public void onStopDiscoveryFailed(String serviceType, int errorCode) { }
        };
        nsd.discoverServices(SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, discovery);
    }

    public void stop() {
        active = false;
        if (fallback != null) {
            main.removeCallbacks(fallback);
            fallback = null;
        }
        stopDiscoveryOnly();
    }

    public void close() {
        stop();
        network.shutdownNow();
    }

    private void stopDiscoveryOnly() {
        if (nsd != null && discovery != null) {
            try {
                nsd.stopServiceDiscovery(discovery);
            } catch (Exception ignored) { }
            discovery = null;
        }
    }

    private void discoverByBroadcast() {
        network.execute(() -> {
            try (DatagramSocket socket = new DatagramSocket()) {
                socket.setBroadcast(true);
                byte[] request = "FUTBOL_DISCOVER_V1".getBytes();
                socket.send(new DatagramPacket(request, request.length,
                        InetAddress.getByName("255.255.255.255"), UDP_DISCOVERY_PORT));
                socket.setSoTimeout(2500);
                byte[] buffer = new byte[512];
                DatagramPacket response = new DatagramPacket(buffer, buffer.length);
                socket.receive(response);
                JSONObject payload = new JSONObject(new String(response.getData(), 0, response.getLength()));
                String base = "http://" + response.getAddress().getHostAddress()
                        + ":" + payload.optInt("port", 8080);
                main.post(() -> {
                    publish(base);
                });
            } catch (Exception error) {
                main.post(() -> {
                    if (active && !announced) listener.onDiscoveryError(error);
                });
            }
        });
    }

    private void publish(String baseUrl) {
        if (!active || announced) return;
        announced = true;
        listener.onServerFound(baseUrl);
    }
}
