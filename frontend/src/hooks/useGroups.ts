import { UseMutationResult, UseQueryResult, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    GroupDetail,
    GroupJoinResponse,
    GroupLeaveResponse,
    OpenGroupsFilters,
    getGroup,
    getMyGroups,
    joinGroup,
    leaveGroup,
    listOpenGroups,
} from "../services/booking.service";
import { getToken } from "../services/auth.service";

// Mesmo padrão de `useCourtDetail.ts`/`useMe.ts` — anotação de retorno
// explícita + cast pro `data` não virar `any`.
export function useOpenGroups(filters: OpenGroupsFilters = {}): UseQueryResult<GroupDetail[]> {
    return useQuery<GroupDetail[]>({
        queryKey: ["open-groups", filters],
        queryFn: () => listOpenGroups(filters),
        staleTime: 30 * 1000,
    }) as UseQueryResult<GroupDetail[]>;
}

export function useGroupDetail(groupId: number | null): UseQueryResult<GroupDetail> {
    return useQuery<GroupDetail>({
        queryKey: ["group", groupId],
        queryFn: () => getGroup(groupId as number),
        enabled: !!groupId,
        staleTime: 15 * 1000,
    }) as UseQueryResult<GroupDetail>;
}

export function useJoinGroup(): UseMutationResult<GroupJoinResponse, Error, number> {
    return useMutation({
        mutationFn: (groupId: number) => joinGroup(groupId),
    }) as UseMutationResult<GroupJoinResponse, Error, number>;
}

export function useMyGroups(): UseQueryResult<GroupDetail[]> {
    return useQuery<GroupDetail[]>({
        queryKey: ["my-groups"],
        queryFn: () => getMyGroups(),
        enabled: !!getToken(),
        staleTime: 15 * 1000,
    }) as UseQueryResult<GroupDetail[]>;
}

export function useLeaveGroup(): UseMutationResult<GroupLeaveResponse, Error, number> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (groupId: number) => leaveGroup(groupId),
        onSuccess: (_res, groupId) => {
            queryClient.invalidateQueries({ queryKey: ["my-groups"] });
            queryClient.invalidateQueries({ queryKey: ["group", groupId] });
        },
    }) as UseMutationResult<GroupLeaveResponse, Error, number>;
}
