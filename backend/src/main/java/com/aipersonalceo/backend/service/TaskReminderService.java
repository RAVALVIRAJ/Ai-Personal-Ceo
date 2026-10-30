package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskRecurrence;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;

@Service
public class TaskReminderService {

    private final TaskRepository taskRepository;
    private final ReminderEmailSender emailSender;

    public TaskReminderService(
            TaskRepository taskRepository,
            ReminderEmailSender emailSender
    ) {
        this.taskRepository = taskRepository;
        this.emailSender = emailSender;
    }

    @Transactional
    public void sendReminder(Long taskId) {
        Task task = taskRepository.findById(taskId)
                .orElseThrow(() -> new IllegalStateException(
                        "Reminder task no longer exists: " + taskId
                ));

        if (Boolean.TRUE.equals(task.getNotified())
                || (task.getStatus() != TaskStatus.PENDING
                && task.getStatus() != TaskStatus.IN_PROGRESS)
                || task.getDueDate() == null
                || task.getDueTime() == null
                || task.getReminderBeforeMinutes() == null) {
            return;
        }

        emailSender.send(
                "Task reminder: " + task.getTitle(),
                "This is a reminder for your task: " + task.getTitle()
                        + "\nDue: " + task.getDueDate() + " at " + task.getDueTime()
        );

        task.setNotified(true);
        taskRepository.save(task);

        TaskRecurrence recurrence = task.getRecurrence();
        if (recurrence != TaskRecurrence.NONE) {
            createNextOccurrence(task, recurrence);
        }
    }

    private void createNextOccurrence(Task task, TaskRecurrence recurrence) {
        LocalDate nextDate = switch (recurrence) {
            case DAILY -> task.getDueDate().plusDays(1);
            case WEEKLY -> task.getDueDate().plusWeeks(1);
            case MONTHLY -> task.getDueDate().plusMonths(1);
            case NONE -> task.getDueDate();
        };

        Task next = new Task();
        next.setTitle(task.getTitle());
        next.setDescription(task.getDescription());
        next.setDueDate(nextDate);
        next.setDueTime(task.getDueTime());
        next.setDurationMinutes(task.getDurationMinutes());
        next.setReminderBeforeMinutes(task.getReminderBeforeMinutes());
        next.setRecurrence(recurrence);
        next.setNotified(false);
        next.setStatus(TaskStatus.PENDING);
        taskRepository.save(next);
    }
}
