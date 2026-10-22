package com.aipersonalceo.backend.service;

import com.aipersonalceo.backend.dto.CreateEventRequest;
import com.aipersonalceo.backend.entity.Event;
import com.aipersonalceo.backend.repository.EventRepository;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
public class EventService {

    private final EventRepository eventRepository;

    public EventService(EventRepository eventRepository) {
        this.eventRepository = eventRepository;
    }

    public Event createEvent(CreateEventRequest request) {

    var existingEvent =
            eventRepository.findFirstByTitleIgnoreCaseAndEventDateAndStartTimeAndEndTime(
                    request.getTitle(),
                    request.getEventDate(),
                    request.getStartTime(),
                    request.getEndTime()
            );

    if (existingEvent.isPresent()) {
        return existingEvent.get();
    }

    Event event = new Event();

    event.setTitle(request.getTitle());
    event.setDescription(request.getDescription());
    event.setEventDate(request.getEventDate());
    event.setStartTime(request.getStartTime());
    event.setEndTime(request.getEndTime());

    return eventRepository.save(event);
    }

    public List<Event> getAllEvents() {
        return eventRepository.findAll();
    }

    public Event getEvent(Long id) {
        return eventRepository.findById(id)
                .orElseThrow(() ->
                        new ResponseStatusException(
                                HttpStatus.NOT_FOUND,
                                "Event not found: " + id
                        )
                );
    }

    public Event updateEvent(Long id, CreateEventRequest request) {

        Event event = eventRepository.findById(id)
                .orElseThrow(() ->
                        new RuntimeException("Event not found: " + id)
                );

        event.setTitle(request.getTitle());
        event.setDescription(request.getDescription());
        event.setEventDate(request.getEventDate());
        event.setStartTime(request.getStartTime());
        event.setEndTime(request.getEndTime());

        return eventRepository.save(event);
    }

    public void deleteEvent(Long id) {
        eventRepository.deleteById(id);
    }
}