package com.storex.combo;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

@SpringBootApplication
public class ComboApplication {
    public static void main(String[] args) { SpringApplication.run(ComboApplication.class, args); }
    @Bean WebClient.Builder webClientBuilder() { return WebClient.builder(); }
}

@RestController
@RequestMapping("/api/combo-bookings")
class ComboController {
    private final ComboSagaService service;
    ComboController(ComboSagaService service) { this.service = service; }

    @PostMapping
    Mono<ComboResult> book(@RequestBody ComboRequest request) { return service.book(request); }
}

@org.springframework.stereotype.Service
class ComboSagaService {
    private final WebClient flight;
    private final WebClient hotel;
    private final WebClient payment;
    private final Duration hotelTimeout;
    private final int retryCount;
    private final Duration retryDelay;

    ComboSagaService(WebClient.Builder builder,
                     @Value("${partners.flight-url}") String flightUrl,
                     @Value("${partners.hotel-url}") String hotelUrl,
                     @Value("${partners.payment-url}") String paymentUrl,
                     @Value("${partners.hotel-timeout}") Duration hotelTimeout,
                     @Value("${partners.retry-count}") int retryCount,
                     @Value("${partners.retry-delay}") Duration retryDelay) {
        this.flight = builder.clone().baseUrl(flightUrl).build();
        this.hotel = builder.clone().baseUrl(hotelUrl).build();
        this.payment = builder.clone().baseUrl(paymentUrl).build();
        this.hotelTimeout = hotelTimeout;
        this.retryCount = retryCount;
        this.retryDelay = retryDelay;
    }

    Mono<ComboResult> book(ComboRequest request) {
        return Mono.defer(() -> {
            SagaContext ctx = new SagaContext("COMBO-" + UUID.randomUUID().toString().substring(0, 8));
            return reserveFlight(ctx, request)
                    .then(reserveHotel(ctx, request))
                    .then(charge(ctx, request))
                    .then(Mono.fromSupplier(ctx::success))
                    .onErrorResume(error -> compensate(ctx)
                            .thenReturn(ctx.failed("Da bu tru giao dich: " + rootMessage(error))));
        });
    }

    private Mono<Void> reserveFlight(SagaContext ctx, ComboRequest request) {
        return flight.post().uri("/api/flights/reserve")
                .bodyValue(new FlightRequest(ctx.orderId, request.flightCode()))
                .retrieve().bodyToMono(PartnerResult.class)
                .doOnNext(result -> ctx.flightId = result.id()).then();
    }

    private Mono<Void> reserveHotel(SagaContext ctx, ComboRequest request) {
        return hotel.post().uri("/api/hotels/reserve")
                .bodyValue(new HotelRequest(ctx.orderId, request.hotelCode(), request.scenario()))
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError,
                        response -> response.createException().flatMap(Mono::error))
                .bodyToMono(PartnerResult.class)
                .timeout(hotelTimeout)
                .retryWhen(Retry.fixedDelay(retryCount, retryDelay)
                        .filter(error -> !(error instanceof org.springframework.web.reactive.function.client.WebClientResponseException.UnprocessableEntity)))
                .doOnNext(result -> ctx.hotelId = result.id()).then();
    }

    private Mono<Void> charge(SagaContext ctx, ComboRequest request) {
        return payment.post().uri("/api/payments/charge")
                .bodyValue(new PaymentRequest(ctx.orderId, request.amount(), request.scenario()))
                .retrieve().bodyToMono(PartnerResult.class)
                .doOnNext(result -> ctx.paymentId = result.id()).then();
    }

    private Mono<Void> compensate(SagaContext ctx) {
        Mono<Void> refund = ctx.paymentId == null ? Mono.empty() : payment.post()
                .uri("/api/payments/{id}/refund", ctx.paymentId).retrieve().bodyToMono(Void.class)
                .onErrorResume(error -> Mono.empty());
        Mono<Void> cancelHotel = ctx.hotelId == null ? Mono.empty() : hotel.delete()
                .uri("/api/hotels/{id}", ctx.hotelId).retrieve().bodyToMono(Void.class)
                .onErrorResume(error -> Mono.empty());
        Mono<Void> cancelFlight = ctx.flightId == null ? Mono.empty() : flight.delete()
                .uri("/api/flights/{id}", ctx.flightId).retrieve().bodyToMono(Void.class)
                .onErrorResume(error -> Mono.empty());
        return refund.then(cancelHotel).then(cancelFlight);
    }

    private String rootMessage(Throwable error) {
        Throwable current = error;
        while (current.getCause() != null) current = current.getCause();
        return current.getMessage();
    }
}

record ComboRequest(String customerId, String flightCode, String hotelCode,
                    BigDecimal amount, String scenario) {}
record ComboResult(String orderId, String status, String flightReservationId,
                   String hotelReservationId, String paymentId, String message) {}
record PartnerResult(String id, String status) {}
record FlightRequest(String orderId, String flightCode) {}
record HotelRequest(String orderId, String hotelCode, String scenario) {}
record PaymentRequest(String orderId, BigDecimal amount, String scenario) {}

class SagaContext {
    final String orderId;
    String flightId;
    String hotelId;
    String paymentId;
    SagaContext(String orderId) { this.orderId = orderId; }
    ComboResult success() {
        return new ComboResult(orderId, "CONFIRMED", flightId, hotelId, paymentId,
                "Dat combo thanh cong");
    }
    ComboResult failed(String message) {
        return new ComboResult(orderId, "CANCELLED", flightId, hotelId, paymentId, message);
    }
}
