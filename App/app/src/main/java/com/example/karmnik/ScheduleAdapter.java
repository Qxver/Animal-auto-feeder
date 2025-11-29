package com.example.karmnik;

import android.app.AlertDialog;
import android.content.Context;
import android.text.InputType;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class ScheduleAdapter extends RecyclerView.Adapter<ScheduleAdapter.ScheduleViewHolder> {
    private List<ScheduleTime> scheduleList;
    private Context context;
    private ScheduleAdapterListener listener;

    public interface ScheduleAdapterListener {
        void onEdit(ScheduleTime scheduleTime);
        void onDelete(ScheduleTime scheduleTime);
    }

    public ScheduleAdapter(Context context, List<ScheduleTime> scheduleList, ScheduleAdapterListener listener) {
        this.context = context;
        this.scheduleList = scheduleList;
        this.listener = listener;
    }

    @NonNull
    @Override
    public ScheduleViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(context).inflate(R.layout.schedule_item, parent, false);
        return new ScheduleViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ScheduleViewHolder holder, int position) {
        ScheduleTime schedule = scheduleList.get(position);
        holder.timeTextView.setText(schedule.time);

        holder.editButton.setOnClickListener(v -> {
            showEditDialog(schedule, position);
        });

        holder.deleteButton.setOnClickListener(v -> {
            if (listener != null) {
                listener.onDelete(schedule);
            }
        });
    }

    @Override
    public int getItemCount() {
        return scheduleList.size();
    }

    private void showEditDialog(ScheduleTime schedule, int position) {
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("Edit Schedule Time");

        EditText input = new EditText(context);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText(schedule.time);
        input.setHint("HH:mm");

        LinearLayout layout = new LinearLayout(context);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(16, 16, 16, 16);
        layout.addView(input);

        builder.setView(layout);
        builder.setPositiveButton("Save", (dialog, which) -> {
            String newTime = input.getText().toString().trim();
            if (!newTime.isEmpty()) {
                schedule.time = newTime;
                if (listener != null) {
                    listener.onEdit(schedule);
                }
            }
        });
        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        builder.show();
    }

    public void updateList(List<ScheduleTime> newList) {
        this.scheduleList = newList;
        notifyDataSetChanged();
    }

    public static class ScheduleViewHolder extends RecyclerView.ViewHolder {
        TextView timeTextView;
        Button editButton;
        Button deleteButton;

        public ScheduleViewHolder(@NonNull View itemView) {
            super(itemView);
            timeTextView = itemView.findViewById(R.id.timeTextView);
            editButton = itemView.findViewById(R.id.editButton);
            deleteButton = itemView.findViewById(R.id.deleteButton);
        }
    }
}