import { UseMutationResult, UseQueryResult, useMutation, useQuery } from "@tanstack/react-query";
import {
    AvailabilityResponse,
    BookingCreateResponse,
    GroupBookingConfig,
    createClosedBooking,
    createGroupBooking,
    getAvailability,
} from "../../../services/booking.service";

export { useCourt } from "../../../hooks/useCourt";
// Reaproveitado para o seletor "trocar de quadra" — mesma company, outras quadras.
export { useCompanyDetail } from "../../CourtDetail/hooks/useCourtDetail";

// Anotação de retorno explícita + cast — mesma razão de `hooks/useCompanies.ts`:
// nesta combinação de TypeScript/@tanstack-react-query, o generic sozinho em
// `useQuery<T>`/`useMutation<T>` não basta pra `data` não virar `any`.
export function useAvailability(courtId: number | null, date: string): UseQueryResult<AvailabilityResponse> {
    return useQuery<AvailabilityResponse>({
        queryKey: ["availability", courtId, date],
        queryFn: () => getAvailability(courtId as number, date),
        enabled: !!courtId && !!date,
        staleTime: 15 * 1000,
    }) as UseQueryResult<AvailabilityResponse>;
}

export function useCreateBooking(): UseMutationResult<
    BookingCreateResponse,
    Error,
    { courtId: number; date: string; startTime: string; endTime: string }
> {
    return useMutation({
        mutationFn: ({ courtId, date, startTime, endTime }) =>
            createClosedBooking(courtId, date, startTime, endTime),
    }) as UseMutationResult<
        BookingCreateResponse,
        Error,
        { courtId: number; date: string; startTime: string; endTime: string }
    >;
}

export function useCreateGroupBooking(): UseMutationResult<
    BookingCreateResponse,
    Error,
    { courtId: number; date: string; startTime: string; endTime: string; group: GroupBookingConfig }
> {
    return useMutation({
        mutationFn: ({ courtId, date, startTime, endTime, group }) =>
            createGroupBooking(courtId, date, startTime, endTime, group),
    }) as UseMutationResult<
        BookingCreateResponse,
        Error,
        { courtId: number; date: string; startTime: string; endTime: string; group: GroupBookingConfig }
    >;
}
