package com.aipersonalceo.backend.controller;

import com.aipersonalceo.backend.dto.CreateTaskRequest;
import com.aipersonalceo.backend.entity.Task;
import com.aipersonalceo.backend.service.TaskService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/tasks")
public class TaskController {

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    // CREATE
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Task createTask(
            @Valid @RequestBody CreateTaskRequest request
    ) {
        return taskService.createTask(request);
    }

    // GET ALL
    @GetMapping
    public List<Task> getAllTasks() {
        return taskService.getAllTasks();
    }

    // GET ONE
    @GetMapping("/{id}")
    public Task getTask(@PathVariable Long id) {
        return taskService.getTask(id);
    }

    // DELETE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteTask(@PathVariable Long id) {
        taskService.deleteTask(id);
    }

    // UPDATE
    @PutMapping("/{id}")
    public Task updateTask(
            @PathVariable Long id,
            @Valid @RequestBody CreateTaskRequest request
    ) {
        return taskService.updateTask(id, request);
    }

    // COMPLETE
    @PatchMapping("/{id}/complete")
    public Task completeTask(@PathVariable Long id) {
        return taskService.completeTask(id);
    }

    // TODAY
    @GetMapping("/today")
    public List<Task> getTodayTasks() {
        return taskService.getTodayTasks();
    }

    // TOMORROW
    @GetMapping("/tomorrow")
    public List<Task> getTomorrowTasks() {
        return taskService.getTomorrowTasks();
    }

    // WEEK
    @GetMapping("/week")
    public List<Task> getWeekTasks() {
        return taskService.getWeekTasks();
    }
}