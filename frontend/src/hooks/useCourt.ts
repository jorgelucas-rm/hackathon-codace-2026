import { UseQueryResult, useQuery } from "@tanstack/react-query";
import { CourtDetail, getCourt } from "../services/booking.service";

// Anotação de retorno explícita + cast — ver comentário em `hooks/useCompanies.ts`.
export function useCourt(courtId: number | null | undefined): UseQueryResult<CourtDetail> {
    return useQuery<CourtDetail>({
        queryKey: ["court", courtId],
        queryFn: () => getCourt(courtId as number),
        enabled: !!courtId,
        staleTime: 5 * 60 * 1000,
    }) as UseQueryResult<CourtDetail>;
}
