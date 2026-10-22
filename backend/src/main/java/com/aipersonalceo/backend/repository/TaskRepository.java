package com.aipersonalceo.backend.repository;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Optional;

public interface TaskRepository extends JpaRepository<Task, Long> {

    List<Task> findByStatus(TaskStatus status);

    Optional<Task>
    findFirstByTitleIgnoreCaseAndDueDateAndDueTimeAndDurationMinutesAndStatusIn(
            String title,
            LocalDate dueDate,
            LocalTime dueTime,
            Integer durationMinutes,
            List<TaskStatus> statuses
    );

    List<Task> findByDueDate(LocalDate dueDate);

    List<Task> findByDueDateBetween(
            LocalDate startDate,
            LocalDate endDate
    );

    @Query("""
            select task from Task task
            where task.status in :statuses
              and task.dueDate is not null
              and task.dueTime is not null
              and task.reminderBeforeMinutes is not null
              and (task.notified = false or task.notified is null)
            """)
    List<Task> findReminderCandidates(
            @Param("statuses") List<TaskStatus> statuses
    );
}