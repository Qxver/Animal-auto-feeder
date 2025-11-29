package com.example.karmnik;

import androidx.room.Entity;
import androidx.room.Ignore;
import androidx.room.PrimaryKey;

@Entity(tableName = "schedule_times")
public class ScheduleTime {
    @PrimaryKey(autoGenerate = true)
    public int id;
    
    public String time;

    public ScheduleTime(int id, String time) {
        this.id = id;
        this.time = time;
    }

    @Ignore
    public ScheduleTime(String time) {
        this.time = time;
    }
}