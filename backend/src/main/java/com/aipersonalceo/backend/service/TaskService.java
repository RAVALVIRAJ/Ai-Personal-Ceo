package com.aipersonalceo.backend.service;
import com.aipersonalceo.backend.exception.ResourceNotFoundException;
import com.aipersonalceo.backend.dto.CreateTaskRequest;
import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.entity.TaskRecurrence;
import com.aipersonalceo.backend.entity.TaskStatus;
import com.aipersonalceo.backend.repository.TaskRepository;
import org.springframework.stereotype.Service;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.List;

@Service
public class TaskService {

    private final TaskRepository taskRepository;

    public TaskService(TaskRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    // =========================================================
    // CREATE
    // =========================================================

    public Task createTask(CreateTaskRequest request) {

        List<TaskStatus> activeStatuses = List.of(
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS
        );

        var existingTask =
                taskRepository
                        .findFirstByTitleIgnoreCaseAndDueDateAndDueTimeAndDurationMinutesAndStatusIn(
                                request.getTitle(),
                                request.getDueDate(),
                                request.getDueTime(),
                                request.getDurationMinutes(),
                                activeStatuses
                        );

        if (existingTask.isPresent()) {
            Task existing = existingTask.get();
            boolean reminderChanged =
                    !java.util.Objects.equals(
                            existing.getReminderBeforeMinutes(),
                            request.getReminderBeforeMinutes()
                    ) || existing.getRecurrence() != request.getRecurrence();
            existing.setReminderBeforeMinutes(request.getReminderBeforeMinutes());
            existing.setRecurrence(request.getRecurrence());
            if (reminderChanged) {
                existing.setNotified(false);
            }
            return reminderChanged ? taskRepository.save(existing) : existing;
        }

        Task task = new Task();

        task.setTitle(request.getTitle());
        task.setDescription(request.getDescription());
        task.setDueDate(request.getDueDate());
        task.setDueTime(request.getDueTime());
        task.setDurationMinutes(request.getDurationMinutes());
        task.setReminderBeforeMinutes(request.getReminderBeforeMinutes());
        task.setRecurrence(request.getRecurrence());
        task.setStatus(TaskStatus.PENDING);

        return taskRepository.save(task);
    }

    // =========================================================
    // GET ALL
    // =========================================================

    public List<Task> getAllTasks() {
        return taskRepository.findAll();
    }

    // =========================================================
    // GET ONE
    // =========================================================

    public Task getTask(Long id) {
    return taskRepository.findById(id)
            .orElseThrow(() ->
                    new ResourceNotFoundException(
                            "Task not found: " + id
                    )
            );
    }

    // =========================================================
    // UPDATE
    // =========================================================

    public Task updateTask(
            Long id,
            CreateTaskRequest request
    ) {

        Task task = getTask(id);

        boolean scheduleChanged =
                !java.util.Objects.equals(task.getDueDate(), request.getDueDate())
                || !java.util.Objects.equals(task.getDueTime(), request.getDueTime())
                || !java.util.Objects.equals(
                        task.getReminderBeforeMinutes(),
                        request.getReminderBeforeMinutes()
                );
        task.setTitle(request.getTitle());
        task.setDescription(request.getDescription());
        task.setDueDate(request.getDueDate());
        task.setDueTime(request.getDueTime());
        task.setDurationMinutes(request.getDurationMinutes());
        task.setReminderBeforeMinutes(request.getReminderBeforeMinutes());
        task.setRecurrence(request.getRecurrence());
        if (scheduleChanged) {
            task.setNotified(false);
        }

        return taskRepository.save(task);
    }

    // =========================================================
    // COMPLETE
    // =========================================================

    public Task completeTask(Long id) {

    Task task = getTask(id);

    if (task.getStatus() == TaskStatus.COMPLETED) {
        return task;
    }

    task.setStatus(TaskStatus.COMPLETED);

    return taskRepository.save(task);
}

    // =========================================================
    // DELETE
    // =========================================================

    public void deleteTask(Long id) {

    if (!taskRepository.existsById(id)) {
        throw new ResourceNotFoundException(
                "Task not found: " + id
        );
    }

    taskRepository.deleteById(id);
}

    // =========================================================
    // TODAY
    // =========================================================

    public List<Task> getTodayTasks() {

        return taskRepository.findByDueDate(
                LocalDate.now()
        );
    }

    // =========================================================
    // TOMORROW
    // =========================================================

    public List<Task> getTomorrowTasks() {

        return taskRepository.findByDueDate(
                LocalDate.now().plusDays(1)
        );
    }

    // =========================================================
    // THIS WEEK
    // =========================================================

    public List<Task> getWeekTasks() {

        LocalDate today = LocalDate.now();

        LocalDate monday =
                today.with(DayOfWeek.MONDAY);

        LocalDate sunday =
                monday.plusDays(6);

        return taskRepository.findByDueDateBetween(
                monday,
                sunday
        );
    }
}