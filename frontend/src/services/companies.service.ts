// Service de arenas (companies) e esportes — integração real com o backend
// (FastAPI, prefixo /api). Mesmo envelope de resposta usado em
// `auth.service.ts`: { code, message, error_code, data, status }.
//
// Endpoints usados aqui:
//   GET /api/sports                -> lista de esportes p/ os filtros
//   GET /api/companies?...         -> busca pública de arenas (vitrine)
//   GET /api/companies/{id}        -> detalhe completo de uma arena
//   GET /api/companies/{id}/reviews -> avaliações da arena (paginado)

export interface Sport {
    id: number;
    name: string;
    icon: string | null;
}

export interface OpeningHour {
    dia_semana: string;
    abertura: string | null;
    fechamento: string | null;
    fechado: boolean;
}

export interface Court {
    id: number;
    company_id: number;
    name: string;
    capacity: number;
    photos: string[];
    base_price_hour: number;
    status: string;
    sports: Sport[];
}

export interface CompanySearchCard {
    id: number;
    name: string;
    cover_photo: string | null;
    distance_km: number | null;
    min_price_hour: number | null;
    nota_media: number | null;
}

export interface CompanyDetail {
    id: number;
    cnpj: string;
    name: string;
    email: string;
    street: string;
    number: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
    situation: boolean;
    description: string | null;
    phone: string | null;
    latitude: number | null;
    longitude: number | null;
    photos: string[];
    amenities: string[];
    opening_hours: OpeningHour[];
    courts: Court[];
    nota_media: number | null;
}

export interface CompanyReview {
    id: number;
    company_id: number;
    booking_id: number;
    user_id: number;
    user_name: string | null;
    rating: number;
    comment: string | null;
    helpful_count: number;
    created_at: string;
}

export interface Pagination<T> {
    items: T[];
    total: number;
    total_filtered: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface CompanySearchFilters {
    q?: string;
    sportId?: number | null;
    lat?: number;
    lng?: number;
    raioKm?: number;
    amenities?: string[];
    page?: number;
    size?: number;
}

interface Envelope<T> {
    code: number;
    message: string;
    error_code?: string | null;
    data: T;
}

async function getJson<T>(url: string, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url);
    const json = await res.json().catch(() => null);
    if (!res.ok) {
        throw new Error(json?.message || fallbackError);
    }
    return json as Envelope<T>;
}

function buildQuery(params: Record<string, string | number | string[] | undefined | null>): string {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null || value === "") continue;
        if (Array.isArray(value)) {
            value.forEach((v) => search.append(key, v));
        } else {
            search.append(key, String(value));
        }
    }
    const qs = search.toString();
    return qs ? `?${qs}` : "";
}

export async function getSports(): Promise<Sport[]> {
    const json = await getJson<Sport[]>("/api/sports", "Erro ao buscar os esportes");
    return json.data;
}

export async function searchCompanies(filters: CompanySearchFilters = {}): Promise<Pagination<CompanySearchCard>> {
    const qs = buildQuery({
        q: filters.q,
        sport_id: filters.sportId ?? undefined,
        lat: filters.lat,
        lng: filters.lng,
        raio_km: filters.raioKm,
        amenities: filters.amenities,
        page: filters.page ?? 1,
        size: filters.size ?? 12,
    });
    const json = await getJson<Pagination<CompanySearchCard>>(`/api/companies${qs}`, "Erro ao buscar as arenas");
    return json.data;
}

export async function getCompanyDetail(id: number): Promise<CompanyDetail> {
    const json = await getJson<CompanyDetail>(`/api/companies/${id}`, "Erro ao buscar a arena");
    return json.data;
}

export async function getCompanyReviews(id: number, page = 1, size = 10): Promise<Pagination<CompanyReview>> {
    const qs = buildQuery({ page, page_size: size });
    const json = await getJson<Pagination<CompanyReview>>(`/api/companies/${id}/reviews${qs}`, "Erro ao buscar as avaliações");
    return json.data;
}

export function formatPriceCents(cents: number | null | undefined): string {
    if (cents === null || cents === undefined) return "—";
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
