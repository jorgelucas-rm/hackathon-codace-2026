import { UseQueryResult, useQuery } from "@tanstack/react-query";
import { CompanyDetail, CompanyReview, Pagination, getCompanyDetail, getCompanyReviews } from "../../../services/companies.service";

// Anotação de retorno explícita + cast — ver comentário em `hooks/useCompanies.ts`.
export function useCompanyDetail(id: number): UseQueryResult<CompanyDetail> {
    return useQuery<CompanyDetail>({
        queryKey: ["company", id],
        queryFn: () => getCompanyDetail(id),
        enabled: !!id,
        staleTime: 30 * 1000,
    }) as UseQueryResult<CompanyDetail>;
}

export function useCompanyReviews(id: number): UseQueryResult<Pagination<CompanyReview>> {
    return useQuery<Pagination<CompanyReview>>({
        queryKey: ["company", id, "reviews"],
        queryFn: () => getCompanyReviews(id),
        enabled: !!id,
        staleTime: 30 * 1000,
    }) as UseQueryResult<Pagination<CompanyReview>>;
}
