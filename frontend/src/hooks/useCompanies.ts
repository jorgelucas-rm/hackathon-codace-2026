import { UseQueryResult, useQuery } from "@tanstack/react-query";
import { CompanySearchCard, CompanySearchFilters, Pagination, Sport, getSports, searchCompanies } from "../services/companies.service";

// Anotação de retorno explícita (`UseQueryResult<T>`) + cast no `useQuery(...)`
// — nesta combinação de versões de TypeScript/@tanstack-react-query do
// projeto, só o generic em `useQuery<T>(...)` não é suficiente: o inference
// se perde e `data` vira `any` silenciosamente pro chamador (só estoura erro
// mais na frente, em quem faz `.map()` no resultado). Isso força o tipo.
export function useSports(): UseQueryResult<Sport[]> {
    return useQuery<Sport[]>({
        queryKey: ["sports"],
        queryFn: getSports,
        staleTime: 10 * 60 * 1000,
    }) as UseQueryResult<Sport[]>;
}

export function useCompanySearch(filters: CompanySearchFilters): UseQueryResult<Pagination<CompanySearchCard>> {
    return useQuery<Pagination<CompanySearchCard>>({
        queryKey: ["companies", filters],
        queryFn: () => searchCompanies(filters),
        staleTime: 30 * 1000,
    }) as UseQueryResult<Pagination<CompanySearchCard>>;
}
