import {
    UseQueryResult,
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";
import { getMe } from "../../../services/auth.service";
import {
    BlockPayload,
    CompanyMeUpdatePayload,
    CourtCreatePayload,
    CourtUpdatePayload,
    ManualBookingPayload,
    PanelCompany,
    PanelCourt,
    PanelReport,
    ScheduleDay,
    cancelBookingByCompany,
    createBlock,
    createCourt,
    createManualBooking,
    deleteCourt,
    getMyReport,
    getMySchedule,
    listMyCourts,
    removeBlock,
    updateCourt,
    updateMyCompany,
} from "../../../services/companyPanel.service";

// Anotação de retorno explícita + cast — mesmo padrão de `hooks/useMe.ts`
// (nesta versão de TS/@tanstack-react-query o generic sozinho não impede
// `data` de virar `any` silenciosamente).

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Empresa autenticada via GET /api/auth/me (entity é CompanyRead quando o
 *  token é de company). Compartilha a queryKey ["me"] do AuthContext. */
export function useMyCompany(): UseQueryResult<PanelCompany | null> {
    return useQuery({
        queryKey: ["me"],
        queryFn: getMe,
        staleTime: 5 * 60 * 1000,
        retry: false,
        select: (me) => ((me?.entity as unknown as PanelCompany) ?? null),
    }) as UseQueryResult<PanelCompany | null>;
}

export function useMySchedule(date: string): UseQueryResult<ScheduleDay> {
    return useQuery<ScheduleDay>({
        queryKey: ["panel", "schedule", date],
        queryFn: () => getMySchedule(date),
        staleTime: 30 * 1000,
    }) as UseQueryResult<ScheduleDay>;
}

export function useMyReport(from: string, to: string): UseQueryResult<PanelReport> {
    return useQuery<PanelReport>({
        queryKey: ["panel", "report", from, to],
        queryFn: () => getMyReport(from, to),
        staleTime: 60 * 1000,
    }) as UseQueryResult<PanelReport>;
}

export function useMyCourts(): UseQueryResult<PanelCourt[]> {
    return useQuery<PanelCourt[]>({
        queryKey: ["panel", "courts"],
        queryFn: listMyCourts,
        staleTime: 60 * 1000,
    }) as UseQueryResult<PanelCourt[]>;
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

function useInvalidate() {
    const queryClient = useQueryClient();
    return (keys: string[][]) => {
        keys.forEach((key) => queryClient.invalidateQueries({ queryKey: key }));
    };
}

export function useCreateCourt() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: (dto: CourtCreatePayload) => createCourt(dto),
        onSuccess: () => invalidate([["panel", "courts"], ["panel", "schedule"]]),
    });
}

export function useUpdateCourt() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: ({ courtId, dto }: { courtId: number; dto: CourtUpdatePayload }) =>
            updateCourt(courtId, dto),
        onSuccess: () => invalidate([["panel", "courts"], ["panel", "schedule"]]),
    });
}

export function useDeleteCourt() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: ({ courtId, force }: { courtId: number; force?: boolean }) =>
            deleteCourt(courtId, force ?? false),
        onSuccess: () =>
            invalidate([["panel", "courts"], ["panel", "schedule"], ["panel", "report"]]),
    });
}

export function useCreateBlock() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: ({ courtId, dto }: { courtId: number; dto: BlockPayload }) =>
            createBlock(courtId, dto),
        onSuccess: () => invalidate([["panel", "schedule"]]),
    });
}

export function useRemoveBlock() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: (bookingId: number) => removeBlock(bookingId),
        onSuccess: () => invalidate([["panel", "schedule"]]),
    });
}

export function useCreateManualBooking() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: (dto: ManualBookingPayload) => createManualBooking(dto),
        onSuccess: () => invalidate([["panel", "schedule"], ["panel", "report"]]),
    });
}

export function useCancelBookingByCompany() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: (bookingId: number) => cancelBookingByCompany(bookingId),
        onSuccess: () => invalidate([["panel", "schedule"], ["panel", "report"]]),
    });
}

export function useUpdateMyCompany() {
    const invalidate = useInvalidate();
    return useMutation({
        mutationFn: (dto: CompanyMeUpdatePayload) => updateMyCompany(dto),
        onSuccess: () => invalidate([["me"]]),
    });
}
