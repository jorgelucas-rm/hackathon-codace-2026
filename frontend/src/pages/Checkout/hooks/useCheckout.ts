import { UseMutationResult, UseQueryResult, useMutation, useQuery } from "@tanstack/react-query";
import { BookingRead, PaymentRead, confirmPayment, getBooking, getPayment } from "../../../services/booking.service";

// Anotação de retorno explícita + cast — ver comentário em
// `pages/Schedule/hooks/useSchedule.ts`/`hooks/useCompanies.ts`.
export function usePayment(paymentId: number | null): UseQueryResult<PaymentRead> {
    return useQuery<PaymentRead>({
        queryKey: ["payment", paymentId],
        queryFn: () => getPayment(paymentId as number),
        enabled: !!paymentId,
        staleTime: 5 * 1000,
    }) as UseQueryResult<PaymentRead>;
}

export function useBookingByPayment(bookingId: number | undefined): UseQueryResult<BookingRead> {
    return useQuery<BookingRead>({
        queryKey: ["booking", bookingId],
        queryFn: () => getBooking(bookingId as number),
        enabled: !!bookingId,
        staleTime: 5 * 1000,
    }) as UseQueryResult<BookingRead>;
}

export function useConfirmPayment(): UseMutationResult<
    PaymentRead,
    Error,
    { paymentId: number; method: "PIX" | "CARD" }
> {
    return useMutation({
        mutationFn: ({ paymentId, method }) => confirmPayment(paymentId, "approved", method),
    }) as UseMutationResult<PaymentRead, Error, { paymentId: number; method: "PIX" | "CARD" }>;
}
