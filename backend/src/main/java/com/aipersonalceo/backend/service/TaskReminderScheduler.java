package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.List;

@Component
public class TaskReminderScheduler {

    private static final Logger logger =
            LoggerFactory.getLogger(TaskReminderScheduler.class);
    private static final ZoneId TIME_ZONE = ZoneId.of("Asia/Kolkata");

    private final TaskRepository taskRepository;
    private final TaskReminderService reminderService;
    private final boolean enabled;
    private final long maxLateMinutes;

    public TaskReminderScheduler(
            TaskRepository taskRepository,
            TaskReminderService reminderService,
            @Value("${app.reminders.enabled:true}") boolean enabled,
            @Value("${app.reminders.max-late-minutes:1440}") long maxLateMinutes
    ) {
        this.taskRepository = taskRepository;
        this.reminderService = reminderService;
        this.enabled = enabled;
        this.maxLateMinutes = maxLateMinutes;
    }

    @Scheduled(cron = "0 * * * * *", zone = "Asia/Kolkata")
    public void sendDueReminders() {
        if (!enabled) {
            return;
        }
        LocalDateTime now = LocalDateTime.now(TIME_ZONE);
        List<Task> candidates = taskRepository.findReminderCandidates(
                List.of(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        );

        for (Task task : candidates) {
            LocalDateTime reminderAt = LocalDateTime.of(
                    task.getDueDate(),
                    task.getDueTime()
            ).minusMinutes(task.getReminderBeforeMinutes());
            if (reminderAt.isAfter(now)) {
                continue;
            }
            // Do not email about tasks that were due long ago (for example
            // old rows when reminders are first switched on).
            LocalDateTime dueAt = LocalDateTime.of(
                    task.getDueDate(),
                    task.getDueTime()
            );
            if (dueAt.plusMinutes(maxLateMinutes).isBefore(now)) {
                continue;
            }

            try {
                reminderService.sendReminder(task.getId());
            } catch (RuntimeException exception) {
                logger.error(
                        "Failed to send reminder for task {}",
                        task.getId(),
                        exception
                );
            }
        }
    }
}
