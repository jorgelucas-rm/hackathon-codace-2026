import { UseQueryResult, useQuery } from "@tanstack/react-query";
import { MeUserRead, getMe, getToken } from "../services/auth.service";

// Anotação de retorno explícita + cast — ver comentário em `hooks/useCompanies.ts`
// (nesta versão de TypeScript/@tanstack-react-query, o generic sozinho não
// basta pra `data` não virar `any` silenciosamente).
export function useMe(): UseQueryResult<MeUserRead> {
    return useQuery<MeUserRead>({
        queryKey: ["me"],
        queryFn: getMe,
        enabled: !!getToken(),
        staleTime: 5 * 60 * 1000,
        retry: false,
    }) as UseQueryResult<MeUserRead>;
}
