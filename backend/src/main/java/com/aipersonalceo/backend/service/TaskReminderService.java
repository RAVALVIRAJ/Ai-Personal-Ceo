package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskRecurrence;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;

@Service
public class TaskReminderService {

    private final TaskRepository taskRepository;
    private final JavaMailSender mailSender;
    private final String emailFrom;
    private final String emailTo;

    public TaskReminderService(
            TaskRepository taskRepository,
            JavaMailSender mailSender,
            @Value("${app.reminders.email-from:}") String emailFrom,
            @Value("${app.reminders.email-to:}") String emailTo
    ) {
        this.taskRepository = taskRepository;
        this.mailSender = mailSender;
        this.emailFrom = emailFrom;
        this.emailTo = emailTo;
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

        if (emailTo.isBlank() || emailFrom.isBlank()) {
            throw new IllegalStateException(
                    "Reminder email is not configured; set REMINDER_EMAIL_TO "
                            + "and REMINDER_EMAIL_FROM (or SMTP_USERNAME)."
            );
        }

        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(emailFrom);
        message.setTo(emailTo);
        message.setSubject("Task reminder: " + task.getTitle());
        message.setText(
                "This is a reminder for your task: " + task.getTitle()
                        + "\nDue: " + task.getDueDate() + " at " + task.getDueTime()
        );
        mailSender.send(message);

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
