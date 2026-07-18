// Service do painel da empresa (arena autenticada) — integração real com o
// backend. Mesmo padrão de auth.service.ts/companies.service.ts/
// booking.service.ts (envelope { code, message, error_code, data, status }).
// Todas as rotas exigem token de COMPANY (Authorization: Bearer).
//
// Endpoints usados aqui:
//   GET    /api/companies/me/schedule?date=YYYY-MM-DD -> agenda do dia (todas as quadras)
//   GET    /api/companies/me/report?from=&to=         -> relatório do período
//   GET    /api/companies/me/courts                   -> minhas quadras
//   POST   /api/companies/me/courts                   -> criar quadra
//   PATCH  /api/courts/{id}                           -> editar quadra
//   POST   /api/courts/{id}/blocks                    -> bloquear horário
//   DELETE /api/bookings/{id}/block                   -> remover bloqueio
//   POST   /api/companies/me/manual-bookings          -> reserva manual (balcão)
//   POST   /api/bookings/{id}/cancel-by-company       -> cancelar reserva de cliente
//   PATCH  /api/companies/me                          -> editar perfil da arena

import { getToken } from "./auth.service";
import { OpeningHour, Sport } from "./companies.service";
import { BookingRead, BookingStatus, GroupPanelSummary } from "./booking.service";

// ---------------------------------------------------------------------------
// Agenda do dia (GET /api/companies/me/schedule?date=)
// ---------------------------------------------------------------------------

export interface ScheduleCustomer {
    name: string | null;
    phone: string | null;
}

export interface ScheduleBooking {
    id: number;
    court_id: number;
    date: string;
    start_time: string;
    end_time: string;
    type: "CLOSED" | "GROUP";
    status: BookingStatus;
    reason: string | null;
    total_price: number;
    customer: ScheduleCustomer | null;
    group: GroupPanelSummary | null;
}

export interface CourtSchedule {
    court_id: number;
    court_name: string;
    bookings: ScheduleBooking[];
}

export interface ScheduleDay {
    date: string;
    courts: CourtSchedule[];
}

// ---------------------------------------------------------------------------
// Relatório (GET /api/companies/me/report?from=&to=)
// ---------------------------------------------------------------------------

export interface PanelReport {
    from_date: string;
    to_date: string;
    total_bookings: number;
    confirmed_revenue: number; // centavos
    occupied_slots: number;
    available_slots: number;
    occupancy_rate: number;
    peak_day: string | null;
    peak_hour: string | null;
}

// ---------------------------------------------------------------------------
// Quadras (GET/POST /api/companies/me/courts, PATCH /api/courts/{id})
// ---------------------------------------------------------------------------

export interface PanelCourt {
    id: number;
    company_id: number;
    name: string;
    capacity: number;
    photos: string[];
    base_price_hour: number; // centavos
    status: "ACTIVE" | "INACTIVE";
    sports: Sport[];
}

export interface CourtCreatePayload {
    name: string;
    capacity: number;
    photos?: string[];
    base_price_hour: number; // centavos
    sport_ids?: number[];
}

// Atenção: no PATCH o backend (CourtUpdateDTO) espera `status` como o valor
// numérico do enum (ACTIVE=1, INACTIVE=2) — diferente da resposta, que vem
// como string. O service aceita a string e converte antes de enviar.
export interface CourtUpdatePayload {
    name?: string;
    capacity?: number;
    photos?: string[];
    base_price_hour?: number; // centavos
    status?: "ACTIVE" | "INACTIVE";
    sport_ids?: number[];
}

const COURT_STATUS_TO_ENUM: Record<"ACTIVE" | "INACTIVE", number> = {
    ACTIVE: 1,
    INACTIVE: 2,
};

// ---------------------------------------------------------------------------
// Bloqueios, reserva manual e cancelamento pelo estabelecimento
// ---------------------------------------------------------------------------

export interface BlockPayload {
    date: string; // YYYY-MM-DD
    start_time: string; // HH:MM
    end_time: string; // HH:MM
    reason?: string | null;
}

export interface ManualBookingPayload {
    court_id: number;
    date: string; // YYYY-MM-DD
    start_time: string; // HH:MM
    end_time: string; // HH:MM
    customer_name: string;
    customer_phone: string;
}

export interface BookingAdminResponse {
    booking: BookingRead;
}

export interface BookingCancelByCompanyResponse {
    booking: BookingRead;
    refunded: boolean;
    group_canceled: boolean;
}

// ---------------------------------------------------------------------------
// Perfil da empresa (PATCH /api/companies/me)
// ---------------------------------------------------------------------------

export interface CompanyMeUpdatePayload {
    name?: string;
    description?: string | null;
    phone?: string | null;
    street?: string;
    number?: string;
    neighborhood?: string;
    city?: string;
    state?: string;
    zip_code?: string;
    latitude?: number | null;
    longitude?: number | null;
    photos?: string[];
    amenities?: string[];
    opening_hours?: OpeningHour[];
}

// Resposta do PATCH /api/companies/me (CompanyReadDTO — sem courts/nota_media)
export interface PanelCompany {
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
}

// ---------------------------------------------------------------------------
// Infra HTTP (mesmo padrão de booking.service.ts)
// ---------------------------------------------------------------------------

interface Envelope<T> {
    code: number;
    message: string;
    error_code?: string | null;
    data: T;
}

export interface ApiError extends Error {
    code?: string;
}

function authHeaders(): Record<string, string> {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function apiError(json: { message?: string; error_code?: string | null } | null, fallbackError: string): ApiError {
    const err = new Error(json?.message || fallbackError) as ApiError;
    if (json?.error_code) err.code = json.error_code;
    return err;
}

async function requestAuth<T>(
    url: string,
    method: "GET" | "POST" | "PATCH" | "DELETE",
    body: unknown | undefined,
    fallbackError: string
): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method,
        headers:
            body !== undefined
                ? { "Content-Type": "application/json", ...authHeaders() }
                : authHeaders(),
        body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

// ---------------------------------------------------------------------------
// API pública do service
// ---------------------------------------------------------------------------

/** Agenda do dia de todas as quadras da empresa. `date` em ISO YYYY-MM-DD. */
export async function getMySchedule(date: string): Promise<ScheduleDay> {
    const json = await requestAuth<ScheduleDay>(
        `/api/companies/me/schedule?date=${encodeURIComponent(date)}`,
        "GET",
        undefined,
        "Erro ao buscar a agenda"
    );
    return json.data;
}

/** Relatório do período. `from`/`to` em ISO YYYY-MM-DD. */
export async function getMyReport(from: string, to: string): Promise<PanelReport> {
    const json = await requestAuth<PanelReport>(
        `/api/companies/me/report?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
        "GET",
        undefined,
        "Erro ao buscar o relatório"
    );
    return json.data;
}

/** Lista as quadras da empresa autenticada. */
export async function listMyCourts(): Promise<PanelCourt[]> {
    const json = await requestAuth<PanelCourt[]>(
        "/api/companies/me/courts",
        "GET",
        undefined,
        "Erro ao buscar suas quadras"
    );
    return json.data;
}

/** Cria uma quadra para a empresa autenticada. */
export async function createCourt(dto: CourtCreatePayload): Promise<PanelCourt> {
    const json = await requestAuth<PanelCourt>(
        "/api/companies/me/courts",
        "POST",
        dto,
        "Erro ao criar a quadra"
    );
    return json.data;
}

/** Atualiza uma quadra (parcial — só os campos enviados). */
export async function updateCourt(courtId: number, dto: CourtUpdatePayload): Promise<PanelCourt> {
    const body: Record<string, unknown> = { ...dto };
    if (dto.status !== undefined) body.status = COURT_STATUS_TO_ENUM[dto.status];
    const json = await requestAuth<PanelCourt>(
        `/api/courts/${courtId}`,
        "PATCH",
        body,
        "Erro ao atualizar a quadra"
    );
    return json.data;
}

/** Exclui uma quadra da empresa.
 *  - Sem `force`: o backend recusa (409 CONFLICT) quando a quadra tem reservas.
 *  - Com `force`: exclui em cascata, removendo também as reservas da quadra. */
export async function deleteCourt(courtId: number, force = false): Promise<void> {
    const query = force ? "?force=true" : "";
    await requestAuth<null>(
        `/api/companies/me/courts/${courtId}${query}`,
        "DELETE",
        undefined,
        "Erro ao excluir a quadra"
    );
}

/** Bloqueia um horário da quadra (manutenção, evento etc.). */
export async function createBlock(courtId: number, dto: BlockPayload): Promise<BookingAdminResponse> {
    const json = await requestAuth<BookingAdminResponse>(
        `/api/courts/${courtId}/blocks`,
        "POST",
        dto,
        "Erro ao bloquear o horário"
    );
    return json.data;
}

/** Remove um bloqueio (o `bookingId` é o booking com status BLOCKED). */
export async function removeBlock(bookingId: number): Promise<BookingAdminResponse> {
    const json = await requestAuth<BookingAdminResponse>(
        `/api/bookings/${bookingId}/block`,
        "DELETE",
        undefined,
        "Erro ao remover o bloqueio"
    );
    return json.data;
}

/** Reserva manual (balcão) — nasce CONFIRMED, sem pagamento. */
export async function createManualBooking(dto: ManualBookingPayload): Promise<BookingAdminResponse> {
    const json = await requestAuth<BookingAdminResponse>(
        "/api/companies/me/manual-bookings",
        "POST",
        dto,
        "Erro ao criar a reserva manual"
    );
    return json.data;
}

/** Cancela uma reserva de cliente pelo estabelecimento (com reembolso se pago). */
export async function cancelBookingByCompany(bookingId: number): Promise<BookingCancelByCompanyResponse> {
    const json = await requestAuth<BookingCancelByCompanyResponse>(
        `/api/bookings/${bookingId}/cancel-by-company`,
        "POST",
        {},
        "Erro ao cancelar a reserva"
    );
    return json.data;
}

/** Atualiza o perfil da empresa autenticada (parcial). */
export async function updateMyCompany(dto: CompanyMeUpdatePayload): Promise<PanelCompany> {
    const json = await requestAuth<PanelCompany>(
        "/api/companies/me",
        "PATCH",
        dto,
        "Erro ao atualizar os dados da arena"
    );
    return json.data;
}

export function formatPriceCents(cents: number | null | undefined): string {
    if (cents === null || cents === undefined) return "—";
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatHHMM(time: string): string {
    return time.slice(0, 5);
}
