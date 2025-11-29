package com.example.karmnik;

import android.Manifest;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity implements ScheduleAdapter.ScheduleAdapterListener {
    private static final int REQUEST_ENABLE_BT = 1;
    private static final int REQUEST_BLUETOOTH_PERMISSIONS = 2;

    private AppDatabase db;
    private RecyclerView recyclerView;
    private ScheduleAdapter adapter;
    private List<ScheduleTime> scheduleList;
    private FloatingActionButton addScheduleFab;
    private BluetoothManager bluetoothManager;
    private MenuItem connectMenuItem;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize database
        db = AppDatabase.getDatabase(this);

        // Initialize Bluetooth
        bluetoothManager = new BluetoothManager(this);
        bluetoothManager.setConnectionListener(new BluetoothManager.ConnectionListener() {
            @Override
            public void onConnected() {
                Toast.makeText(MainActivity.this, "Połączono z Raspberry Pi", Toast.LENGTH_SHORT).show();
                updateConnectionMenuItem(true);
                syncScheduleToDevice();
            }

            @Override
            public void onDisconnected() {
                Toast.makeText(MainActivity.this, "Rozłączono", Toast.LENGTH_SHORT).show();
                updateConnectionMenuItem(false);
            }

            @Override
            public void onError(String error) {
                Toast.makeText(MainActivity.this, error, Toast.LENGTH_LONG).show();
            }

            @Override
            public void onMessageReceived(String message) {
                Toast.makeText(MainActivity.this, "Wiadomość: " + message, Toast.LENGTH_SHORT).show();
            }
        });

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

        // Check Bluetooth permissions
        checkBluetoothPermissions();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.main_menu, menu);
        connectMenuItem = menu.findItem(R.id.action_connect);
        updateConnectionMenuItem(bluetoothManager.isConnected());
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        int id = item.getItemId();

        if (id == R.id.action_connect) {
            if (bluetoothManager.isConnected()) {
                bluetoothManager.disconnect();
            } else {
                showDeviceSelectionDialog();
            }
            return true;
        } else if (id == R.id.action_sync) {
            syncScheduleToDevice();
            return true;
        } else if (id == R.id.action_test) {
            bluetoothManager.testServo();
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    private void updateConnectionMenuItem(boolean connected) {
        if (connectMenuItem != null) {
            if (connected) {
                connectMenuItem.setTitle("Rozłącz");
                connectMenuItem.setIcon(R.drawable.ic_bluetooth_connected);
            } else {
                connectMenuItem.setTitle("Połącz");
                connectMenuItem.setIcon(R.drawable.ic_bluetooth);
            }
        }
    }

    private void checkBluetoothPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            String[] permissions = {
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.ACCESS_FINE_LOCATION
            };

            List<String> neededPermissions = new ArrayList<>();
            for (String permission : permissions) {
                if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                    neededPermissions.add(permission);
                }
            }

            if (!neededPermissions.isEmpty()) {
                ActivityCompat.requestPermissions(this,
                        neededPermissions.toArray(new String[0]),
                        REQUEST_BLUETOOTH_PERMISSIONS);
            }
        } else {
            String[] permissions = {
                    Manifest.permission.BLUETOOTH,
                    Manifest.permission.BLUETOOTH_ADMIN,
                    Manifest.permission.ACCESS_FINE_LOCATION
            };

            List<String> neededPermissions = new ArrayList<>();
            for (String permission : permissions) {
                if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                    neededPermissions.add(permission);
                }
            }

            if (!neededPermissions.isEmpty()) {
                ActivityCompat.requestPermissions(this,
                        neededPermissions.toArray(new String[0]),
                        REQUEST_BLUETOOTH_PERMISSIONS);
            }
        }
    }

    private void showDeviceSelectionDialog() {
        if (!bluetoothManager.isBluetoothAvailable()) {
            Toast.makeText(this, "Bluetooth nie jest dostępne", Toast.LENGTH_SHORT).show();
            return;
        }

        if (!bluetoothManager.isBluetoothEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
                    == PackageManager.PERMISSION_GRANTED) {
                startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
            }
            return;
        }

        List<BluetoothDevice> devices = bluetoothManager.getPairedDevices();
        if (devices.isEmpty()) {
            Toast.makeText(this, "Brak sparowanych urządzeń", Toast.LENGTH_SHORT).show();
            return;
        }

        String[] deviceNames = new String[devices.size()];
        for (int i = 0; i < devices.size(); i++) {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
                    == PackageManager.PERMISSION_GRANTED) {
                String name = devices.get(i).getName();
                String address = devices.get(i).getAddress();
                deviceNames[i] = name != null ? name + "\n" + address : address;
            }
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Wybierz Raspberry Pi")
                .setItems(deviceNames, (dialog, which) -> {
                    BluetoothDevice device = devices.get(which);
                    Toast.makeText(this, "Łączenie...", Toast.LENGTH_SHORT).show();
                    bluetoothManager.connect(device);
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void syncScheduleToDevice() {
        if (!bluetoothManager.isConnected()) {
            Toast.makeText(this, "Najpierw połącz się z urządzeniem", Toast.LENGTH_SHORT).show();
            return;
        }

        Thread thread = new Thread(() -> {
            List<ScheduleTime> schedules = db.scheduleTimeDao().getAllScheduleTimes();
            bluetoothManager.sendSchedule(schedules);
            runOnUiThread(() -> Toast.makeText(this, "Synchronizacja harmonogramu...", Toast.LENGTH_SHORT).show());
        });
        thread.start();
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
        builder.setTitle("Dodaj godzinę karmienia");

        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setHint("HH:mm");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(16, 16, 16, 16);
        layout.addView(input);

        builder.setView(layout);
        builder.setPositiveButton("Dodaj", (dialog, which) -> {
            String time = input.getText().toString().trim();
            if (!time.isEmpty()) {
                if (isValidTimeFormat(time)) {
                    ScheduleTime scheduleTime = new ScheduleTime(time);
                    Thread thread = new Thread(() -> {
                        db.scheduleTimeDao().insert(scheduleTime);
                        loadScheduleTimes();
                        if (bluetoothManager.isConnected()) {
                            runOnUiThread(() -> syncScheduleToDevice());
                        }
                    });
                    thread.start();
                } else {
                    Toast.makeText(this, "Nieprawidłowy format. Użyj HH:mm", Toast.LENGTH_SHORT).show();
                }
            }
        });
        builder.setNegativeButton("Anuluj", (dialog, which) -> dialog.cancel());
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
            if (bluetoothManager.isConnected()) {
                runOnUiThread(() -> syncScheduleToDevice());
            }
        });
        thread.start();
        Toast.makeText(this, "Harmonogram zaktualizowany", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onDelete(ScheduleTime scheduleTime) {
        Thread thread = new Thread(() -> {
            db.scheduleTimeDao().delete(scheduleTime);
            loadScheduleTimes();
            if (bluetoothManager.isConnected()) {
                runOnUiThread(() -> syncScheduleToDevice());
            }
        });
        thread.start();
        Toast.makeText(this, "Harmonogram usunięty", Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (bluetoothManager != null) {
            bluetoothManager.disconnect();
        }
    }
}