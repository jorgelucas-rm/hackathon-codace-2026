import { UseMutationResult, UseQueryResult, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserRead, getToken } from "../services/auth.service";
import {
    AvatarPreset,
    ProfileUpdateData,
    getAvatarPresets,
    setAvatarPreset,
    updateProfile,
    uploadAvatar,
} from "../services/user.service";

// Mesmo padrão de `useGroups.ts`/`useMe.ts` — anotação de retorno explícita
// + cast pro `data` não virar `any`, e invalidação de `["me"]` depois de
// qualquer mutação que altere o perfil retornado por `GET /api/auth/me`.
export function useAvatarPresets(): UseQueryResult<AvatarPreset[]> {
    return useQuery<AvatarPreset[]>({
        queryKey: ["avatar-presets"],
        queryFn: getAvatarPresets,
        enabled: !!getToken(),
        staleTime: 10 * 60 * 1000,
    }) as UseQueryResult<AvatarPreset[]>;
}

export function useUpdateProfile(): UseMutationResult<UserRead, Error, ProfileUpdateData> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: ProfileUpdateData) => updateProfile(data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
    }) as UseMutationResult<UserRead, Error, ProfileUpdateData>;
}

export function useUploadAvatar(): UseMutationResult<UserRead, Error, File> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (file: File) => uploadAvatar(file),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
    }) as UseMutationResult<UserRead, Error, File>;
}

export function useSetAvatarPreset(): UseMutationResult<UserRead, Error, string> {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (preset: string) => setAvatarPreset(preset),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
    }) as UseMutationResult<UserRead, Error, string>;
}
