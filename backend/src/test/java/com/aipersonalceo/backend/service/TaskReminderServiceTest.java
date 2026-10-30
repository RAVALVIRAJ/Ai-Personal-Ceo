package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskRecurrence;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class TaskReminderServiceTest {

    @Mock
    private TaskRepository taskRepository;

    @Mock
    private ReminderEmailSender emailSender;

    private TaskReminderService reminderService;

    @BeforeEach
    void setUp() {
        reminderService = new TaskReminderService(taskRepository, emailSender);
    }

    @Test
    void sendsReminderAndCreatesNextRecurringTask() {
        Task task = createTask(TaskRecurrence.WEEKLY);
        when(taskRepository.findById(7L)).thenReturn(Optional.of(task));
        when(taskRepository.save(any(Task.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        reminderService.sendReminder(7L);

        verify(emailSender).send(
                org.mockito.ArgumentMatchers.eq("Task reminder: Submit report"),
                contains("Submit report")
        );
        assertTrue(task.getNotified());

        ArgumentCaptor<Task> savedTasks = ArgumentCaptor.forClass(Task.class);
        verify(taskRepository, org.mockito.Mockito.times(2)).save(savedTasks.capture());
        Task nextOccurrence = savedTasks.getAllValues().get(1);
        assertEquals(LocalDate.of(2026, 10, 29), nextOccurrence.getDueDate());
        assertEquals(TaskRecurrence.WEEKLY, nextOccurrence.getRecurrence());
        assertFalse(nextOccurrence.getNotified());
        assertEquals(TaskStatus.PENDING, nextOccurrence.getStatus());
    }

    @Test
    void doesNotCreateOccurrenceForNonRecurringTask() {
        Task task = createTask(TaskRecurrence.NONE);
        when(taskRepository.findById(7L)).thenReturn(Optional.of(task));

        reminderService.sendReminder(7L);

        verify(emailSender).send(anyString(), anyString());
        verify(taskRepository).save(task);
        verify(taskRepository, never()).save(
                org.mockito.ArgumentMatchers.argThat(saved -> saved != task)
        );
    }

    private Task createTask(TaskRecurrence recurrence) {
        Task task = new Task();
        task.setTitle("Submit report");
        task.setDueDate(LocalDate.of(2026, 10, 22));
        task.setDueTime(LocalTime.of(16, 0));
        task.setReminderBeforeMinutes(15);
        task.setRecurrence(recurrence);
        task.setStatus(TaskStatus.PENDING);
        return task;
    }
}
