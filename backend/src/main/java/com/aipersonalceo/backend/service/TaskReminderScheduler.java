package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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

    public TaskReminderScheduler(
            TaskRepository taskRepository,
            TaskReminderService reminderService
    ) {
        this.taskRepository = taskRepository;
        this.reminderService = reminderService;
    }

    @Scheduled(cron = "0 * * * * *", zone = "Asia/Kolkata")
    public void sendDueReminders() {
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
