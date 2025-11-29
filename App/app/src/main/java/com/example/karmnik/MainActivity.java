package com.example.karmnik;

import android.app.AlertDialog;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.text.InputType;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity implements ScheduleAdapter.ScheduleAdapterListener {
    private AppDatabase db;
    private RecyclerView recyclerView;
    private ScheduleAdapter adapter;
    private List<ScheduleTime> scheduleList;
    private FloatingActionButton addScheduleFab;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize database
        db = AppDatabase.getDatabase(this);

        // Initialize RecyclerView
        recyclerView = findViewById(R.id.scheduleRecyclerView);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        // Initialize schedule list and adapter
        scheduleList = new ArrayList<>();
        adapter = new ScheduleAdapter(this, scheduleList, this);
        recyclerView.setAdapter(adapter);

        // Load data from database
        loadScheduleTimes();

        // Initialize FAB
        addScheduleFab = findViewById(R.id.addScheduleFab);
        addScheduleFab.setOnClickListener(v -> showAddTimeDialog());
    }

    private void loadScheduleTimes() {
        Thread thread = new Thread(() -> {
            scheduleList.clear();
            scheduleList.addAll(db.scheduleTimeDao().getAllScheduleTimes());
            runOnUiThread(() -> adapter.notifyDataSetChanged());
        });
        thread.start();
    }

    private void showAddTimeDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Add Schedule Time");

        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setHint("HH:mm (e.g., 12:50)");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(16, 16, 16, 16);
        layout.addView(input);

        builder.setView(layout);
        builder.setPositiveButton("Add", (dialog, which) -> {
            String time = input.getText().toString().trim();
            if (!time.isEmpty()) {
                if (isValidTimeFormat(time)) {
                    ScheduleTime scheduleTime = new ScheduleTime(time);
                    Thread thread = new Thread(() -> {
                        db.scheduleTimeDao().insert(scheduleTime);
                        loadScheduleTimes();
                    });
                    thread.start();
                } else {
                    Toast.makeText(this, "Invalid time format. Use HH:mm", Toast.LENGTH_SHORT).show();
                }
            }
        });
        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        builder.show();
    }

    private boolean isValidTimeFormat(String time) {
        return time.matches("([01]\\d|2[0-3]):[0-5]\\d");
    }

    @Override
    public void onEdit(ScheduleTime scheduleTime) {
        Thread thread = new Thread(() -> {
            db.scheduleTimeDao().update(scheduleTime);
            loadScheduleTimes();
        });
        thread.start();
        Toast.makeText(this, "Schedule updated", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onDelete(ScheduleTime scheduleTime) {
        Thread thread = new Thread(() -> {
            db.scheduleTimeDao().delete(scheduleTime);
            loadScheduleTimes();
        });
        thread.start();
        Toast.makeText(this, "Schedule deleted", Toast.LENGTH_SHORT).show();
    }
}