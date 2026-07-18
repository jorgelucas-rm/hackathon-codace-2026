// Service de agendamento (disponibilidade, criar reserva, pagamento) —
// integração real com o backend. Mesmo padrão de auth.service.ts/
// companies.service.ts (envelope { code, message, error_code, data, status }).
//
// Endpoints usados aqui:
//   GET  /api/courts/{id}                    -> detalhe público de uma quadra
//   GET  /api/courts/{id}/availability?date=  -> slots do dia (público)
//   POST /api/bookings                        -> cria reserva (auth USER)
//   GET  /api/bookings/{id}                   -> detalhe da reserva (auth)
//   GET  /api/users/me/bookings?scope=        -> minhas reservas (auth USER)
//   GET  /api/groups                          -> busca pública de partidas abertas
//   GET  /api/groups/{id}                     -> detalhe do grupo (participantes)
//   POST /api/groups/{id}/join                -> entrar num grupo aberto (auth USER)
//   GET  /api/payments/{id}                   -> detalhe do pagamento (auth USER)
//   POST /api/payments/{id}/confirm           -> simulador de gateway (auth USER)
//   POST /api/bookings/{id}/reviews           -> avalia uma reserva concluída (auth USER)

import { getToken } from "./auth.service";
import { Sport } from "./companies.service";

export interface CourtCompanySummary {
    id: number;
    name: string;
    city: string;
    state: string;
    latitude: number | null;
    longitude: number | null;
}

export interface CourtDetail {
    id: number;
    company_id: number;
    name: string;
    capacity: number;
    photos: string[];
    base_price_hour: number;
    status: string;
    sports: Sport[];
    company: CourtCompanySummary;
}

export interface AvailabilityGroup {
    id: number;
    total_spots: number;
    filled_spots: number;
    spot_price: number;
    closing_deadline: string;
}

export interface AvailabilitySlot {
    start_time: string;
    end_time: string;
    status: "free" | "busy" | "open_group";
    price: number;
    group: AvailabilityGroup | null;
}

export interface AvailabilityResponse {
    court_id: number;
    date: string;
    slots: AvailabilitySlot[];
}

export type BookingStatus = "PENDING" | "CONFIRMED" | "CANCELED" | "COMPLETED" | "BLOCKED";
export type PaymentStatus = "PENDING" | "APPROVED" | "DENIED" | "REFUNDED";

export interface GroupPanelSummary {
    id: number;
    status: string;
    total_spots: number;
    min_spots: number;
    filled_spots: number;
    spot_price: number;
    visibility: string;
    closing_deadline: string;
}

export interface BookingRead {
    id: number;
    court_id: number;
    creator_user_id: number | null;
    creator_company_id: number | null;
    date: string;
    start_time: string;
    end_time: string;
    type: "CLOSED" | "GROUP";
    status: BookingStatus;
    reason: string | null;
    total_price: number;
    customer_name: string | null;
    customer_phone: string | null;
    created_at: string;
    court_name: string | null;
    company_name: string | null;
    sport_names: string[];
    group: GroupPanelSummary | null;
}

export interface GroupMemberRead {
    id: number;
    user_id: number;
    user_name: string | null;
    user_avatar: string | null;
    status: string;
    joined_at: string;
}

export interface GroupDetail {
    id: number;
    booking_id: number;
    court_id: number;
    court_name: string | null;
    company_id: number | null;
    company_name: string | null;
    date: string;
    start_time: string;
    end_time: string;
    status: string;
    total_spots: number;
    min_spots: number;
    filled_spots: number;
    spot_price: number;
    visibility: string;
    closing_deadline: string;
    leftover_rule: string;
    members: GroupMemberRead[];
}

export interface PaymentSummary {
    id: number;
    reference_type: string;
    reference_id: number;
    amount: number;
    method: "PIX" | "CARD" | null;
    status: PaymentStatus;
    created_at: string;
}

export interface PaymentRead extends PaymentSummary {
    company_payout: number | null;
    platform_fee: number | null;
    gateway_fee: number | null;
    refunded_at: string | null;
}

export interface BookingCreateResponse {
    booking: BookingRead;
    payment: PaymentSummary;
}

export interface GroupJoinResponse {
    member: GroupMemberRead;
    payment: PaymentSummary;
    group: GroupPanelSummary;
}

export interface GroupLeaveResponse {
    group: GroupPanelSummary;
    refunded: boolean;
}

export interface BookingCancelResponse {
    booking: BookingRead;
    refunded: boolean;
}

export interface ReviewRead {
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

async function getJson<T>(url: string, fallbackError: string, auth = false): Promise<Envelope<T>> {
    const res = await fetch(url, { headers: auth ? authHeaders() : {} });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

async function postJsonAuth<T>(url: string, body: unknown, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw apiError(json, fallbackError);
    return json as Envelope<T>;
}

export async function getCourt(courtId: number): Promise<CourtDetail> {
    const json = await getJson<CourtDetail>(`/api/courts/${courtId}`, "Erro ao buscar a quadra");
    return json.data;
}

export async function getAvailability(courtId: number, date: string): Promise<AvailabilityResponse> {
    const json = await getJson<AvailabilityResponse>(
        `/api/courts/${courtId}/availability?date=${date}`,
        "Erro ao buscar a disponibilidade"
    );
    return json.data;
}

export async function createClosedBooking(
    courtId: number,
    date: string,
    startTime: string,
    endTime: string
): Promise<BookingCreateResponse> {
    const json = await postJsonAuth<BookingCreateResponse>(
        "/api/bookings",
        { court_id: courtId, date, start_time: startTime, end_time: endTime, type: "closed" },
        "Erro ao criar a reserva"
    );
    return json.data;
}

export interface GroupBookingConfig {
    totalSpots: number;
    minSpots: number;
    visibility: "public" | "link";
    closingDeadline: string;
    leftoverRule: "creator_absorbs" | "recalculate_quota";
}

export async function createGroupBooking(
    courtId: number,
    date: string,
    startTime: string,
    endTime: string,
    group: GroupBookingConfig
): Promise<BookingCreateResponse> {
    const json = await postJsonAuth<BookingCreateResponse>(
        "/api/bookings",
        {
            court_id: courtId,
            date,
            start_time: startTime,
            end_time: endTime,
            type: "group",
            group: {
                total_spots: group.totalSpots,
                min_spots: group.minSpots,
                visibility: group.visibility,
                closing_deadline: group.closingDeadline,
                leftover_rule: group.leftoverRule,
            },
        },
        "Erro ao criar o grupo aberto"
    );
    return json.data;
}

export async function getBooking(bookingId: number): Promise<BookingRead> {
    const json = await getJson<BookingRead>(`/api/bookings/${bookingId}`, "Erro ao buscar a reserva", true);
    return json.data;
}

export async function getMyBookings(scope: "upcoming" | "history"): Promise<BookingRead[]> {
    const json = await getJson<BookingRead[]>(
        `/api/users/me/bookings?scope=${scope}`,
        "Erro ao buscar suas reservas",
        true
    );
    return json.data;
}

export async function getGroup(groupId: number): Promise<GroupDetail> {
    const json = await getJson<GroupDetail>(`/api/groups/${groupId}`, "Erro ao buscar o grupo");
    return json.data;
}

export interface OpenGroupsFilters {
    sportId?: number;
    courtId?: number;
    date?: string;
}

export async function listOpenGroups(filters: OpenGroupsFilters = {}): Promise<GroupDetail[]> {
    const params = new URLSearchParams();
    if (filters.sportId) params.set("sport_id", String(filters.sportId));
    if (filters.courtId) params.set("court_id", String(filters.courtId));
    if (filters.date) params.set("date", filters.date);
    const qs = params.toString();
    const json = await getJson<GroupDetail[]>(`/api/groups${qs ? `?${qs}` : ""}`, "Erro ao buscar partidas abertas");
    return json.data;
}

export async function joinGroup(groupId: number): Promise<GroupJoinResponse> {
    const json = await postJsonAuth<GroupJoinResponse>(
        `/api/groups/${groupId}/join`,
        {},
        "Erro ao entrar no grupo"
    );
    return json.data;
}

export async function cancelBooking(bookingId: number): Promise<BookingCancelResponse> {
    const json = await postJsonAuth<BookingCancelResponse>(
        `/api/bookings/${bookingId}/cancel`,
        {},
        "Erro ao cancelar a reserva"
    );
    return json.data;
}

export async function getMyGroups(): Promise<GroupDetail[]> {
    const json = await getJson<GroupDetail[]>("/api/groups/mine", "Erro ao buscar seus grupos", true);
    return json.data;
}

export async function leaveGroup(groupId: number): Promise<GroupLeaveResponse> {
    const json = await postJsonAuth<GroupLeaveResponse>(
        `/api/groups/${groupId}/leave`,
        {},
        "Erro ao sair do grupo"
    );
    return json.data;
}

export async function getPayment(paymentId: number): Promise<PaymentRead> {
    const json = await getJson<PaymentRead>(`/api/payments/${paymentId}`, "Erro ao buscar o pagamento", true);
    return json.data;
}

export async function confirmPayment(
    paymentId: number,
    result: "approved" | "denied",
    method: "PIX" | "CARD"
): Promise<PaymentRead> {
    const json = await postJsonAuth<PaymentRead>(
        `/api/payments/${paymentId}/confirm`,
        { result, method },
        "Erro ao confirmar o pagamento"
    );
    return json.data;
}

export async function createReview(
    bookingId: number,
    rating: number,
    comment: string | null
): Promise<ReviewRead> {
    const json = await postJsonAuth<ReviewRead>(
        `/api/bookings/${bookingId}/reviews`,
        { rating, comment: comment || null },
        "Erro ao enviar a avaliação"
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
