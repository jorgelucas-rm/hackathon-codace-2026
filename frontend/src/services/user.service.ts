// Service de perfil do usuário (dados pessoais, avatar, favoritos) —
// integração real com o backend (FastAPI, prefixo /api). Mesmo envelope de
// resposta usado em `auth.service.ts`/`booking.service.ts`.
//
// Endpoints usados aqui:
//   PATCH  /api/users/me                  -> atualiza dados do próprio perfil
//   GET    /api/users/avatars/presets     -> lista avatares pré-definidos
//   POST   /api/users/me/avatar           -> upload de avatar customizado
//   PUT    /api/users/me/avatar/preset    -> seleciona um avatar pré-definido
//   GET    /api/users/me/favorites        -> lista quadras favoritas
//   POST   /api/users/me/favorites/{id}   -> favorita uma quadra
//   DELETE /api/users/me/favorites/{id}   -> desfavorita uma quadra

import { getToken, UserRead } from "./auth.service";

export type SkillLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";

export interface ProfileUpdateData {
    name?: string;
    phone?: string | null;
    street?: string | null;
    number?: string | null;
    zip_code?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    sports_of_interest?: number[];
    skill_level?: SkillLevel | null;
}

export interface AvatarPreset {
    id: string;
    url: string | null;
}

export interface FavoriteCourtsDTO {
    court_ids: number[];
}

interface Envelope<T> {
    code: number;
    message: string;
    error_code?: string | null;
    data: T;
}

function authHeaders(): Record<string, string> {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface ApiError extends Error {
    code?: string;
}

function apiError(json: { message?: string; error_code?: string | null } | null, fallbackError: string): ApiError {
    const err = new Error(json?.message || fallbackError) as ApiError;
    if (json?.error_code) err.code = json.error_code;
    return err;
}

async function getJsonAuth<T>(url: string, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, { headers: authHeaders() });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

async function patchJsonAuth<T>(url: string, body: unknown, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

async function putJsonAuth<T>(url: string, body: unknown, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

async function postAuth<T>(url: string, fallbackError: string, body?: BodyInit): Promise<Envelope<T>> {
    const res = await fetch(url, { method: "POST", headers: authHeaders(), body });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

async function deleteAuth<T>(url: string, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, { method: "DELETE", headers: authHeaders() });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

export async function updateProfile(data: ProfileUpdateData): Promise<UserRead> {
    const json = await patchJsonAuth<UserRead>("/api/users/me", data, "Erro ao atualizar o perfil");
    return json.data;
}

export async function getAvatarPresets(): Promise<AvatarPreset[]> {
    const json = await getJsonAuth<AvatarPreset[]>("/api/users/avatars/presets", "Erro ao buscar os avatares");
    return json.data;
}

export async function uploadAvatar(file: File): Promise<UserRead> {
    const formData = new FormData();
    formData.append("file", file);
    const json = await postAuth<UserRead>("/api/users/me/avatar", "Erro ao enviar o avatar", formData);
    return json.data;
}

export async function setAvatarPreset(preset: string): Promise<UserRead> {
    const json = await putJsonAuth<UserRead>(
        "/api/users/me/avatar/preset",
        { preset },
        "Erro ao selecionar o avatar"
    );
    return json.data;
}

export async function listMyFavorites(): Promise<FavoriteCourtsDTO> {
    const json = await getJsonAuth<FavoriteCourtsDTO>("/api/users/me/favorites", "Erro ao buscar favoritos");
    return json.data;
}

export async function addFavorite(courtId: number): Promise<FavoriteCourtsDTO> {
    const json = await postAuth<FavoriteCourtsDTO>(
        `/api/users/me/favorites/${courtId}`,
        "Erro ao favoritar a quadra"
    );
    return json.data;
}

export async function removeFavorite(courtId: number): Promise<FavoriteCourtsDTO> {
    const json = await deleteAuth<FavoriteCourtsDTO>(
        `/api/users/me/favorites/${courtId}`,
        "Erro ao desfavoritar a quadra"
    );
    return json.data;
}
