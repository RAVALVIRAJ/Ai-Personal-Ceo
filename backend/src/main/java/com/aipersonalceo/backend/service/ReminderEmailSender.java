package com.aipersonalceo.backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Locale;

/**
 * Sends the reminder email. Two providers, chosen by REMINDER_EMAIL_PROVIDER:
 * <ul>
 *   <li>{@code smtp} (default): Spring Mail. Works locally. Render's free tier
 *       blocks SMTP ports 25/465/587, so it will time out there.</li>
 *   <li>{@code resend}: HTTPS call to the Resend API. Use this on Render free.</li>
 * </ul>
 */
@Component
public class ReminderEmailSender {

    private static final URI RESEND_URL = URI.create("https://api.resend.com/emails");

    private final JavaMailSender mailSender;
    private final String provider;
    private final String emailFrom;
    private final String emailTo;
    private final String resendApiKey;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    public ReminderEmailSender(
            JavaMailSender mailSender,
            @Value("${app.reminders.provider:smtp}") String provider,
            @Value("${app.reminders.email-from:}") String emailFrom,
            @Value("${app.reminders.email-to:}") String emailTo,
            @Value("${app.reminders.resend-api-key:}") String resendApiKey
    ) {
        this.mailSender = mailSender;
        this.provider = provider == null ? "smtp" : provider.trim().toLowerCase(Locale.ROOT);
        this.emailFrom = emailFrom;
        this.emailTo = emailTo;
        this.resendApiKey = resendApiKey;
    }

    public void send(String subject, String body) {
        if (emailTo.isBlank() || emailFrom.isBlank()) {
            throw new IllegalStateException(
                    "Reminder email is not configured; set REMINDER_EMAIL_TO "
                            + "and REMINDER_EMAIL_FROM (or SMTP_USERNAME)."
            );
        }
        switch (provider) {
            case "resend" -> sendWithResend(subject, body);
            case "", "smtp" -> sendWithSmtp(subject, body);
            default -> throw new IllegalStateException(
                    "Unknown REMINDER_EMAIL_PROVIDER '" + provider
                            + "'; use 'smtp' or 'resend'."
            );
        }
    }

    private void sendWithSmtp(String subject, String body) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(emailFrom);
        message.setTo(emailTo);
        message.setSubject(subject);
        message.setText(body);
        mailSender.send(message);
    }

    private void sendWithResend(String subject, String body) {
        if (resendApiKey.isBlank()) {
            throw new IllegalStateException(
                    "RESEND_API_KEY is not set but REMINDER_EMAIL_PROVIDER=resend."
            );
        }
        String json = "{\"from\":" + quote(emailFrom)
                + ",\"to\":[" + quote(emailTo) + "]"
                + ",\"subject\":" + quote(subject)
                + ",\"text\":" + quote(body) + "}";

        HttpRequest request = HttpRequest.newBuilder(RESEND_URL)
                .timeout(Duration.ofSeconds(15))
                .header("Authorization", "Bearer " + resendApiKey)
                .header("Content-Type", "application/json")
                .header("User-Agent", "ai-personal-ceo")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        try {
            HttpResponse<String> response =
                    httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() / 100 != 2) {
                throw new IllegalStateException(
                        "Resend rejected the email (HTTP " + response.statusCode()
                                + "): " + response.body()
                );
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Interrupted while sending email", exception);
        } catch (IOException exception) {
            throw new IllegalStateException("Could not reach the Resend API", exception);
        }
    }

    private static String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        return out.append('"').toString();
    }
}
