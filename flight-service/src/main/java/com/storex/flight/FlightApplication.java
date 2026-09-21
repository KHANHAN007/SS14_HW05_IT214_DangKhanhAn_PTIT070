package com.storex.flight;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@SpringBootApplication
@RestController
@RequestMapping("/api/flights")
public class FlightApplication {
    private final Map<String, String> reservations = new ConcurrentHashMap<>();

    public static void main(String[] args) { SpringApplication.run(FlightApplication.class, args); }

    @PostMapping("/reserve")
    Mono<Reservation> reserve(@RequestBody ReserveRequest request) {
        String id = "FLT-" + UUID.randomUUID().toString().substring(0, 8);
        reservations.put(id, "RESERVED");
        return Mono.just(new Reservation(id, "RESERVED"));
    }

    @DeleteMapping("/{id}")
    Mono<Reservation> cancel(@PathVariable String id) {
        reservations.computeIfPresent(id, (key, value) -> "CANCELLED");
        return Mono.just(new Reservation(id, reservations.getOrDefault(id, "CANCELLED")));
    }

    record ReserveRequest(String orderId, String flightCode) {}
    record Reservation(String id, String status) {}
}
