import { UseMutationResult, UseQueryResult, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getToken } from "../../../services/auth.service";
import { BookingCancelResponse, BookingRead, ReviewRead, cancelBooking, createReview, getBooking, getMyBookings } from "../../../services/booking.service";

// Mesmo padrão de `useCourtDetail.ts`/`useMe.ts` — anotação de retorno
// explícita + cast pro `data` não virar `any`.
export function useMyBookings(scope: "upcoming" | "history"): UseQueryResult<BookingRead[]> {
    return useQuery<BookingRead[]>({
        queryKey: ["my-bookings", scope],
        queryFn: () => getMyBookings(scope),
        enabled: !!getToken(),
        staleTime: 30 * 1000,
    }) as UseQueryResult<BookingRead[]>;
}

export function useBookingDetail(bookingId: number | null): UseQueryResult<BookingRead> {
    return useQuery<BookingRead>({
        queryKey: ["booking", bookingId],
        queryFn: () => getBooking(bookingId as number),
        enabled: !!bookingId && !!getToken(),
        staleTime: 15 * 1000,
    }) as UseQueryResult<BookingRead>;
}

export function useCancelBooking(): UseMutationResult<BookingCancelResponse, Error, number> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (bookingId: number) => cancelBooking(bookingId),
        onSuccess: (_res, bookingId) => {
            queryClient.invalidateQueries({ queryKey: ["my-bookings"] });
            queryClient.invalidateQueries({ queryKey: ["booking", bookingId] });
        },
    }) as UseMutationResult<BookingCancelResponse, Error, number>;
}

export function useCreateReview(): UseMutationResult<ReviewRead, Error, { bookingId: number; rating: number; comment: string | null }> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ bookingId, rating, comment }) => createReview(bookingId, rating, comment),
        onSuccess: (_res, { bookingId }) => {
            queryClient.invalidateQueries({ queryKey: ["booking", bookingId] });
        },
    }) as UseMutationResult<ReviewRead, Error, { bookingId: number; rating: number; comment: string | null }>;
}

// `useGroupDetail` (grupo de uma reserva específica) vive em
// `hooks/useGroups.ts` — reaproveitado aqui e em Home/OpenMatches.
export { useGroupDetail } from "../../../hooks/useGroups";
