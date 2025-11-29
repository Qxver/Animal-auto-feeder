package com.example.karmnik;

import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;
import java.util.List;

@Dao
public interface ScheduleTimeDao {
    @Insert
    void insert(ScheduleTime scheduleTime);

    @Update
    void update(ScheduleTime scheduleTime);

    @Delete
    void delete(ScheduleTime scheduleTime);

    @Query("SELECT * FROM schedule_times ORDER BY time ASC")
    List<ScheduleTime> getAllScheduleTimes();
}