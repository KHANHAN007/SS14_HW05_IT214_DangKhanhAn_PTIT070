package com.storex.payment;

import java.math.BigDecimal;
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
@RequestMapping("/api/payments")
public class PaymentApplication {
    private final Map<String, String> payments = new ConcurrentHashMap<>();

    public static void main(String[] args) { SpringApplication.run(PaymentApplication.class, args); }

    @PostMapping("/charge")
    Mono<Payment> charge(@RequestBody ChargeRequest request) {
        if ("PAYMENT_FAIL".equals(request.scenario())) {
            return Mono.error(new ResponseStatusException(HttpStatus.PAYMENT_REQUIRED, "Thanh toan bi tu choi"));
        }
        String id = "PAY-" + UUID.randomUUID().toString().substring(0, 8);
        payments.put(id, "PAID");
        return Mono.just(new Payment(id, "PAID"));
    }

    @PostMapping("/{id}/refund")
    Mono<Payment> refund(@PathVariable String id) {
        payments.computeIfPresent(id, (key, value) -> "REFUNDED");
        return Mono.just(new Payment(id, payments.getOrDefault(id, "REFUNDED")));
    }

    record ChargeRequest(String orderId, BigDecimal amount, String scenario) {}
    record Payment(String id, String status) {}
}
