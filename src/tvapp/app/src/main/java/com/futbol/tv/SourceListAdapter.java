package com.futbol.tv;

import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.futbol.tv.model.Source;
import java.util.List;

public final class SourceListAdapter extends RecyclerView.Adapter<SourceListAdapter.Holder> {
    public interface Listener { void onSourceTap(int index); }
    private final List<Source> sources;
    private final Listener listener;
    private int selected;
    public SourceListAdapter(List<Source> sources, Listener listener) { this.sources = sources; this.listener = listener; }
    public void setSelected(int selected) { this.selected = selected; notifyDataSetChanged(); }
    @NonNull @Override public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) { return new Holder(new SourceRowView(parent.getContext())); }
    @Override public void onBindViewHolder(@NonNull Holder holder, int position) { holder.row.bind(sources.get(position), position == selected); holder.row.setOnClickListener(view -> listener.onSourceTap(position)); }
    @Override public int getItemCount() { return sources.size(); }
    static final class Holder extends RecyclerView.ViewHolder { final SourceRowView row; Holder(SourceRowView row) { super(row); this.row = row; } }
}
