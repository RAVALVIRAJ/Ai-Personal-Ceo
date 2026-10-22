package com.aipersonalceo.backend.entity;

import jakarta.persistence.*;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.LocalDateTime;

@Entity
@Table(name = "tasks")
public class Task {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(length = 2000)
    private String description;

    private LocalDate dueDate;

    private LocalTime dueTime;

    private Integer durationMinutes;

    private Integer reminderBeforeMinutes;

    @Enumerated(EnumType.STRING)
    private TaskRecurrence recurrence = TaskRecurrence.NONE;

    private Boolean notified = false;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TaskStatus status = TaskStatus.PENDING;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    public Task() {
    }

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public LocalDate getDueDate() {
        return dueDate;
    }

    public void setDueDate(LocalDate dueDate) {
        this.dueDate = dueDate;
    }

    public LocalTime getDueTime() {
        return dueTime;
    }

    public void setDueTime(LocalTime dueTime) {
        this.dueTime = dueTime;
    }

    public Integer getDurationMinutes() {
        return durationMinutes;
    }

    public void setDurationMinutes(Integer durationMinutes) {
        this.durationMinutes = durationMinutes;
    }

    public Integer getReminderBeforeMinutes() {
        return reminderBeforeMinutes;
    }

    public void setReminderBeforeMinutes(Integer reminderBeforeMinutes) {
        this.reminderBeforeMinutes = reminderBeforeMinutes;
    }

    public TaskRecurrence getRecurrence() {
        return recurrence == null ? TaskRecurrence.NONE : recurrence;
    }

    public void setRecurrence(TaskRecurrence recurrence) {
        this.recurrence = recurrence == null ? TaskRecurrence.NONE : recurrence;
    }

    public Boolean getNotified() {
        return Boolean.TRUE.equals(notified);
    }

    public void setNotified(Boolean notified) {
        this.notified = Boolean.TRUE.equals(notified);
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}