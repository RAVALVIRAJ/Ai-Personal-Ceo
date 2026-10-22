package com.aipersonalceo.backend.repository;

import com.aipersonalceo.backend.entity.Event;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Optional;

public interface EventRepository extends JpaRepository<Event, Long> {

    Optional<Event> findFirstByTitleIgnoreCaseAndEventDateAndStartTimeAndEndTime(
            String title,
            LocalDate eventDate,
            LocalTime startTime,
            LocalTime endTime
    );
}