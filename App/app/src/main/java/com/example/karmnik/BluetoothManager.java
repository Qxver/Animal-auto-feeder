package com.example.karmnik;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import androidx.core.app.ActivityCompat;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public class BluetoothManager {
    private static final String TAG = "BluetoothManager";
    private static final UUID MY_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothSocket bluetoothSocket;
    private OutputStream outputStream;
    private InputStream inputStream;
    private Context context;
    private ConnectionListener connectionListener;
    private Thread workerThread;
    private boolean isConnected = false;

    public interface ConnectionListener {
        void onConnected();
        void onDisconnected();
        void onError(String error);
        void onMessageReceived(String message);
    }

    public BluetoothManager(Context context) {
        this.context = context;
        this.bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
    }

    public void setConnectionListener(ConnectionListener listener) {
        this.connectionListener = listener;
    }

    public boolean isBluetoothAvailable() {
        return bluetoothAdapter != null;
    }

    public boolean isBluetoothEnabled() {
        return bluetoothAdapter != null && bluetoothAdapter.isEnabled();
    }

    public List<BluetoothDevice> getPairedDevices() {
        List<BluetoothDevice> devices = new ArrayList<>();
        if (bluetoothAdapter != null) {
            if (ActivityCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT)
                    == PackageManager.PERMISSION_GRANTED) {
                Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();
                if (pairedDevices != null) {
                    devices.addAll(pairedDevices);
                    Log.d(TAG, "Znaleziono " + devices.size() + " sparowanych urządzeń");
                    for (BluetoothDevice device : devices) {
                        Log.d(TAG, "Urządzenie: " + device.getName() + " [" + device.getAddress() + "]");
                    }
                } else {
                    Log.w(TAG, "getBondedDevices() zwróciło null");
                }
            } else {
                Log.e(TAG, "Brak uprawnienia BLUETOOTH_CONNECT");
            }
        } else {
            Log.e(TAG, "BluetoothAdapter jest null");
        }
        return devices;
    }

    public void connect(BluetoothDevice device) {
        new Thread(() -> {
            try {
                bluetoothSocket = device.createRfcommSocketToServiceRecord(MY_UUID);
                bluetoothAdapter.cancelDiscovery();
                bluetoothSocket.connect();

                outputStream = bluetoothSocket.getOutputStream();
                inputStream = bluetoothSocket.getInputStream();

                isConnected = true;
                startListening();
                notifyConnected();

            } catch (SecurityException e) {
                Log.e(TAG, "Security exception - missing permissions", e);
                notifyError("Brak uprawnień Bluetooth. Włącz w ustawieniach aplikacji.");
                disconnect();
            } catch (IOException e) {
                Log.e(TAG, "Connection failed", e);
                notifyError("Nie udało się połączyć: " + e.getMessage());
                disconnect();
            }
        }).start();
    }

    private void startListening() {
        workerThread = new Thread(() -> {
            byte[] buffer = new byte[1024];
            int bytes;

            while (isConnected) {
                try {
                    bytes = inputStream.read(buffer);
                    String message = new String(buffer, 0, bytes);
                    notifyMessageReceived(message);
                } catch (IOException e) {
                    if (isConnected) {
                        Log.e(TAG, "Connection lost", e);
                        disconnect();
                    }
                    break;
                }
            }
        });
        workerThread.start();
    }

    public void sendSchedule(List<ScheduleTime> scheduleList) {
        if (!isConnected) {
            notifyError("Nie połączono z urządzeniem");
            return;
        }

        new Thread(() -> {
            try {
                StringBuilder json = new StringBuilder("{\"schedules\":[");
                for (int i = 0; i < scheduleList.size(); i++) {
                    if (i > 0) json.append(",");
                    json.append("\"").append(scheduleList.get(i).time).append("\"");
                }
                json.append("]}\n");

                outputStream.write(json.toString().getBytes());
                outputStream.flush();
                Log.d(TAG, "Schedule sent: " + json);

            } catch (IOException e) {
                Log.e(TAG, "Failed to send schedule", e);
                notifyError("Błąd wysyłania harmonogramu: " + e.getMessage());
            }
        }).start();
    }

    public void testServo() {
        sendCommand("TEST");
    }

    public void sendCommand(String command) {
        if (!isConnected) {
            notifyError("Nie połączono z urządzeniem");
            return;
        }

        new Thread(() -> {
            try {
                outputStream.write((command + "\n").getBytes());
                outputStream.flush();
                Log.d(TAG, "Command sent: " + command);
            } catch (IOException e) {
                Log.e(TAG, "Failed to send command", e);
                notifyError("Błąd wysyłania komendy: " + e.getMessage());
            }
        }).start();
    }

    public void disconnect() {
        isConnected = false;

        try {
            if (workerThread != null) {
                workerThread.interrupt();
            }
            if (outputStream != null) {
                outputStream.close();
            }
            if (inputStream != null) {
                inputStream.close();
            }
            if (bluetoothSocket != null) {
                bluetoothSocket.close();
            }
        } catch (IOException e) {
            Log.e(TAG, "Error closing connection", e);
        }

        notifyDisconnected();
    }

    public boolean isConnected() {
        return isConnected;
    }

    private void notifyConnected() {
        if (connectionListener != null) {
            new Handler(Looper.getMainLooper()).post(() -> connectionListener.onConnected());
        }
    }

    private void notifyDisconnected() {
        if (connectionListener != null) {
            new Handler(Looper.getMainLooper()).post(() -> connectionListener.onDisconnected());
        }
    }

    private void notifyError(String error) {
        if (connectionListener != null) {
            new Handler(Looper.getMainLooper()).post(() -> connectionListener.onError(error));
        }
    }

    private void notifyMessageReceived(String message) {
        if (connectionListener != null) {
            new Handler(Looper.getMainLooper()).post(() -> connectionListener.onMessageReceived(message));
        }
    }
}