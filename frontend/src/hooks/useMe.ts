import { useQuery } from "@tanstack/react-query";
import { getMe, getToken } from "../services/auth.service";

export function useMe() {
    return useQuery({
        queryKey: ["me"],
        queryFn: getMe,
        enabled: !!getToken(),
        staleTime: 5 * 60 * 1000,
        retry: false,
    });
}
