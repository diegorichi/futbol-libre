package com.futbol.tv.ui.list;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.futbol.tv.EventListAdapter;
import com.futbol.tv.SourceListAdapter;
import com.futbol.tv.TvScreenView;
import com.futbol.tv.state.ScreenState;

/** Binds event/source RecyclerViews to the current screen state. */
public final class TvListBinder {
    private final RecyclerView eventList;
    private final RecyclerView sourceList;
    private final EventListAdapter eventAdapter;
    private SourceListAdapter sourceAdapter;
    private String listKey = "";
    private boolean listForPip;

    public TvListBinder(Context context, TvScreenView.Host host) {
        eventList = new RecyclerView(context);
        eventList.setLayoutManager(new LinearLayoutManager(context));
        eventList.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
        eventList.setFocusable(false);
        eventList.setDescendantFocusability(ViewGroup.FOCUS_BLOCK_DESCENDANTS);
        eventAdapter = new EventListAdapter(host.events(), index -> host.onEventTap(index, listForPip));
        eventList.setAdapter(eventAdapter);

        sourceList = new RecyclerView(context);
        sourceList.setLayoutManager(new LinearLayoutManager(context));
        sourceList.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
        sourceList.setFocusable(false);
        sourceList.setDescendantFocusability(ViewGroup.FOCUS_BLOCK_DESCENDANTS);
        eventList.setVisibility(View.GONE);
        sourceList.setVisibility(View.GONE);
    }

    public RecyclerView eventList() { return eventList; }
    public RecyclerView sourceList() { return sourceList; }
    public boolean eventsVisible() { return eventList.getVisibility() == View.VISIBLE; }
    public boolean sourcesVisible() { return sourceList.getVisibility() == View.VISIBLE; }

    public void sync(ScreenState state, int heightPx, float density, boolean compact, TvScreenView.Host host) {
        boolean eventsState = state.eventListVisible();
        boolean sourcesState = state.sourceListVisible();
        eventList.setVisibility(eventsState ? View.VISIBLE : View.GONE);
        sourceList.setVisibility(sourcesState ? View.VISIBLE : View.GONE);
        if (eventsState) {
            listForPip = state.isPipList();
            String key = state + ":" + host.events().size() + ":" + host.selectedEvent() + ":" + host.pipEvent();
            if (!key.equals(listKey)) {
                listKey = key;
                eventAdapter.setSelected(listForPip ? host.pipEvent() : host.selectedEvent());
                eventList.scrollToPosition(listForPip ? host.pipEvent() : host.selectedEvent());
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1,
                    Math.max(0, heightPx - dp(compact ? 82 : 98, density) - dp(46, density)));
            params.topMargin = dp(compact ? 82 : 98, density);
            eventList.setLayoutParams(params);
        } else if (sourcesState && !host.events().isEmpty()) {
            listForPip = state.isPipList();
            int eventIndex = listForPip ? host.pipEvent() : host.selectedEvent();
            if (eventIndex < host.events().size()) {
                String key = state + ":" + eventIndex + ":" + host.events().get(eventIndex).sources.size()
                        + ":" + host.selectedSource() + ":" + host.pipSource();
                if (!key.equals(listKey)) {
                    listKey = key;
                    sourceAdapter = new SourceListAdapter(host.events().get(eventIndex).sources,
                            index -> host.onSourceTap(index, listForPip));
                    sourceAdapter.setSelected(listForPip ? host.pipSource() : host.selectedSource());
                    sourceList.setAdapter(sourceAdapter);
                    sourceList.scrollToPosition(listForPip ? host.pipSource() : host.selectedSource());
                }
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1,
                    Math.max(0, heightPx - dp(compact ? 108 : 122, density) - dp(46, density)));
            params.topMargin = dp(compact ? 108 : 122, density);
            sourceList.setLayoutParams(params);
        }
    }

    private static int dp(float value, float density) {
        return (int) (value * density + 0.5f);
    }
}
