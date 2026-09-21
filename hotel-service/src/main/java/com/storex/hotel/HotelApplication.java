package com.storex.hotel;

import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Mono;

@SpringBootApplication
@RestController
@RequestMapping("/api/hotels")
public class HotelApplication {
    private final Map<String, String> reservations = new ConcurrentHashMap<>();

    public static void main(String[] args) { SpringApplication.run(HotelApplication.class, args); }

    @PostMapping("/reserve")
    Mono<Reservation> reserve(@RequestBody ReserveRequest request) {
        if ("HOTEL_FAIL".equals(request.scenario())) {
            return Mono.error(new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY, "Khach san het phong"));
        }
        Mono<Reservation> result = Mono.fromSupplier(() -> {
            String id = "HTL-" + UUID.randomUUID().toString().substring(0, 8);
            reservations.put(id, "RESERVED");
            return new Reservation(id, "RESERVED");
        });
        return "HOTEL_TIMEOUT".equals(request.scenario()) ? result.delayElement(Duration.ofSeconds(5)) : result;
    }

    @DeleteMapping("/{id}")
    Mono<Reservation> cancel(@PathVariable String id) {
        reservations.computeIfPresent(id, (key, value) -> "CANCELLED");
        return Mono.just(new Reservation(id, reservations.getOrDefault(id, "CANCELLED")));
    }

    record ReserveRequest(String orderId, String hotelCode, String scenario) {}
    record Reservation(String id, String status) {}
}
