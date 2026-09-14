package com.futbol.tv;

import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.futbol.tv.model.Event;
import java.util.List;

public final class EventListAdapter extends RecyclerView.Adapter<EventListAdapter.Holder> {
    public interface Listener { void onEventTap(int index); }
    private final List<Event> events;
    private final Listener listener;
    private int selected;
    public EventListAdapter(List<Event> events, Listener listener) { this.events = events; this.listener = listener; }
    public void setSelected(int selected) { this.selected = selected; notifyDataSetChanged(); }
    @NonNull @Override public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) { return new Holder(new EventRowView(parent.getContext())); }
    @Override public void onBindViewHolder(@NonNull Holder holder, int position) { holder.row.bind(events.get(position), position == selected); holder.row.setOnClickListener(view -> listener.onEventTap(position)); }
    @Override public int getItemCount() { return events.size(); }
    static final class Holder extends RecyclerView.ViewHolder { final EventRowView row; Holder(EventRowView row) { super(row); this.row = row; } }
}
